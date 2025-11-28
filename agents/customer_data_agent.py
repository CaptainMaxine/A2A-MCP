# agents/customer_data_agent.py
from typing import Any, Dict

from .base_agent import A2AMessage, BaseAgent
from .mcp_client import MCPClient


class CustomerDataAgent(BaseAgent):
    """
    Specialist for customer & ticket data.

    Responsibilities (per assignment):
    - Access customer database via MCP
    - Retrieve customer information
    - Update customer records
    - Handle data validation
    """

    def __init__(self, mcp_client: MCPClient):
        super().__init__(name="customer_data")
        self.mcp = mcp_client

    def handle(self, message: A2AMessage) -> A2AMessage:
        state = dict(message.state)  # shallow copy
        action = state.get("action")

        if action == "get_customer":
            customer_id = state.get("customer_id")
            customer = self.mcp.get_customer(customer_id)
            state["customer"] = customer

            content = (
                f"[CustomerDataAgent] Retrieved customer {customer_id}."
                if customer
                else f"[CustomerDataAgent] No customer found for id={customer_id}."
            )

        elif action == "list_premium_customers":
            # For demo, treat all 'active' customers as 'premium'.
            customers = self.mcp.list_customers(status="active", limit=100)
            state["premium_customers"] = customers
            state["premium_customer_ids"] = [c["id"] for c in customers]
            content = f"[CustomerDataAgent] Found {len(customers)} premium (active) customers."

        elif action == "get_active_customers_with_open_tickets":
            # Data agent can return active customers; support agent will inspect tickets.
            customers = self.mcp.list_customers(status="active", limit=200)
            state["active_customers"] = customers
            state["active_customer_ids"] = [c["id"] for c in customers]
            content = (
                f"[CustomerDataAgent] Listed {len(customers)} active customers "
                f"for open-ticket analysis."
            )

        elif action == "update_customer_email":
            customer_id = state.get("customer_id")
            new_email = state.get("new_email")
            updated = self.mcp.update_customer(customer_id, {"email": new_email})
            state["updated_customer"] = updated
            content = (
                f"[CustomerDataAgent] Updated email to {new_email} for customer {customer_id}."
                if updated
                else f"[CustomerDataAgent] Failed to update customer {customer_id}."
            )

        else:
            content = "[CustomerDataAgent] No recognized action; passing through."
            # no state change

        # Always reply to router
        return A2AMessage(
            sender=self.name,
            receiver="router",
            role="agent",
            content=content,
            state=state,
        )
