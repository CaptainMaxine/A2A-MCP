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
