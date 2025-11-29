# agents/customer_data_agent.py
from typing import Dict, Any, List

from .base_agent import BaseAgent, A2AMessage
from .mcp_client import MCPClient


class CustomerDataAgent(BaseAgent):
    """
    Deterministic data-specialist agent for MCP-backed database access.

    Responsibilities:
    - Fetch customer records
    - Update customer data
    - List premium/active customers
    - Retrieve ticket history
    - Return structured information back to RouterAgent

    IMPORTANT:
    This agent *does not* use an LLM. It must be deterministic.
    """

    def __init__(self, mcp_client: MCPClient):
        super().__init__(name="customer_data")
        self.mcp = mcp_client

    # ------------------------------------------------------
    # Main handler
    # ------------------------------------------------------
    def handle(self, message: A2AMessage) -> A2AMessage:
        state = dict(message.state)
        scenario = state.get("scenario")
        content = message.content

        print(f"[CustomerDataAgent] Received: scenario={scenario}, content={content}")

        # ------------------------------------------------------
        # CASE 1 — Customer lookup
        # Router requires customer_id → DataAgent retrieves it
        # ------------------------------------------------------
        if "customer_id" in state and state["customer_id"] is not None:
            cid = state["customer_id"]
            customer = self.mcp.get_customer(cid)
            state["customer"] = customer

            return A2AMessage(
                sender=self.name,
                receiver="router",
                role="agent",
                content="customer_context_ready",
                state=state,
            )

        # ------------------------------------------------------
        # CASE 2 — Scenario: list active customers
        # Used for query: "Show me all active customers who have open tickets"
        # ------------------------------------------------------
        if scenario == "active_customers_with_open_tickets":
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
        # CASE 3 — Scenario: list premium customers
        # Used for scenario_3: high-priority tickets for premium customers
        # ------------------------------------------------------
        if scenario == "high_priority_for_premium":
            # Your DB has no "premium" flag → we approximate with status="active"
            customers = self.mcp.list_customers(status="active")
            state["premium_customers"] = customers

            return A2AMessage(
                sender=self.name,
                receiver="router",
                role="agent",
                content="premium_customers_ready",
                state=state,
            )

        # ------------------------------------------------------
        # CASE 4 — Scenario: get history for explicit customer
        # Used in: "update email and show my ticket history"
        # ------------------------------------------------------
        if scenario == "update_email_and_history":
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
        # DEFAULT: No operation
        # ------------------------------------------------------
        print("[CustomerDataAgent] Warning: no matching scenario. Returning noop.")
        return A2AMessage(
            sender=self.name,
            receiver="router",
            role="agent",
            content="data_agent_noop",
            state=state,
        )
