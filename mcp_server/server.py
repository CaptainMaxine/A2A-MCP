# mcp_server/server.py

from pathlib import Path
from .database_setup import DatabaseSetup


def ensure_database():
    """Always create DB inside the mcp_server folder."""
    db_path = Path(__file__).parent / "support.db"

    if db_path.exists():
        print(f"[MCP Server] Found existing database at {db_path}")
        return

    print(f"[MCP Server] Creating database at {db_path} ...")

    setup = DatabaseSetup(db_path=str(db_path))
    setup.connect()
    setup.create_tables()
    setup.create_triggers()
    setup.insert_sample_data()
    setup.close()

    print("[MCP Server] Database initialized with sample data.")
    print(f"[MCP Server] Database stored at: {db_path}")


def main():
    ensure_database()
    print("[MCP Server] Tools ready for MCPClient (in-process mode).")


if __name__ == "__main__":
    main()
