# agents/customer_data_agent.py
from typing import Dict, Any, List

from .base_agent import BaseAgent, A2AMessage
from .mcp_client import MCPClient


class CustomerDataAgent(BaseAgent):
    """
    Data-specialist agent responsible for:
    - Fetching customer records
    - Updating customer data
    - Listing premium/active customers
    - Retrieving ticket history
    - Returning structured information in state for Router & SupportAgent

    This agent does NOT use an LLM.
    It is a deterministic DB specialist.
    """

    def __init__(self, mcp_client: MCPClient):
        super().__init__(name="data")
        self.mcp = mcp_client

    # ------------------------------------------------------
    # Main handler
    # ------------------------------------------------------
    def handle(self, message: A2AMessage) -> A2AMessage:
        state = dict(message.state)
        scenario = state.get("scenario")
        content = message.content

        print(f"[DataAgent] Received from router: {scenario} / {content}")

        # ------------------------------------------------------
        # 1) Lookup customer by ID
        # ------------------------------------------------------
        if content == "lookup_customer":
            cid = state.get("customer_id")
            if cid:
                customer = self.mcp.get_customer(cid)
                state["customer"] = customer
            else:
                state["customer"] = None

            return A2AMessage(
                sender=self.name,
                receiver="router",
                role="agent",
                content="customer_context_ready",
                state=state,
            )

        # ------------------------------------------------------
        # 2) List premium customers (Scenario 3)
        # ------------------------------------------------------
        if content == "list_premium_customers":
            # Premium = status = "active" AND plan = premium (your DB doesn't have plan, so approximate)
            # Here we treat "active" as your original logic.
            customers = self.mcp.list_customers(status="active")
            # You can add filtering logic if your DB had a premium flag.
            state["premium_customers"] = customers

            return A2AMessage(
                sender=self.name,
                receiver="router",
                role="agent",
                content="premium_customers_ready",
                state=state,
            )

        # ------------------------------------------------------
        # 3) List active customers (Scenario: active_customers_with_open_tickets)
        # ------------------------------------------------------
        if content == "list_active_customers":
            customers = self.mcp.list_customers(status="active")
            state["active_customers"] = customers

            return A2AMessage(
                sender=self.name,
                receiver="router",
                role="agent",
                content="active_customers_ready",
                state=state,
            )

        # ------------------------------------------------------
        # 4) Fetch ticket history for a customer
        # ------------------------------------------------------
        if content == "get_history":
            cid = state.get("customer_id")
            if cid:
                history = self.mcp.get_customer_history(cid)
                state["customer_history"] = history
            else:
                state["customer_history"] = []

            return A2AMessage(
                sender=self.name,
                receiver="router",
                role="agent",
                content="history_ready",
                state=state,
            )

        # ------------------------------------------------------
        # 5) Default fallback (should not happen)
        # ------------------------------------------------------
        print("[DataAgent] Warning: Unrecognized command from RouterAgent.")
        return A2AMessage(
            sender=self.name,
            receiver="router",
            role="agent",
            content="data_agent_noop",
            state=state,
        )
