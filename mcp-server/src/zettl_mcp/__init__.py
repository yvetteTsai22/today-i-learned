"""Zettl MCP Server - Expose knowledge management API to AI agents."""

from zettl_mcp.server import mcp
from zettl_mcp.client import ZettlClient, ZettlAPIError

__version__ = "0.1.0"
__all__ = ["mcp", "ZettlClient", "ZettlAPIError"]
