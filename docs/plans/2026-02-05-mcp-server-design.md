# Zettl MCP Server Design

## Overview

An MCP (Model Context Protocol) server that exposes the Zettl knowledge management API to AI agents. This enables Claude Code, Cursor, and other MCP-compatible clients to add notes, search knowledge, generate digests, and create content drafts.

## Architecture

### Approach

**HTTP client to existing API** — The MCP server acts as a thin client that calls FastAPI endpoints over HTTP. This:
- Keeps the API as single source of truth
- Works whether API runs locally or remotely
- Avoids tight coupling with internal services

### Project Structure

```
zettl/mcp-server/
├── pyproject.toml          # Package config, dependencies: mcp, httpx, pydantic
├── src/
│   └── zettl_mcp/
│       ├── __init__.py
│       ├── server.py       # MCP server setup, tool registration
│       ├── client.py       # HTTP client for Zettl API
│       └── tools.py        # Tool implementations
├── TODO.md                 # Roadmap for future phases
└── README.md               # Usage instructions
```

### Configuration

Single environment variable with sensible default:
- `ZETTL_API_URL` — defaults to `http://localhost:8000`

## MCP Tools

### Phase 1 Tools (Current Scope)

| Tool | Description | Parameters |
|------|-------------|------------|
| `add_note` | Add a note to the knowledge graph | `content` (required), `tags` (optional list), `source` (defaults to "agent") |
| `search_knowledge` | Semantic search across knowledge | `query` (required), `search_type` ("graph_completion" or "chunks") |
| `generate_digest` | Create weekly summary with topic suggestions | None — uses last 7 days automatically |
| `generate_content` | Generate content drafts for a topic | `topic`, `source_chunks`, `formats` (blog/linkedin/x_thread/video_script) |

### Tool Design Decisions

- **Return formatted strings** — LLMs work better with readable text than raw JSON
- **`source` defaults to "agent"** — Notes added via MCP are trackable
- **`formats` defaults to blog + linkedin** — Most common combo, keeps responses focused

## HTTP Client

### ZettlClient Class

```python
class ZettlClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("ZETTL_API_URL", "http://localhost:8000")
        self.http = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def add_note(self, content: str, tags: list[str] = None, source: str = "agent") -> dict
    async def search(self, query: str, search_type: str = "graph_completion") -> dict
    async def generate_digest(self) -> dict
    async def generate_content(self, topic: str, source_chunks: list[str], formats: list[str]) -> dict
    async def health_check(self) -> dict  # Ready for phase 2 resource
```

### Error Handling

| Scenario | Response |
|----------|----------|
| Network errors | "Cannot reach Zettl API at {url}" |
| 4xx errors | Pass through API validation messages |
| 5xx errors | "Zettl API error: {detail}" |
| Timeout | 30s default (content generation can be slow) |

### Why httpx?

- Native async support (MCP servers are async)
- Similar API to `requests` (familiar)
- Built-in timeout handling

## Installation & Usage

### Install

```bash
cd zettl/mcp-server
pip install -e .
```

### Run Standalone (Testing)

```bash
python -m zettl_mcp

# Or via MCP inspector
mcp dev src/zettl_mcp/server.py
```

### Claude Code Configuration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "zettl": {
      "command": "python",
      "args": ["-m", "zettl_mcp"],
      "env": {
        "ZETTL_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Extensibility

The MCP SDK makes adding resources and prompts straightforward:

### Adding Resources (Phase 2)

```python
@server.list_resources()
async def list_resources():
    return [Resource(uri="zettl://health", name="API Health")]

@server.read_resource()
async def read_resource(uri: str):
    if uri == "zettl://health":
        return await client.health_check()
```

### Adding Prompts (Phase 3)

```python
@server.list_prompts()
async def list_prompts():
    return [Prompt(name="explore-topic", arguments=[PromptArgument(name="topic")])]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict):
    if name == "explore-topic":
        return f"Search my knowledge graph for insights about {arguments['topic']}..."
```

## Roadmap

### Phase 1: Tools (Current)
- [x] add_note tool
- [x] search_knowledge tool
- [x] generate_digest tool
- [x] generate_content tool

### Phase 2: Resources
- [ ] zettl://health — API health status
- [ ] zettl://recent-notes — Last N notes added
- [ ] zettl://digest/latest — Most recent digest

### Phase 3: Prompts
- [ ] explore-topic — "What have I learned about {topic}?"
- [ ] weekly-review — "Summarize my week and suggest content"
- [ ] content-idea — "Generate content ideas from recent notes"

## Dependencies

```toml
[project]
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]
```
