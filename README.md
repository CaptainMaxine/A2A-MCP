# A2A-MCP
# Multi-Agent Customer Service System (A2A + MCP-style)

This project implements a **multi-agent customer service system** that uses:

- **RouterAgent** (orchestrator)
- **CustomerDataAgent** (MCP-backed customer DB specialist)
- **SupportAgent** (support + escalation specialist)
- A thin **MCPClient** wrapper around `mcp_server.tools`

Database and sample data are created by your course-provided
`database_setup.py` (renamed here as `mcp_server/database_setup.py`).

---

## 1. Setup

```bash
git clone <this-repo>
cd multi-agent-cs

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt   # currently stdlib only, but keep file for consistency

2. Initialize Database
python -m mcp_server.server


This will:

Create support.db if missing

Create tables & triggers

Insert sample customers & tickets

3. Run End-to-End Demo (Python script)
python -m agents.coordinator


You will see:

A2A logs for each step (Router → DataAgent → Router → SupportAgent …)

Final response for each scenario

4. Notebook Demo

Open notebook/multi_agent_demo.py and copy the content into a Jupyter / Colab
notebook as separate cells (or convert via jupytext). Run all cells to:

Initialize DB

Construct the agents + coordinator

Execute all required test scenarios (simple query, coordinated query, complex query, escalation, multi-intent, plus the three explicit scenarios).

The printed logs satisfy the assignment requirement:

"Add explicit logging to show agent-to-agent communication"

5. MCP Integration

In this reference implementation, agents/mcp_client.py calls
mcp_server.tools in-process.

In your course environment, replace MCPClient methods with real MCP calls:

class MCPClient:
    def get_customer(self, customer_id: int):
        # TODO: call MCP server tool get_customer
        ...


No other file needs to change.

6. Conclusion Template (you can adapt)

In this assignment I learned how to separate concerns between a router
agent, data specialist, and support specialist, and how to use a
MCP-style tool layer to isolate database logic from agent reasoning.
Designing the A2A coordination forced me to model scenarios such as
task allocation, negotiation, and multi-step decomposition explicitly
in the shared state passed between agents.

The main challenges were debugging multi-agent loops and ensuring that
information was not lost between transfers. I addressed this by adding
a structured A2AMessage object, centralized logging in the
coordinator, and simple scenario tags in the shared state so that each
agent could make decisions deterministically.
