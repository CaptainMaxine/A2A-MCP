# agents/coordinator.py

from typing import Dict, List, Tuple
from .base_agent import A2AMessage
from .router_agent import RouterAgent
from .customer_data_agent import CustomerDataAgent
from .support_agent import SupportAgent


class A2ACoordinator:
    """
    Orchestrates the A2A loop:
    - Holds router, customer_data, support agents
    - Runs multi-step message passing
    - Handles Scenario 2 special behavior:
        SupportAgent needs billing context ->
        Router sets flag -> Coordinator fetches via MCP ->
        State enriched -> Resume to SupportAgent
    """

    def __init__(self, mcp_client):
        self.router = RouterAgent()
        self.customer_data = CustomerDataAgent(mcp_client)
        self.support = SupportAgent(mcp_client)
        self.agents = {
            "router": self.router,
            "customer_data": self.customer_data,
            "support": self.support,
        }
        self.mcp = mcp_client

    # -------------------------------------------------------------
    # Core run loop
    # -------------------------------------------------------------
    def run(self, query: str, max_steps: int = 12) -> Tuple[str, List[str]]:
        """
        Run A2A from raw user query until final answer (to user).

        Returns:
          final_text, log_lines
        """

        log: List[str] = []

        # Initial message: user -> router
        msg = A2AMessage(
            sender="user",
            receiver="router",
            role="user",
            content=query,
            state={},
        )

        for step in range(1, max_steps + 1):

            # ---------------------------
            # Logging this step
            # ---------------------------
            log.append(
                f"[STEP {step}] {msg.sender} -> {msg.receiver} | content='{msg.content}' | state={msg.state}"
            )

            # ---------------------------
            # Final answer?
            # ---------------------------
            if msg.receiver == "user" and msg.sender != "router":
                # SupportAgent or fallback responded directly
                return msg.content, log

            # ---------------------------
            # Scenario 2 special logic:
            # Router → Data → support history fetch
            # ---------------------------
            state = msg.state

            if (
                state.get("router_should_fetch_history_via_data_agent")
                and msg.sender == "router"
                and msg.receiver == "customer_data"
                and state.get("action") == "get_customer_history"
            ):
                # Router told coordinator to fetch history via MCP.
                customer_id = state.get("customer_id")
                history_response = self.mcp.call(
                    tool="get_customer_history",
                    arguments={"customer_id": customer_id},
                )

                # Inject into state
                state["customer_history"] = history_response.get("result")
                # Clear flag
                state.pop("router_should_fetch_history_via_data_agent", None)

                # Now send it to SupportAgent
                msg = A2AMessage(
                    sender="router",
                    receiver="support",
                    role="agent",
                    content="[Coordinator] Injected billing history into state; handing to SupportAgent.",
                    state=state,
                )
                continue

            # ---------------------------
            # Normal A2A message passing:
            # find the next agent and call `handle()`
            # ---------------------------
            receiver = msg.receiver
            if receiver not in self.agents:
