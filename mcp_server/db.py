# mcp_server/db.py
import sqlite3
from typing import Any, Dict, List, Optional
from pathlib import Path

DB_PATH = Path(__file__).parent / "customers.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def dictify(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


# ---- MCP tools core logic ----

def get_customer(customer_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    conn.close()
    return dictify(row) if row else None


def list_customers(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    if status:
        cur.execute(
            "SELECT * FROM customers WHERE status = ? ORDER BY id LIMIT ?",
            (status, limit),
        )
    else:
        cur.execute("SELECT * FROM customers ORDER BY id LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dictify(r) for r in rows]


def update_customer(customer_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    data 可以包含: name, email, phone, status
    """
    if not data:
        return get_customer(customer_id)

    allowed_fields = {"name", "email", "phone", "status"}
    fields = [k for k in data.keys() if k in allowed_fields]
    if not fields:
        return get_customer(customer_id)

    conn = get_connection()
    cur = conn.cursor()

    set_clause = ", ".join([f"{f} = ?" for f in fields])
    values = [data[f] for f in fields]
    values.append(customer_id)

    cur.execute(f"UPDATE customers SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE id = ?", values)
    conn.commit()
    conn.close()

    return get_customer(customer_id)


def create_ticket(customer_id: int, issue: str, priority: str = "medium") -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO tickets (customer_id, issue, status, priority, created_at)
        VALUES (?, ?, 'open', ?, CURRENT_TIMESTAMP)
        """,
        (customer_id, issue, priority),
    )
    ticket_id = cur.lastrowid
    conn.commit()
    cur.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cur.fetchone()
    conn.close()
    return dictify(row)


def get_customer_history(customer_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM tickets WHERE customer_id = ? ORDER BY created_at DESC",
        (customer_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dictify(r) for r in rows]
