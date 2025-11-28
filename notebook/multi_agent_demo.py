# notebook/multi_agent_demo.py
"""
This file is just a linear Python version of what you'd put into a
Jupyter / Colab notebook. Split into cells as needed.
"""

from mcp_server.server import ensure_database
from agents.coordinator import A2ACoordinator

# 1. Init DB + coordinator
ensure_database()
coord = A2ACoordinator()

# 2. Define test queries from assignment
queries = [
    # Simple Query
    "Get customer information for ID 5",

    # Coordinated Query
    "I'm customer 1 and need help upgrading my account",

    # Complex Query
    "Show me all active customers who have open tickets",

    # Escalation
    "I'm customer 1 and I've been charged twice, please refund immediately!",

    # Multi-Intent
    "I'm customer 1, update my email to new@email.com and show my ticket history",

    # Scenario 1 (Task Allocation)
    "I need help with my account, customer ID 1",

    # Scenario 2 (Negotiation/Escalation)
    "I want to cancel my subscription but I'm having billing issues",

    # Scenario 3 (Multi-step Coordination)
    "What's the status of all high-priority tickets for premium customers?"
]

for q in queries:
    print("=" * 80)
    print("USER:", q)
    print("=" * 80)

    answer, log = coord.run(q)

    print("\nA2A LOG:")
    for line in log:
        print(" ", line)

    print("\nFINAL ANSWER:")
    print(answer)
    print("\n\n")
