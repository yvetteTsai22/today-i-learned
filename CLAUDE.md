# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zettl is a personal knowledge management system that ingests notes, stores them in a Neo4j graph database with Zettelkasten-style auto-linking via Cognee, and generates weekly content digests in multiple formats (blog, LinkedIn, X thread, video script).

## Commands

### Full Stack (Docker)
```bash
cd zettl
docker-compose up              # Start all services (Neo4j, API, UI)
docker-compose up --build      # Rebuild and start
```

### API Development (Python)
```bash
cd zettl/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest                         # All tests
pytest tests/test_notes_router.py  # Single file
pytest -k "test_create_note"   # Single test by name
```

### UI Development (Next.js)
```bash
cd zettl/ui
npm install
npm run dev                    # Dev server on :3000
npm run build                  # Production build
npm run lint                   # ESLint
```

## Architecture

```
zettl/
├── api/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py         # App entrypoint, Cognee config, CORS
│   │   ├── config.py       # Pydantic settings from .env
│   │   ├── routers/        # notes.py (POST /notes, /search), digest.py (POST /digest, /digest/content)
│   │   ├── services/
│   │   │   ├── cognee_service.py       # Knowledge graph ops: add_note, search
│   │   │   ├── llm_service.py          # Content generation via LiteLLM
│   │   │   └── digest_cache_service.py # Weekly digest caching in Neo4j
│   │   └── models/         # Pydantic models for notes, digest, content
│   └── tests/              # pytest + dependency overrides for mocking
├── mcp-server/             # MCP server (wraps API for Claude Code)
│   ├── src/zettl_mcp/
│   │   ├── server.py       # FastMCP tools: add_note, search_knowledge, generate_digest, generate_content
│   │   └── client.py       # Async HTTP client for Zettl API
│   └── tests/              # anyio + mock-based tests
├── ui/                     # Next.js frontend (App Router)
│   ├── app/
│   │   ├── page.tsx        # Home
│   │   └── capture/page.tsx # Note capture form
│   ├── components/         # shadcn/ui components + capture-form.tsx
│   └── lib/api.ts          # API client
└── docker-compose.yml      # Neo4j, API, UI orchestration
```

## Key Patterns

**Service Layer**: Routers depend on services via FastAPI `Depends()`. Tests mock services by overriding dependencies:
```python
app.dependency_overrides[get_cognee_service] = lambda: mock_cognee_service
```

**LLM Abstraction**: `LLMService` uses LiteLLM for provider flexibility (Anthropic, Vertex AI, OpenAI). Configure via `LLM_PROVIDER` and `LLM_MODEL` env vars.

**Knowledge Graph Flow**: Notes → `cognee.add()` → `cognee.cognify()` → Neo4j chunks with semantic relationships.

**Content Formats**: Each format has a dedicated generation method with specific structure templates (e.g., blog: Hook → Context → Insight → Examples → Takeaway).

## Git Conventions

- Do NOT append `Co-Authored-By` lines to commit messages
- Use emoji prefixes from `~/.gitmessage` (e.g., `✨feat:`, `🐛fix:`, `📝doc:`, `🔧build:`)

## Environment Configuration

Copy `zettl/.env.example` to `zettl/.env`. Key variables:
- `GRAPH_DATABASE_*`: Neo4j connection (auto-set by docker-compose for local)
- `LLM_PROVIDER`: `anthropic`, `vertex_ai`, or `openai`
- `LLM_MODEL`: Model name (e.g., `claude-sonnet-4-20250514`)
- Provider-specific API keys

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/notes` | POST | Add note to knowledge graph (invalidates digest cache) |
| `/search` | POST | Semantic search (`graph_completion` or `chunks`) |
| `/digest` | POST | Generate weekly summary + topic suggestions (cached per week; `?force_refresh=true` to bypass) |
| `/digest/content` | POST | Generate content drafts for a topic |
| `/health` | GET | Health check |

## Cross-Layer Changes

When modifying API endpoint signatures (new params, changed responses), update all consumers:

1. **API router** (`zettl/api/app/routers/`) — endpoint definition + tests
2. **MCP client** (`zettl/mcp-server/src/zettl_mcp/client.py`) — HTTP wrapper + tests
3. **MCP server** (`zettl/mcp-server/src/zettl_mcp/server.py`) — tool definition + tests
4. **UI API client** (`zettl/ui/lib/api.ts`) — fetch wrapper
5. **UI components** (`zettl/ui/components/`) — component calling the API function
