"""
Scientific Skills MCP HTTP Server.

Implements the MCP protocol over HTTP so the Novaflow backend
can discover and retrieve scientific skill definitions.
"""

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .skill_loader import SkillRegistry

logger = logging.getLogger(__name__)

app = FastAPI(title="Scientific Skills MCP Server")
registry = SkillRegistry()


@app.on_event("startup")
async def startup():
    registry.load()
    logger.info(f"Scientific Skills MCP server ready with {registry.count} skills")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "tools_count": registry.count,
        "server": "scientific-skills-mcp",
        "version": "1.0.0",
    }


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP JSON-RPC style requests.

    Expected payload: {"id": "...", "method": "...", "params": {...}}
    """
    body: Dict[str, Any] = await request.json()
    message_id = body.get("id", "unknown")
    method = body.get("method", "")
    params = body.get("params", {})

    if method == "initialize":
        return JSONResponse({
            "id": message_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "scientific-skills-mcp",
                    "version": "1.0.0",
                },
            },
        })

    if method == "tools/list":
        tools = registry.list_tools()
        return JSONResponse({
            "id": message_id,
            "result": {"tools": tools},
        })

    if method == "tools/call":
        tool_name = params.get("name", "")
        content = registry.get_skill_content(tool_name)
        if content is None:
            return JSONResponse({
                "id": message_id,
                "error": f"Unknown tool: {tool_name}",
            })
        return JSONResponse({
            "id": message_id,
            "result": {
                "content": [
                    {"type": "text", "text": content}
                ],
            },
        })

    return JSONResponse({
        "id": message_id,
        "error": f"Unsupported method: {method}",
    })
