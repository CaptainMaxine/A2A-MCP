# mcp_server/tools.py
"""
MCP-style tools wrapping low-level DB helpers.

In your actual MCP server, you'll expose these functions
as MCP tools (e.g. with decorators from your course framework).
"""

from typing import Any, Dict, List, Optional

from . import db


# Required by assignment:

def get_customer(customer_id: int) -> Optional[Dict[str, Any]]:
    """Tool: get_customer(customer_id)"""
    return db.get_customer(customer_id)


def list_customers(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Tool: list_customers(status, limit)"""
    return db.list_customers(status=status, limit=limit)


def update_customer(customer_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Tool: update_customer(customer_id, data)"""
    return db.update_customer(customer_id, data)


def create_ticket(
    customer_id: int,
    issue: str,
    priority: str = "medium",
) -> Dict[str, Any]:
    """Tool: create_ticket(customer_id, issue, priority)"""
    return db.create_ticket(customer_id=customer_id, issue=issue, priority=priority)


def get_customer_history(customer_id: int) -> List[Dict[str, Any]]:
    """Tool: get_customer_history(customer_id)"""
    return db.get_customer_history(customer_id)


# Extra helper tool for scenario 3 / complex queries:

def list_open_tickets_for_customers(
    customer_ids: List[int],
    priority: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return db.list_open_tickets_for_customers(customer_ids=customer_ids, priority=priority)
