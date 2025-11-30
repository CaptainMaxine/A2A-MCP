# mcp_server/server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from . import db

app = FastAPI(title="Customer MCP Server")

# ----------------------------
# MCP tool metadata
# ----------------------------

TOOLS = {
    "get_customer": {
        "name": "get_customer",
        "description": "Get a single customer by ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"}
            },
            "required": ["customer_id"]
        },
    },
    "list_customers": {
        "name": "list_customers",
        "description": "List customers, optionally filtering by status",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "limit": {"type": "integer"}
            },
            "required": []
        },
    },
    "update_customer": {
        "name": "update_customer",
        "description": "Update customer fields",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "data": {"type": "object"}
            },
            "required": ["customer_id", "data"]
        },
    },
    "create_ticket": {
        "name": "create_ticket",
        "description": "Create a support ticket for a customer",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "issue": {"type": "string"},
                "priority": {"type": "string"}
            },
            "required": ["customer_id", "issue"]
        },
    },
    "get_customer_history": {
        "name": "get_customer_history",
        "description": "Get ticket history for a customer",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"}
            },
            "required": ["customer_id"]
        },
    },
}


# ----------------------------
# JSON-RPC request/response models
# ----------------------------

class ToolCallParams(BaseModel):
    name: str
    arguments: Dict[str, Any]


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    method: str
    params: ToolCallParams


class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


# ----------------------------
#  MCP endpoints
# ----------------------------

@app.get("/tools/list")
def list_tools():
    """
    MCP-style tool listing.
    """
    return {"tools": list(TOOLS.values())}


@app.post("/tools/call", response_model=JsonRpcResponse)
def call_tool(request: JsonRpcRequest):
    """
    JSON-RPC style MCP tool call.

    Request:
    {
      "jsonrpc": "2.0",
      "id": "1",
      "method": "tools/call",
      "params": {
        "name": "get_customer",
        "arguments": {"customer_id": 5}
      }
    }
    """
    if request.method != "tools/call":
        raise HTTPException(status_code=400, detail="Invalid method")

    tool_name = request.params.name
    args = request.params.arguments

    if tool_name not in TOOLS:
        return JsonRpcResponse(
            id=request.id,
            error={"message": f"Unknown tool: {tool_name}"},
        )

    try:
        if tool_name == "get_customer":
            cid = int(args["customer_id"])
            result = db.get_customer(cid)

        elif tool_name == "list_customers":
            status = args.get("status")
            limit = int(args.get("limit", 50))
            result = db.list_customers(status=status, limit=limit)

        elif tool_name == "update_customer":
            cid = int(args["customer_id"])
            data = args.get("data") or {}
            result = db.update_customer(cid, data)

        elif tool_name == "create_ticket":
            cid = int(args["customer_id"])
            issue = str(args["issue"])
            priority = str(args.get("priority", "medium"))
            result = db.create_ticket(cid, issue, priority)

        elif tool_name == "get_customer_history":
            cid = int(args["customer_id"])
            result = db.get_customer_history(cid)

        else:
            result = None

        return JsonRpcResponse(id=request.id, result={"data": result})

    except Exception as e:
        return JsonRpcResponse(
            id=request.id,
            error={"message": str(e)},
        )
