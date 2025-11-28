# mcp_server/server.py
"""
Lightweight "server" bootstrap.

In the real assignment, replace the placeholders with the actual
MCP server framework your course uses (e.g. decorators to expose
tools from tools.py).

Here we only ensure that `support.db` exists and print a message.
"""

from pathlib import Path

from .database_setup import DatabaseSetup  # your provided class
from . import tools  # noqa: F401  # imported so this file "sees" the tools


def ensure_database(db_path: str = "support.db") -> None:
    """Create DB and tables if they don't exist yet."""
    path = Path(db_path)
    if path.exists():
        print(f"[MCP Server] Found existing database at {path.resolve()}")
        return

    print(f"[MCP Server] Database {db_path} not found, creating...")
    setup = DatabaseSetup(db_path=db_path)
    setup.connect()
    setup.create_tables()
    setup.create_triggers()
    # Optionally insert sample data automatically:
    setup.insert_sample_data()
    setup.close()
    print("[MCP Server] Database initialized with sample data.")


def main():
    ensure_database()
    # TODO: Replace this with your actual MCP server startup code.
    print("[MCP Server] Tools are ready to be exposed via MCP.")
    print("  Tools: get_customer, list_customers, update_customer,")
    print("         create_ticket, get_customer_history")
    print("This sample version does not start a network server;")
    print("agents call tools in-process via MCPClient.")


if __name__ == "__main__":
    main()
