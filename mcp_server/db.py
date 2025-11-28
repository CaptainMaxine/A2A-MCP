# mcp_server/db.py
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent / "support.db"


@contextmanager
def get_conn():
    """Context manager returning a SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row) if row is not None else {}


# ---------- Customer operations ----------

def get_customer(customer_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single customer by id."""
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT id, name, email, phone, status, created_at, updated_at
            FROM customers
            WHERE id = ?
            """,
            (customer_id,),
        )
        row = cur.fetchone()
        return _row_to_dict(row) if row else None


def list_customers(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    List customers, optionally filtered by status.

    status: 'active' | 'disabled' | None
    """
    with get_conn() as conn:
        if status:
            cur = conn.execute(
                """
                SELECT id, name, email, phone, status, created_at, updated_at
                FROM customers
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (status, limit),
            )
        else:
            cur = conn.execute(
                """
                SELECT id, name, email, phone, status, created_at, updated_at
                FROM customers
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def update_customer(customer_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update customer fields.

    data keys may include: name, email, phone, status.
    Returns the updated record, or None if customer not found.
    """
    ALLOWED_FIELDS = {"name", "email", "phone", "status"}
    updates = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}

    if not updates:
        # Nothing to update
        return get_customer(customer_id)

    set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
    updates["id"] = customer_id

    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE customers SET {set_clause} WHERE id = :id",
            updates,
        )
        if cur.rowcount == 0:
            return None

    # Trigger will auto-update updated_at
    return get_customer(customer_id)


# ---------- Ticket operations ----------

def create_ticket(
    customer_id: int,
    issue: str,
    priority: str = "medium",
    status: str = "open",
) -> Dict[str, Any]:
    """
    Create a new ticket. Priority: 'low'|'medium'|'high'.
    Status: 'open'|'in_progress'|'resolved' (default 'open').
    """
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tickets (customer_id, issue, status, priority)
            VALUES (?, ?, ?, ?)
            """,
            (customer_id, issue, status, priority),
        )
        ticket_id = cur.lastrowid

        cur = conn.execute(
            """
            SELECT id, customer_id, issue, status, priority, created_at
            FROM tickets
            WHERE id = ?
            """,
            (ticket_id,),
        )
        row = cur.fetchone()
        return _row_to_dict(row)


def get_customer_history(customer_id: int) -> List[Dict[str, Any]]:
    """Return all tickets for a given customer, most recent first."""
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT id, customer_id, issue, status, priority, created_at
            FROM tickets
            WHERE customer_id = ?
            ORDER BY created_at DESC
            """,
            (customer_id,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def list_open_tickets_for_customers(
    customer_ids: List[int],
    priority: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Helper used by SupportAgent:
    Return open tickets (optionally only a given priority)
    for a list of customer IDs.
    """
    if not customer_ids:
        return []

    placeholders = ", ".join("?" for _ in customer_ids)
    params: List[Any] = list(customer_ids)

    query = f"""
        SELECT id, customer_id, issue, status, priority, created_at
        FROM tickets
        WHERE status = 'open'
          AND customer_id IN ({placeholders})
    """

    if priority:
        query += " AND priority = ?"
        params.append(priority)

    with get_conn() as conn:
        cur = conn.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
