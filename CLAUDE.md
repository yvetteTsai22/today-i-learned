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
│   │   ├── routers/        # notes.py (CRUD /notes, /search), digest.py (/digest, /digest/content)
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
├── ui/                     # Next.js frontend (App Router, dashboard layout)
│   ├── app/
│   │   ├── page.tsx        # Dashboard home (stats, graph widget, activity feed)
│   │   ├── capture/page.tsx # Note capture form
│   │   ├── search/page.tsx  # Knowledge search
│   │   └── digest/page.tsx  # Weekly digest + content generation
│   ├── components/         # shadcn/ui + command palette, graph widget, note cards
│   └── lib/api.ts          # API client
├── extension/              # Browser extension (Chrome/Firefox) — planned
│   ├── manifest.json       # Manifest V3
│   ├── popup/              # Capture popup UI
│   └── background/         # Context menu + API calls
└── docker-compose.yml      # Neo4j, API, UI orchestration
```

### UI Architecture

Navigation uses a **command palette (Cmd+K)** instead of sidebar/tabs — minimal top strip with logo, search hint, and theme toggle. See `docs/plans/2026-02-23-ui-design-vision.md` for full design spec.

**Input channels:** Desktop web UI, browser extension (context menu + popup), iOS/Android shortcut (API call).

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

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/notes` | POST | Add note to knowledge graph (invalidates digest cache) | Implemented |
| `/notes/{id}` | PUT | Update existing note | Planned |
| `/notes/{id}` | DELETE | Delete note from graph | Planned |
| `/search` | POST | Semantic search (`graph_completion` or `chunks`) | Implemented |
| `/digest` | POST | Generate weekly summary + topic suggestions (cached per week; `?force_refresh=true` to bypass) | Implemented |
| `/digest/content` | POST | Generate content drafts for a topic | Implemented |
| `/graph` | GET | Return nodes + edges for graph visualization | Planned |
| `/stats` | GET | Return KPI data (note count, topics, connections) | Planned |
| `/activity` | GET | Return recent activity timeline | Planned |
| `/health` | GET | Health check | Implemented |

## Cross-Layer Changes

When modifying API endpoint signatures (new params, changed responses), update all consumers:

1. **API router** (`zettl/api/app/routers/`) — endpoint definition + tests
2. **MCP client** (`zettl/mcp-server/src/zettl_mcp/client.py`) — HTTP wrapper + tests
3. **MCP server** (`zettl/mcp-server/src/zettl_mcp/server.py`) — tool definition + tests
4. **UI API client** (`zettl/ui/lib/api.ts`) — fetch wrapper
5. **UI components** (`zettl/ui/components/`) — component calling the API function
6. **Browser extension** (`zettl/extension/`) — if the endpoint is used by the extension (notes, auth)
