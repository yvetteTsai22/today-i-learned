# Zettl MCP Server

MCP server that exposes the Zettl knowledge management API to AI agents.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Zettl backend running at `http://localhost:8000` (via `docker-compose up` in `zettl/`)

## Installation

```bash
cd zettl/mcp-server
uv sync              # Install dependencies
uv sync --dev        # Install with dev dependencies
```

## Usage

### Run standalone (testing)

```bash
cd zettl/mcp-server
uv run python -m zettl_mcp
```

### Claude Code configuration

The MCP server can be configured at three scopes:

| Scope | File | Use case |
|-------|------|----------|
| **Global (user state)** | `~/.claude.json` | Access from any repo (recommended) |
| **Global (dedicated)** | `~/.claude/.mcp.json` | Access from any repo, MCP-only config |
| **Project** | `<project-root>/.mcp.json` | Access only within a specific project |

#### Recommended: Add to `~/.claude.json`

Add an `mcpServers` key to your existing `~/.claude.json`:

```json
{
  "mcpServers": {
    "zettl": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/zettl/mcp-server", "run", "python", "-m", "zettl_mcp"],
      "env": {
        "ZETTL_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

#### Alternative: Dedicated `.mcp.json`

For a global or project-scoped `.mcp.json`, use the same structure (without `"type": "stdio"`):

```json
{
  "mcpServers": {
    "zettl": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/zettl/mcp-server", "run", "python", "-m", "zettl_mcp"],
      "env": {
        "ZETTL_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

**Important notes:**
- `--directory` must point to the **absolute path** of the `mcp-server/` directory so `uv` can find `pyproject.toml` and manage the virtualenv.
- `uv run` is required because the MCP server's dependencies (`mcp`, `httpx`, `pydantic`) are not installed in the system Python — `uv` handles virtualenv creation and dependency resolution automatically.
- The Zettl Docker stack (`docker-compose up`) **must be running** for the tools to work, since the MCP server calls the FastAPI backend over HTTP.
- **Restart Claude Code** after adding/changing the configuration.

## Tools

| Tool | Description |
|------|-------------|
| `add_note` | Add a note to your knowledge graph |
| `search_knowledge` | Semantic search across your knowledge |
| `generate_digest` | Create weekly summary with topic suggestions |
| `generate_content` | Generate content drafts for a topic |
