# agents/support_agent.py
from typing import Dict, List

from .base_agent import A2AMessage, BaseAgent
from .mcp_client import MCPClient


class SupportAgent(BaseAgent):
    """
    General support specialist.

    Responsibilities:
    - Handle general support questions
    - Escalate complex issues
    - Request customer context from Data Agent (via Router)
    - Create tickets, summarize history, generate responses
    """

    def __init__(self, mcp_client: MCPClient):
        super().__init__(name="support")
        self.mcp = mcp_client

    # ---- Helper response formatters ----

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

    # ---- Main handler ----

    def handle(self, message: A2AMessage) -> A2AMessage:
        state = dict(message.state)
        scenario = state.get("scenario")
        intent = state.get("intent")
        intents: List[str] = state.get("intents", [])
        content: str

        # Scenario 1 / simple support after data lookup
        if scenario in {"scenario_1_task_allocation", "simple_get_and_support"}:
            customer = state.get("customer")
            issue = state.get("issue") or "help with your account"
            if customer:
                summary = self._format_customer_summary(customer)
                content = (
                    f"[SupportAgent] Hi {customer['name']}, I see your account is "
                    f"{customer['status']}. Let's look into {issue}.\n\n"
                    f"{summary}"
                )
            else:
                content = (
                    "[SupportAgent] I couldn't find your account. "
                    "Please double-check your customer ID."
                )

        # Coordinated upgrade (test: “need help upgrading my account”)
        elif scenario == "coordinated_upgrade":
            customer = state.get("customer")
            if customer:
                content = (
                    f"[SupportAgent] Customer {customer['name']} wants to upgrade.\n"
                    "Recommendation: move to Premium Plan. I have created a high-priority "
                    "ticket so billing can process the upgrade."
                )
                ticket = self.mcp.create_ticket(
                    customer_id=customer["id"],
                    issue="Customer requested account upgrade",
                    priority="high",
                )
                state["created_ticket"] = ticket
            else:
                content = "[SupportAgent] No customer context yet; need customer_id."

        # Negotiation / escalation (Scenario 2)
        elif scenario == "cancel_and_billing":
            # First time: if we don't yet have billing context, ask router to obtain it.
            if not state.get("billing_context_ready"):
                content = (
                    "[SupportAgent] I can cancel the subscription but need billing context "
                    "first (recent tickets / charges)."
                )
                state["support_needs_billing_context"] = True
            else:
                customer = state.get("customer")
                history = state.get("customer_history", [])
                summary_lines = [self._format_ticket_line(t) for t in history[:5]]
                summary = "\n".join(summary_lines) or "No previous billing tickets."

                if customer:
                    cust_name = customer["name"]
                else:
                    cust_name = "customer"

                content = (
                    f"[SupportAgent] Hi {cust_name}, I can help with cancellation and "
                    f"your billing issue. Based on your recent history:\n{summary}\n\n"
                    "I will open a high-priority refund ticket and cancel your subscription."
                )
                ticket = self.mcp.create_ticket(
                    customer_id=customer["id"],
                    issue="Refund requested due to double charge & cancellation",
                    priority="high",
                )
                state["created_ticket"] = ticket

        # Scenario 3: multi-step high-priority tickets for premium customers
        elif scenario == "high_priority_for_premium":
            premium_customers = state.get("premium_customers", [])
            premium_ids = [c["id"] for c in premium_customers]
            high_tickets = self.mcp.list_open_tickets_for_customers(
                customer_ids=premium_ids, priority="high"
            )
            state["high_priority_tickets"] = high_tickets

            lines = []
            for t in high_tickets:
                cust = next(
                    (c for c in premium_customers if c["id"] == t["customer_id"]),
                    None,
                )
                cname = cust["name"] if cust else f"Customer {t['customer_id']}"
                lines.append(
                    f"{cname} -> Ticket #{t['id']} [{t['status']}] {t['issue']}"
                )

            report = (
                "\n".join(lines)
                if lines
                else "No high-priority open tickets for premium customers."
            )
            content = (
                "[SupportAgent] Status of high-priority open tickets for premium customers:\n"
                + report
            )

        # Complex query: all active customers with open tickets
        elif scenario == "active_customers_with_open_tickets":
            active_customers = state.get("active_customers", [])
            ids = [c["id"] for c in active_customers]
            open_tickets = self.mcp.list_open_tickets_for_customers(
                customer_ids=ids, priority=None
            )
            state["open_tickets"] = open_tickets

            by_customer: Dict[int, Dict] = {c["id"]: c for c in active_customers}
            lines: List[str] = []
            for t in open_tickets:
                cust = by_customer.get(t["customer_id"])
                cname = cust["name"] if cust else f"Customer {t['customer_id']}"
                lines.append(
                    f"{cname} -> Ticket #{t['id']} [{t['priority']}] {t['issue']}"
                )

            body = "\n".join(lines) if lines else "No active customers with open tickets."
            content = "[SupportAgent] Active customers with open tickets:\n" + body

        # Escalation: refund / charged twice
        elif scenario == "refund_escalation":
            customer = state.get("customer")
            if customer:
                ticket = self.mcp.create_ticket(
                    customer_id=customer["id"],
                    issue="Customer reports double charge; immediate refund requested.",
                    priority="high",
                )
                state["created_ticket"] = ticket
                content = (
                    f"[SupportAgent] Marked as HIGH priority escalation. "
                    f"Refund ticket #{ticket['id']} created for customer {customer['name']}."
                )
            else:
                content = (
                    "[SupportAgent] Unable to escalate refund; missing customer_id. "
                    "Please provide your customer ID."
                )

        # Multi-intent: update email + show ticket history
        elif scenario == "update_email_and_history":
            customer = state.get("updated_customer") or state.get("customer")
            customer_id = state.get("customer_id")
            history = self.mcp.get_customer_history(customer_id)
            state["customer_history"] = history

            header = (
                f"Updated email for {customer['name']} to {customer['email']}."
                if customer
                else "Email update may have failed (customer not found)."
            )
            lines = [self._format_ticket_line(t) for t in history[:10]]
            tickets_text = "\n".join(lines) or "No previous tickets."

            content = (
                f"[SupportAgent] {header}\n\n"
                f"Here is your recent ticket history:\n{tickets_text}"
            )

        # Default / fall-back
        else:
            content = (
                "[SupportAgent] Generic support: I'm not sure which scenario applies. "
                "Please provide your customer ID and a brief description of the issue."
            )

        # ------------------------------------------------------
        # NEW: Let LLM rephrase / polish the final message
        # ------------------------------------------------------

        original_query = state.get("original_query", message.content)
        customer = state.get("customer")
        history = state.get("customer_history", [])

        context_lines = []

        if customer:
            context_lines.append(
                f"Customer #{customer['id']} - {customer['name']} "
                f"(status={customer['status']}, email={customer.get('email')})"
            )

        if history:
            context_lines.append("Recent tickets:")
            for t in history[:5]:
                context_lines.append(
                    f"- #{t['id']} [{t['priority']}] {t['issue']} (status={t['status']})"
                )

        context_block = "\n".join(context_lines) if context_lines else "No extra context."

        system_prompt = (
            "You are an experienced customer support agent. "
            "Rewrite the draft reply into a polished, professional, "
            "empathetic message. Do NOT invent new facts."
        )

        user_prompt = (
            f"User query:\n{original_query}\n\n"
            f"Context:\n{context_block}\n\n"
            f"Draft reply:\n{content}\n\n"
            "Please rewrite the draft into the final message."
        )

        final_content = self.llm(system_prompt, user_prompt)

        return A2AMessage(
            sender=self.name,
            receiver="router",
            role="agent",
            content=final_content,
            state=state,
        )
