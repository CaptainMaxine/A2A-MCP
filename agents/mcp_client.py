# agents/mcp_client.py
"""
Simple in-process MCP client.

In a real MCP setup, you'd replace this class implementation so that
each method performs a remote call to your MCP server.

The rest of the agent code only depends on this interface, so you can
swap the implementation without touching agents.
"""

from typing import Any, Dict, List, Optional

from mcp_server import tools


class MCPClient:
    def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        return tools.get_customer(customer_id)

    def list_customers(self, status: Optional[str] = None, limit: int = 50):
        return tools.list_customers(status=status, limit=limit)

    def update_customer(self, customer_id: int, data: Dict[str, Any]):
        return tools.update_customer(customer_id, data)

    def create_ticket(self, customer_id: int, issue: str, priority: str = "medium"):
        return tools.create_ticket(customer_id=customer_id, issue=issue, priority=priority)

    def get_customer_history(self, customer_id: int):
        return tools.get_customer_history(customer_id)

    def list_open_tickets_for_customers(
        self, customer_ids: List[int], priority: Optional[str] = None
    ):
        return tools.list_open_tickets_for_customers(customer_ids=customer_ids, priority=priority)

