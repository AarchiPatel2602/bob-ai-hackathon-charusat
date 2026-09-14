from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_user
from backend.app.mcp.routewise_mcp import RouteWiseMCPServer, MCP_TOOLS

router = APIRouter(prefix="/mcp", tags=["mcp"])

class MCPToolCallRequest(BaseModel):
    tool_name: str
    arguments: Optional[Dict[str, Any]] = {}

@router.get("/tools")
def list_mcp_tools():
    """
    Expose list of registered Model Context Protocol (MCP) tools and JSON schemas.
    """
    return {
        "protocol_version": "2024-11-05",
        "server_name": "routewise-mcp-server",
        "tools": MCP_TOOLS
    }

@router.post("/call")
async def call_mcp_tool(
    req: MCPToolCallRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute a specified Model Context Protocol tool with authenticated session context.
    """
    server = RouteWiseMCPServer(db_session=db, user_id=current_user.id)
    result = await server.call_tool(req.tool_name, req.arguments or {})
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {
        "tool_name": req.tool_name,
        "content": [
            {
                "type": "text",
                "text": str(result)
            }
        ],
        "structured_data": result
    }
