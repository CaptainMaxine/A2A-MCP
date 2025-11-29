import json
from typing import Dict
from openai import OpenAI
import os

from .base_agent import A2AMessage, BaseAgent


class RouterAgent(BaseAgent):
    """
    Router / Orchestrator agent.
    Responsibilities:
    - Use LLM to classify user intent
    - Determine scenario
    - Route messages to agents
    - Aggregate state
    """

    def __init__(self):
        super().__init__(name="router")
        self.llm = self._make_llm()   # <-- FIXED: now exists

    # ------------------------------------------------------
    # Build LLM client
    # ------------------------------------------------------
    def _make_llm(self):
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        def run(system_prompt: str, user_prompt: str) -> str:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return resp.choices[0].message.content

        return run

    # ------------------------------------------------------
    # Intent Classification
    # ------------------------------------------------------
    def classify_intent(self, user_query: str) -> Dict:
        system_prompt = (
            "You are an intent classifier. "
            "Given a user query, extract: intents[], customer_id, scenario.\n"
            "Choose scenario from: simple_get, coordinated_upgrade, "
            "open_tickets, refund_escalation, update_email_and_history.\n"
            "Return ONLY valid JSON."
        )

        user_prompt = f"User query: {user_query}\nExtract JSON."

        raw = self.llm(system_prompt, user_prompt)

        try:
            parsed = json.loads(raw)
        except:
            parsed = {"intents": ["unknown"], "scenario": "unknown", "customer_id": None}

        return parsed

    # ------------------------------------------------------
    # Router logic
    # ------------------------------------------------------
    def handle(self, message: A2AMessage) -> A2AMessage:
        state = dict(message.state)

        # -------- FIRST TURN: From user ----------
        if message.sender == "user":
            intents = self.classify_intent(message.content)
            state.update(intents)
            state["original_query"] = message.content

            customer_id = intents.get("customer_id")

            # Need customer data first → send to CustomerDataAgent
            if customer_id:
                return A2AMessage(
                    sender="router",
                    receiver="customer_data",
                    role="agent",
                    content=message.content,
                    state=state,
                )

            # No customer ID → go directly to SupportAgent
            return A2AMessage(
                sender="router",
                receiver="support",
                role="agent",
                content=message.content,
                state=state,
            )

        # -------- RETURN: From CustomerDataAgent ----------
        if message.sender == "customer_data":
            state.update(message.state)
            return A2AMessage(
                sender="router",
                receiver="support",
                role="agent",
                content=message.content,
                state=state,
            )

        # -------- FINAL RETURN: From SupportAgent ----------
        if message.sender == "support":
            return A2AMessage(
                sender="router",
                receiver="user",
                role="system",
                content=message.content,
                state=state,
            )

        # fallback
        return A2AMessage(
            sender="router",
            receiver="user",
            role="system",
            content="[Router] Could not route message.",
            state=state,
        )
