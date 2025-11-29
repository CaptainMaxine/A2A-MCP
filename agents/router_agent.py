# agents/router_agent.py
import re
from typing import Dict, List, Any

from .base_agent import BaseAgent, A2AMessage


class RouterAgent(BaseAgent):
    """
    The RouterAgent is the orchestrator of the multi-agent system.

    Upgraded version:
    - Uses LLM to classify user intent
    - Maps LLM intent → scenario
    - Routes to DataAgent or SupportAgent
    - Stores structured state for multi-step workflows
    """

    def __init__(self):
        super().__init__(name="router")

    # ------------------------------------------------------
    # 1. LLM-based intent classification
    # ------------------------------------------------------
    def classify_intent(self, user_query: str) -> Dict[str, Any]:
        """
        Use an LLM to classify the user's request into:
        - scenario
        - intents (list)
        - extracted fields (e.g., customer_id, email)
        """

        system_prompt = (
            "You are an intent classification system for a customer service AI. "
            "You must return a JSON dictionary with keys:\n"
            "- scenario: one of ['scenario_1_task_allocation', 'simple_get_and_support', "
            "'coordinated_upgrade', 'cancel_and_billing', "
            "'high_priority_for_premium', 'active_customers_with_open_tickets', "
            "'refund_escalation', 'update_email_and_history']\n"
            "- intents: list of atomic intents\n"
            "- customer_id: integer or null\n"
            "- email: string or null\n"
            "- issue: string or null\n\n"
            "Do not include explanations. Only valid JSON."
        )

        user_prompt = f"User query: {user_query}\n\nExtract intents."

        raw = self.llm(system_prompt, user_prompt)

        # Parse JSON safely
        import json
        try:
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError
        except Exception:
            # fallback minimal structure
            result = {
                "scenario": "simple_get_and_support",
                "intents": [],
                "customer_id": None,
                "email": None,
                "issue": user_query,
            }

        return result

    # ------------------------------------------------------
    # 2. Extract customer ID with regex (LLM may miss)
    # ------------------------------------------------------
    def extract_customer_id(self, text: str) -> int:
        m = re.search(r"\b(\d{3,6})\b", text)
        return int(m.group(1)) if m else None

    # ------------------------------------------------------
    # 3. Handle message from user or agents
    # ------------------------------------------------------
    def handle(self, message: A2AMessage) -> A2AMessage:
        sender = message.sender
        content = message.content
        state = dict(message.state)

        # User is talking
        if sender == "user":
            # Save original query
            state["original_query"] = content

            # 1) LLM-based classification
            result = self.classify_intent(content)
            scenario = result.get("scenario")
            intents = result.get("intents", [])
            customer_id = result.get("customer_id")
            email = result.get("email")
            issue = result.get("issue") or content

            # 2) Regex fallback for customer_id
            if not customer_id:
                customer_id = self.extract_customer_id(content)

            state.update(
                {
                    "scenario": scenario,
                    "intents": intents,
                    "customer_id": customer_id,
                    "email": email,
                    "issue": issue,
                }
            )

            # 3) Decide next agent
            # Most scenarios need customer data first
            if scenario in {
                "scenario_1_task_allocation",
                "coordinated_upgrade",
                "cancel_and_billing",
                "refund_escalation",
                "update_email_and_history",
                "simple_get_and_support",
            }:
                return A2AMessage(
                    sender=self.name,
                    receiver="data",
                    role="router",
                    content="lookup_customer",
                    state=state,
                )

            # Scenario 3: premium customers → need DataAgent to list
            if scenario == "high_priority_for_premium":
                return A2AMessage(
                    sender=self.name,
                    receiver="data",
                    role="router",
                    content="list_premium_customers",
                    state=state,
                )

            # Active customers with open tickets
            if scenario == "active_customers_with_open_tickets":
                return A2AMessage(
                    sender=self.name,
                    receiver="data",
                    role="router",
                    content="list_active_customers",
                    state=state,
                )

            # Fallback
            return A2AMessage(
                sender=self.name,
                receiver="support",
                role="router",
                content="general_support",
                state=state,
            )

        # ------------------------------------------------------
        # Message from DataAgent
        # ------------------------------------------------------
        if sender == "data":
            scenario = state.get("scenario")

            # Typical flow: after lookup_customer, data agent sets customer
            if scenario in {
                "scenario_1_task_allocation",
                "simple_get_and_support",
                "coordinated_upgrade",
                "refund_escalation",
                "update_email_and_history",
            }:
                return A2AMessage(
                    sender=self.name,
                    receiver="support",
                    role="router",
                    content="support_handle",
                    state=state,
                )

            # Negotiation (Scenario 2)
            if scenario == "cancel_and_billing":
                if state.get("support_needs_billing_context"):
                    # Now we have billing data
                    state["billing_context_ready"] = True
                return A2AMessage(
                    sender=self.name,
                    receiver="support",
                    role="router",
                    content="support_handle",
                    state=state,
                )

            # Multi-step premium ticket query
            if scenario == "high_priority_for_premium":
                return A2AMessage(
                    sender=self.name,
                    receiver="support",
                    role="router",
                    content="support_handle",
                    state=state,
                )

            if scenario == "active_customers_with_open_tickets":
                return A2AMessage(
                    sender=self.name,
                    receiver="support",
                    role="router",
                    content="support_handle",
                    state=state,
                )

        # ------------------------------------------------------
        # Message from SupportAgent → return to user
        # ------------------------------------------------------
        if sender == "support":
            return A2AMessage(
                sender=self.name,
                receiver="user",
                role="router",
                content=content,
                state=state,
            )

        # Should never reach here
        return A2AMessage(
            sender=self.name,
            receiver="user",
            role="router",
            content="[RouterAgent] Unrecognized routing case.",
            state=state,
        )
