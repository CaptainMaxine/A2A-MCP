# agents/base_agent.py
from dataclasses import dataclass, field
from typing import Any, Dict, Literal

Role = Literal["user", "system", "agent"]


@dataclass
class A2AMessage:
    """
    Generic message passed between agents.

    - sender: name of the agent or "user"
    - receiver: target agent name or "user"
    - role: semantic role (user/system/agent)
    - content: natural language content
    - state: shared structured state between agents
    """
    sender: str
    receiver: str
    role: Role
    content: str
    state: Dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    """Base class for all agents."""

    def __init__(self, name: str):
        self.name = name

    def handle(self, message: A2AMessage) -> A2AMessage:
        """
        Process an incoming message and return a new message.

        Subclasses must override this method.
        """
        raise NotImplementedError
