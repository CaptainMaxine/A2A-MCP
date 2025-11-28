# agents/router_agent.py
import re
from typing import Dict, List, Tuple

from .base_agent import A2AMessage, BaseAgent


class RouterAgent(BaseAgent):
    """
    Central orchestrator / router.

    Responsibilities:
    - Receive user query
    - Analyze intent & scenario
    - Route to CustomerDataAgent / SupportAgent
    - Coordinate multi-step flows
    - Synthesize final response to user
    """

    def __init__(self):
        super().__init__(name="router")

    # ---------- Intent & scenario parsing ----------

    def _extract_customer_id(self, text: str) -> int | None:
        patterns = [
            r"customer\s+id\s+(\d+)",
            r"id\s+(\d+)",
            r"i[' ]?m\s+customer\s+(\d+)",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return int(m.group(1))
        return None

    def _extract_email(self, text: str) -> str | None:
        m = re.search(r"[\w\.-]+@[\w\.-]+", text)
        return m.group(0) if m else None

    def analyze_query(self, query: str) -> Tuple[str, Dict]:
        """
        Analyze raw user query and return (scenario, initial_state_partial).
        """
        q = query.lower()
        state: Dict = {"original_query": query}

        customer_id = self._extract_customer_id(query)
        if customer_id is not None:
            state["customer_id"] = customer_id

        # Scenario mapping based on key phrases

        # Scenario 3 (explicit in assignment)
        if "status of all high-priority tickets for premium customers" in q:
            scenario = "high_priority_for_premium"
            state["intent"] = "report_high_priority_premium"

        # Scenario 2: cancellation + billing
        elif "cancel" in q and "billing" in q:
            scenario = "cancel_and_billing"
            state["intent"] = "cancel_and_billing"

        # Scenario 1: task allocation with explicit ID
        elif "help with my account" in q and "id" in q:
            scenario = "scenario_1_task_allocation"
            state["intent"] = "account_help"
            state["issue"] = "help with your account"

        # Simple query: just get customer info
        elif "get customer information" in q and "id" in q:
            scenario = "simple_get_customer"
            state["intent"] = "get_customer_info"

        # Coordinated upgrade
        elif "upgrade" in q or "upgrading my account" in q:
            scenario = "coordinated_upgrade"
            state["intent"] = "upgrade"

        # Complex: all active customers with open tickets
        elif "active customers" in q and "open tickets" in q:
            scenario = "active_customers_with_open_tickets"
            state["intent"] = "report_active_open_tickets"

        # Escalation: refund / charged twice
        elif "charged twice" in q or "refund" in q:
            scenario = "refund_escalation"
            state["intent"] = "refund"

        # Multi-intent: update email + ticket history
        elif "update my email" in q and "ticket history" in q:
            scenario = "update_email_and_history"
            state["intent"] = "update_email_and_history"
            email = self._extract_email(query)
            if email:
                state["new_email"] = email

        else:
            scenario = "generic_support"
            state["intent"] = "generic"

        state["scenario"] = scenario
        state["step"] = 0
        return scenario, state

    # ---------- Main handler ----------

    def handle(self, message: A2AMessage) -> A2AMessage:
        """
        Router is invoked in multiple contexts:

        - From user: first turn; analyze scenario & dispatch.
        - From CustomerDataAgent: inspect scenario and decide next agent.
        - From SupportAgent: usually ready to answer user.
        """
        state = dict(message.state)
        sender = message.sender
        scenario = state.get("scenario")
        step = state.get("step", 0)

        # 1) Initial user query
        if sender == "user":
            scenario, state = self.analyze_query(message.content)
            state["scenario"] = scenario
            state["step"] = 1

            # Decide first specialist
            if scenario in {
                "scenario_1_task_allocation",
                "simple_get_customer",
                "coordinated_upgrade",
                "cancel_and_billing",
                "refund_escalation",
                "update_email_and_history",
            }:
                # Need customer data first.
                state["action"] = "get_customer"
                next_receiver = "customer_data"

            elif scenario == "high_priority_for_premium":
                state["action"] = "list_premium_customers"
                next_receiver = "customer_data"

            elif scenario == "active_customers_with_open_tickets":
                state["action"] = "get_active_customers_with_open_tickets"
                next_receiver = "customer_data"

            else:
                # generic support: send directly to support
                next_receiver = "support"

            return A2AMessage(
                sender=self.name,
                receiver=next_receiver,
                role="agent",
                content=f"[Router] Dispatching scenario={scenario} to {next_receiver}.",
                state=state,
            )

        # 2) Reply from CustomerDataAgent
        if sender == "customer_data":
            step += 1
            state["step"] = step

            # Scenario 1: after getting customer, hand to support
            if scenario in {"scenario_1_task_allocation", "coordinated_upgrade"}:
                state.setdefault("issue", "help with your account")
                next_receiver = "support"
                content = "[Router] Forwarding customer context to SupportAgent."

            # Simple query: after data, answer directly to user
            elif scenario == "simple_get_customer":
                customer = state.get("customer")
                if customer:
                    c = customer
                    text = (
                        f"Customer #{c['id']}: {c['name']}\n"
                        f"Email: {c.get('email')}\n"
                        f"Phone: {c.get('phone')}\n"
                        f"Status: {c['status']}\n"
                        f"Created: {c['created_at']}\n"
                        f"Updated: {c['updated_at']}"
                    )
                else:
                    text = "No customer found for the provided ID."
                return A2AMessage(
                    sender=self.name,
                    receiver="user",
                    role="agent",
                    content=text,
                    state=state,
                )

            # Scenario 2: we now have customer context; need billing history
            elif scenario == "cancel_and_billing":
                # Ask customer_data to also provide ticket history
                customer_id = state.get("customer_id")
                if state.get("customer") and not state.get("customer_history"):
                    history = None  # Ask SupportAgent to request it explicitly
                # Router will ask support what it needs.
                next_receiver = "support"
                content = "[Router] Customer context ready; checking with SupportAgent."

            # Scenario 3: premium customers list obtained -> support builds report
            elif scenario == "high_priority_for_premium":
                next_receiver = "support"
                content = "[Router] Premium customer list ready; asking SupportAgent for report."

            # Complex: active customers list -> support computes open tickets
            elif scenario == "active_customers_with_open_tickets":
                next_receiver = "support"
                content = "[Router] Active customer list ready; asking SupportAgent."

            # Multi-intent update email + history:
            elif scenario == "update_email_and_history":
                # After CustomerDataAgent updates email, let SupportAgent generate history summary
                next_receiver = "support"
                content = "[Router] Email updated; asking SupportAgent for history."

            # Refund escalation: after getting customer, send to support for escalation
            elif scenario == "refund_escalation":
                next_receiver = "support"
                content = "[Router] Customer identified; escalating to SupportAgent."

            else:
                next_receiver = "support"
                content = "[Router] Passing data reply to SupportAgent (fallback)."

            return A2AMessage(
                sender=self.name,
                receiver=next_receiver,
                role="agent",
                content=content,
                state=state,
            )

        # 3) Reply from SupportAgent
        if sender == "support":
            step += 1
            state["step"] = step

            # If support explicitly requested billing context (Scenario 2)
            if scenario == "cancel_and_billing" and state.get(
                "support_needs_billing_context"
            ):
                # Router now fetches billing context (ticket history) via DataAgent
                state.pop("support_needs_billing_context", None)
                state["action"] = "get_customer_history"
                # Instead of new DB API, we reuse existing tool via DataAgent:
                # We'll signal via flag and let coordinator or DataAgent adapt.
                # For simplicity, Router will store the requirement and final history
                # will be retrieved in coordinator using MCPClient directly.
                # To keep within assignment spirit, we model it as:
                state["router_should_fetch_history_via_data_agent"] = True
                return A2AMessage(
                    sender=self.name,
                    receiver="customer_data",
                    role="agent",
                    content="[Router] Support requested billing context; "
                            "asking CustomerDataAgent for ticket history.",
                    state=state,
                )

            # Otherwise, SupportAgent response is considered final for user.
            return A2AMessage(
                sender=self.name,
                receiver="user",
                role="agent",
                content=message.content,
                state=state,
            )

        # 4) Fallback: any other sender, just echo to user
        return A2AMessage(
            sender=self.name,
            receiver="user",
            role="agent",
            content=message.content,
            state=state,
        )
