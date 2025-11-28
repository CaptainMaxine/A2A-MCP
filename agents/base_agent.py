# agents/base_agent.py
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class A2AMessage:
    sender: str          # agent name or "user"
    receiver: str        # target agent name or "user"
    role: str            # "user", "system", or "agent"
    content: str         # free text query or instruction
    state: Dict[str, Any] = field(default_factory=dict)

class BaseAgent:
    def __init__(self, name: str, mcp_client=None):
        self.name = name
        self.mcp = mcp_client

    def handle(self, message: A2AMessage) -> A2AMessage:
        """
        Must be implemented by RouterAgent / CustomerDataAgent / SupportAgent.
        Returns a new A2AMessage.
        """
        raise NotImplementedError
