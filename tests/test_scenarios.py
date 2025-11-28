# tests/test_scenarios.py
from agents.coordinator import A2ACoordinator
from mcp_server.server import ensure_database


def test_simple_query():
    ensure_database()
    coord = A2ACoordinator()
    answer, log = coord.run("Get customer information for ID 1")
    assert "Customer #1" in answer or "No customer found" in answer
    assert any("router -> customer_data" in line for line in log)


def test_complex_query():
    ensure_database()
    coord = A2ACoordinator()
    answer, log = coord.run("Show me all active customers who have open tickets")
    assert "Active customers with open tickets" in answer
