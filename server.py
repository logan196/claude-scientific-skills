"""
Scientific Skills MCP Server

A lightweight HTTP server that exposes the claude-scientific-skills
collection as MCP tools. Each skill's SKILL.md is parsed for metadata
(name, description) and served via the MCP protocol over HTTP.
"""

import os
import pathlib
from typing import Any, Dict, List, Optional

import yaml
from fastapi import FastAPI

app = FastAPI(title="Scientific Skills MCP Server")

SKILLS_DIR = pathlib.Path(__file__).parent / "scientific-skills"


def _parse_frontmatter(text: str) -> Dict[str, Any]:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not text.startswith("---"):
        return {}
    end = text.index("---", 3)
    return yaml.safe_load(text[3:end]) or {}


def _load_skills() -> List[Dict[str, Any]]:
    """Scan scientific-skills/ and return a list of tool definitions."""
    tools: List[Dict[str, Any]] = []
    if not SKILLS_DIR.is_dir():
        return tools

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            content = skill_md.read_text(encoding="utf-8")
            meta = _parse_frontmatter(content)
            name = meta.get("name", skill_dir.name)
            description = meta.get("description", f"Scientific skill: {name}")
            tools.append(
                {
                    "name": name,
                    "description": description,
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The query or task to perform with this skill",
                            }
                        },
                    },
                }
            )
        except Exception:
            continue
    return tools


# Pre-load skills at startup
_TOOLS: List[Dict[str, Any]] = _load_skills()


def _read_skill_content(skill_name: str) -> Optional[str]:
    """Read full SKILL.md content for a given skill name."""
    # Try exact directory name first, then search by metadata name
    direct = SKILLS_DIR / skill_name / "SKILL.md"
    if direct.is_file():
        return direct.read_text(encoding="utf-8")

    # Fallback: search all skills for matching name in frontmatter
    for skill_dir in SKILLS_DIR.iterdir():
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        content = skill_md.read_text(encoding="utf-8")
        meta = _parse_frontmatter(content)
        if meta.get("name") == skill_name:
            return content
    return None


# ── HTTP Endpoints ────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok", "tools_count": len(_TOOLS)}


@app.post("/mcp")
async def mcp_endpoint(body: Dict[str, Any]):
    """Handle MCP protocol messages over HTTP."""
    msg_id = body.get("id", "")
    method = body.get("method", "")
    params = body.get("params", {})

    if method == "initialize":
        return {
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "scientific-skills",
                    "version": "1.0.0",
                },
                "capabilities": {
                    "tools": {"listChanged": False},
                },
            },
            "error": None,
        }

    if method == "tools/list":
        return {
            "id": msg_id,
            "result": {"tools": _TOOLS},
            "error": None,
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        content = _read_skill_content(tool_name)
        if content is None:
            return {
                "id": msg_id,
                "result": None,
                "error": f"Skill '{tool_name}' not found",
            }
        return {
            "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": content}],
                "isError": False,
            },
            "error": None,
        }

    if method == "resources/list":
        return {
            "id": msg_id,
            "result": {"resources": []},
            "error": None,
        }

    if method == "resources/read":
        return {
            "id": msg_id,
            "result": None,
            "error": "Resource not found",
        }

    return {
        "id": msg_id,
        "result": None,
        "error": f"Unknown method: {method}",
    }
