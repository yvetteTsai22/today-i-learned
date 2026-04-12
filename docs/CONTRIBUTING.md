# Contributing to Zettl

## Prerequisites

- Python 3.11+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker + Docker Compose (for full-stack local dev)
- Neo4j (local or [Aura free tier](https://neo4j.com/cloud/platform/aura-graph-database/))

## Development Setup

### With Docker (recommended)

```bash
git clone https://github.com/your-username/zettl.git
cd zettl/zettl
cp .env.example .env        # Fill in your API keys
make up-build               # Build images and start all services
```

Services start at:
- Web UI: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

### Without Docker

**API:**
```bash
cd zettl/api
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

**UI:**
```bash
cd zettl/ui
npm install
npm run dev        # http://localhost:3000
```

**MCP server:**
```bash
cd zettl/mcp-server
uv pip install -e ".[dev]"
```

## Available Commands

<!-- AUTO-GENERATED from zettl/Makefile -->
| Command | Description |
|---------|-------------|
| `make up` | Start stack with existing images (no rebuild) |
| `make up-build` | Rebuild all images and start stack |
| `make down` | Stop and remove containers |
| `make tag` | Tag current images with branch name |
| `make restore BRANCH=<name>` | Restore images from a branch tag to `:latest` |
| `make test` | Run API unit + integration tests |
| `make e2e` | Run E2E tests against a running stack |
| `make rebuild` | Safe rebuild: tag current branch, then rebuild |
<!-- END AUTO-GENERATED -->

## Testing

The test suite must pass before a PR is merged.

### API tests (Python)

```bash
cd zettl/api
uv run pytest                            # All tests (61 tests)
uv run pytest tests/test_notes_router.py # Single file
uv run pytest --cov=app                  # With coverage report
uv run pytest -k "test_create_note"      # Single test by name
```

### MCP server tests (Python)

```bash
cd zettl/mcp-server
uv run pytest                            # All tests (17 tests)
```

### UI

```bash
cd zettl/ui
npm run build     # TypeScript + Next.js build check
npm run lint      # ESLint
```

### E2E tests (requires running stack)

```bash
cd zettl
make up
make e2e
```

## Code Style

### Python
- Follows PEP 8 — format with **black**, lint with **ruff**
- Type annotations required on all function signatures
- Immutable data patterns preferred (avoid in-place mutation)
- Functions stay under 50 lines; files stay under 800 lines

### TypeScript / React
- TypeScript strict mode — no `any` in application code
- Named `interface` for props and object shapes
- No `console.log` in production code
- shadcn/ui component patterns for new UI elements

## Project Structure Conventions

**Service injection:** Routers depend on services via FastAPI `Depends()`. Tests mock by overriding:
```python
app.dependency_overrides[get_cognee_service] = lambda: mock_service
```

**LLM provider switching:** Controlled by `LLM_PROVIDER` + `LLM_MODEL` env vars — no code changes needed to switch providers.

**Adding a content format:** Drop a `.md` skill file in `zettl/api/app/services/content_agent/skills/` and add the enum value to `ContentFormat` in `zettl/api/app/models/content.py`. No other Python changes needed.

**Cross-layer changes:** When modifying an API endpoint signature, update all consumers:
1. API router (`zettl/api/app/routers/`)
2. MCP client (`zettl/mcp-server/src/zettl_mcp/client.py`)
3. MCP server (`zettl/mcp-server/src/zettl_mcp/server.py`)
4. UI API client (`zettl/ui/lib/api.ts`)
5. UI components that call that function

## PR Checklist

- [ ] `uv run pytest` passes in `zettl/api` and `zettl/mcp-server`
- [ ] `npm run build` passes in `zettl/ui`
- [ ] New behaviour is covered by tests
- [ ] No hardcoded secrets or API keys
- [ ] PR description explains the **why**, not just the what

## Submitting a PR

- **Bug reports:** Open an issue with reproduction steps before a fix PR.
- **Features:** Open an issue to discuss before opening a PR.
- **Content skills:** Adding new `.md` skill files in `skills/` is the easiest contribution — no Python required.
- **Keep PRs focused:** One concern per PR.
