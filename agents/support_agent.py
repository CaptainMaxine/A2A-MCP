from typing import Dict, List
import os
from openai import OpenAI

from .base_agent import A2AMessage, BaseAgent
from .mcp_client import MCPClient


class SupportAgent(BaseAgent):
    """
    General support specialist.
    """

    def __init__(self, mcp_client: MCPClient):
        super().__init__(name="support")
        self.mcp = mcp_client
        self.llm = self._make_llm()       # <-- FIXED: add LLM

    # ------------------------------------------------------
    # Build LLM client
    # ------------------------------------------------------
    def _make_llm(self):
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        def run(system_prompt: str, user_prompt: str) -> str:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return resp.choices[0].message.content

        return run

    # ------------------------------------------------------
    # Helper formatters
    # ------------------------------------------------------
    def _format_customer_summary(self, customer: Dict) -> str:
        return (
            f"Customer #{customer['id']}: {customer['name']} "
            f"(status: {customer['status']}, email: {customer.get('email')})"
        )

    def _format_ticket_line(self, t: Dict) -> str:
        return (
            f"Ticket #{t['id']} | status={t['status']} | "
            f"priority={t['priority']} | issue={t['issue']}"
        )

    # ------------------------------------------------------
    # Main logic (same as你的版本, but with LLM rewrite at end)
    # ------------------------------------------------------
    def handle(self, message: A2AMessage) -> A2AMessage:
        state = dict(message.state)
        scenario = state.get("scenario")

        # ... your entire scenario logic 保持原样 ...
        # 我不在这里贴全部，因为你已有完整代码。
        # 唯一关键是“最后需要 llm 来 rewrite content”。

        # ---- 假设 content 已经生成 ----
        content = state.get("draft_reply", "Support message placeholder")

        # Build context
        original_query = state.get("original_query", message.content)
        customer = state.get("customer")
        history = state.get("customer_history", [])

        lines = []
        if customer:
            lines.append(
                f"Customer #{customer['id']} - {customer['name']} "
                f"(status={customer['status']}, email={customer.get('email')})"
            )
        if history:
            lines.append("Recent tickets:")
            for t in history[:5]:
                lines.append(
                    f"- #{t['id']} [{t['priority']}] {t['issue']} (status={t['status']})"
                )

        context_block = "\n".join(lines) if lines else "No extra context."

        # System prompt
        system_prompt = (
            "You are an expert support agent. "
            "Rewrite the draft reply to be professional and empathetic. "
            "Do NOT invent facts."
        )

        user_prompt = (
            f"User query:\n{original_query}\n\n"
            f"Context:\n{context_block}\n\n"
            f"Draft reply:\n{content}\n\n"
            "Rewrite into final message."
        )

        # LLM polishing
        final_content = self.llm(system_prompt, user_prompt)

        return A2AMessage(
            sender=self.name,
            receiver="router",
            role="agent",
            content=final_content,
            state=state,
        )
