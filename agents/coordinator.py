# agents/coordinator.py

from agents.router_agent import RouterAgent
from agents.customer_data_agent import CustomerDataAgent
from agents.support_agent import SupportAgent
from agents.mcp_client import MCPClient
from agents.base_agent import A2AMessage


class A2ACoordinator:
    def __init__(self):
        self.mcp = MCPClient()

        # Initialize agents
        self.router = RouterAgent()
        self.customer_data_agent = CustomerDataAgent(self.mcp)
        self.support_agent = SupportAgent(self.mcp)

        # Agent registry
        self.agents = {
            "router": self.router,
            "customer_data": self.customer_data_agent,
            "support": self.support_agent,
        }

    def run(self, query: str):
        """Runs a single end-to-end A2A workflow."""
        log = []
        message = A2AMessage(
            sender="user",
            receiver="router",
            content=query,
            state={}
        )

        for step in range(15):
            log.append(
                f"[STEP {step+1}] {message.sender} → {message.receiver} | content={message.content} | state={message.state}"
            )

            # Final answer returned to user
            if message.receiver == "user":
                return message.content, log

            receiver = message.receiver

            # Validate receiver
            if receiver not in self.agents:
                return f"ERROR: Unknown receiver '{receiver}'", log

            agent = self.agents[receiver]
            message = agent.handle(message)

        return "ERROR: Max steps exceeded", log


def run_demo():
    """Runs all required assignment scenarios."""

    coordinator = A2ACoordinator()

    scenarios = [
        # Scenario 1
        "I need help with my account, customer ID 12345",

        # Scenario 2
        "I want to cancel my subscription but I'm having billing issues",

        # Scenario 3
        "What's the status of all high-priority tickets for premium customers?",

        # Simple Query
        "Get customer information for ID 5",

        # Coordinated Query
        "I'm customer 12345 and need help upgrading my account",

        # Complex Query
        "Show me all active customers who have open tickets",

        # Escalation
        "I've been charged twice, please refund immediately!",

        # Multi-intent
        "Update my email to new@email.com and show my ticket history",
    ]

    for q in scenarios:
        print("\n" + "=" * 80)
        print(f"QUERY: {q}")
        print("=" * 80)

        response, log = coordinator.run(q)

        for line in log:
            print(line)

        print("\nFINAL RESPONSE:", response)
        print("\n" + "-" * 80)


if __name__ == "__main__":
    run_demo()
