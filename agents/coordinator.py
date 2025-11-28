# agents/coordinator.py

from agents.router_agent import RouterAgent
from agents.customer_data_agent import CustomerDataAgent
from agents.support_agent import SupportAgent
from agents.mcp_client import MCPClient
from agents.base_agent import A2AMessage


class A2ACoordinator:
    """
    Main controller that routes messages between agents and logs the steps.
    """

    def __init__(self):
        self.mcp = MCPClient()

        # Instantiate agents
        self.router = RouterAgent()
        self.customer_data = CustomerDataAgent(self.mcp)
        self.support = SupportAgent(self.mcp)

        # Agent registry
        self.agents = {
            "router": self.router,
            "customer_data": self.customer_data,
            "support": self.support
        }

    def run(self, query: str):
        """
        Run a single user query through the A2A system.
        """
        print("\n==============================")
        print(f"USER QUERY: {query}")
        print("==============================\n")

        # Initial message to RouterAgent
        message = A2AMessage(
            sender="user",
            receiver="router",
            content=query,
            state={}
        )

        steps = 0
        max_steps = 20

        while steps < max_steps:
            steps += 1

            print(f"[STEP {steps}] {message.sender} → {message.receiver}")
            print(f"  Content: {message.content}")
            print(f"  State: {message.state}\n")

            receiver = message.receiver

            # If message goes back to user → finished
            if receiver == "user":
                print("=== FINAL ANSWER ===")
                print(message.content)
                print("====================\n")
                return message.content

            # Safety check
            if receiver not in self.agents:
                raise ValueError(f"Unknown receiver agent: {receiver}")

            # Call the appropriate agent
            agent = self.agents[receiver]
            message = agent.handle(message)

        raise RuntimeError("A2A exceeded maximum steps (possible infinite loop).")


# -------------------------
# Built-in scenarios
# -------------------------

def demo_scenarios():
    coord = A2ACoordinator()

    queries = [
        "I need help with my account, customer ID 12345",
        "I want to cancel my subscription but I'm having billing issues",
        "What's the status of all high-priority tickets for premium customers?",
        "Get customer information for ID 5",
        "I'm customer 12345 and need help upgrading my account",
        "Show me all active customers who have open tickets",
        "I've been charged twice, please refund immediately!",
        "Update my email to new@email.com and show my ticket history"
    ]

    for q in queries:
        coord.run(q)


# When running via: python -m agents.coordinator
if __name__ == "__main__":
    demo_scenarios()
