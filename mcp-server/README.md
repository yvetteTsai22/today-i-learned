# Zettl MCP Server

MCP server that exposes the Zettl knowledge management API to AI agents.

## Installation

```bash
cd zettl/mcp-server
pip install -e ".[dev]"
```

## Usage

### Run standalone (testing)

```bash
python -m zettl_mcp
```

### Claude Code configuration

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

## Tools

- `add_note` - Add a note to your knowledge graph
- `search_knowledge` - Semantic search across your knowledge
- `generate_digest` - Create weekly summary with topic suggestions
- `generate_content` - Generate content drafts for a topic
