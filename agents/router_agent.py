import json
from typing import Dict, List

from .base_agent import A2AMessage, BaseAgent


class RouterAgent(BaseAgent):
    """
    Router / Orchestrator.
    Responsibilities:
    - Classify user intent using an LLM
    - Determine scenario
    - Route messages to CustomerDataAgent and SupportAgent
    - Aggregate state and return final message
    """

    def __init__(self):
        super().__init__(name="router")
        self.llm = self._make_llm()   # <-- IMPORTANT

    # ------------------------------------------------------
    # 1. Intent Classification via LLM
    # ------------------------------------------------------
    def classify_intent(self, user_query: str) -> Dict:
        system_prompt = (
            "You are an intent classification model. "
            "Extract intents from the query. "
            "Return JSON with fields: intents[], customer_id, scenario."
        )

        user_prompt = f"User query: {user_query}\n\nExtract intents."

        raw = self.llm(system_prompt, user_prompt)

        # Safe JSON parse
        try:
            data = json.loads(raw)
        except:
            data = {"intents": ["unknown"], "scenario": "unknown"}

        return data

    # ------------------------------------------------------
    # 2. Route messages between agents
    # ------------------------------------------------------
    def handle(self, message: A2AMessage) -> A2AMessage:
        state = dict(message.state)

        # If this is the first turn
        if message.sender == "user":
            intents = self.classify_intent(message.content)
            state.update(intents)
            state["original_query"] = message.content

            # extract scenario for routing
            scenario = intents.get("scenario")

            # Route to data agent first if customer_id is needed
            if "customer_id" in intents and intents["customer_id"]:
                return A2AMessage(
                    sender="router",
                    receiver="customer_data",
                    role="agent",
                    content=message.content,
                    state=state,
                )

            # If no customer needed → go directly to support
            return A2AMessage(
                sender="router",
                receiver="support",
                role="agent",
                content=message.content,
                state=state,
            )

        # ------------------------------------------------------
        # If message comes back from CustomerDataAgent
        # ------------------------------------------------------
        if message.sender == "customer_data":
            state.update(message.state)

            # After getting data → always go to support
            return A2AMessage(
                sender="router",
                receiver="support",
                role="agent",
                content=message.content,
                state=state,
            )

        # ------------------------------------------------------
        # If message comes back from SupportAgent
        # Final answer — return to user
        # ------------------------------------------------------
        if message.sender == "support":
            return A2AMessage(
                sender="router",
                receiver="user",
                role="system",
                content=message.content,
                state=state,
            )

        # Fallback
        return A2AMessage(
            sender="router",
            receiver="user",
            role="system",
            content="[RouterAgent] Unable to route message.",
            state=state,
        )
