"""Entry point for running the MCP server: python -m mcp_server"""

import argparse
import logging
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

parser = argparse.ArgumentParser(description="Scientific Skills MCP Server")
parser.add_argument("--host", default="0.0.0.0", help="Bind host")
parser.add_argument("--port", type=int, default=8100, help="Bind port")

args = parser.parse_args()

uvicorn.run("mcp_server.server:app", host=args.host, port=args.port)
