# Zettl Runbook

Operational guide for running and troubleshooting Zettl.

---

## Deployment

### Docker Compose (standard local deployment)

```bash
cd zettl/zettl
cp .env.example .env     # First time only — fill in your API keys
make up-build            # Build images and start all services
```

To start with pre-built images (faster):
```bash
make up
```

To stop:
```bash
make down
```

### Safe Rebuild Workflow

Before rebuilding (in case you need to roll back):
```bash
make rebuild             # Equivalent to: make tag && make up-build
```

To roll back to a previous build:
```bash
make restore BRANCH=<branch-name>    # e.g. make restore BRANCH=main
```

### Service URLs

| Service | URL |
|---------|-----|
| Web UI | http://localhost:3000 |
| API | http://localhost:8000 |
| Interactive API docs (Swagger) | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

---

## Health Checks

### API health

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### Neo4j connectivity

```bash
curl http://localhost:7474
# Or open Neo4j Browser at http://localhost:7474 and run: MATCH (n) RETURN count(n)
```

### Stats endpoint (confirms Neo4j + Cognee are connected)

```bash
curl http://localhost:8000/stats
# Expected: {"notes": N, "topics": N, "connections": N, "this_week": N}
```

---

## Common Issues

### API starts but `/stats` returns 500

**Symptom:** Health check passes but `/stats` returns HTTP 500.

**Cause:** Neo4j is not yet reachable. Docker Compose starts services in parallel — Neo4j takes ~15–30 seconds to initialise.

**Fix:** Wait 30 seconds and retry. Check Neo4j container logs:
```bash
docker-compose logs neo4j
```

---

### LanceDB schema error on startup

**Symptom:** Log contains `Field not found in target schema` or `belongs_to_set`.

**Cause:** The Cognee version changed and the LanceDB schema is stale.

**Fix:** The API startup code (`main.py: _migrate_vector_store_if_needed`) auto-detects version changes and wipes the stale LanceDB directory. Restart the API container:
```bash
docker-compose restart api
```

Notes are stored in Neo4j and are unaffected.

---

### LLM calls fail with authentication errors

**Symptom:** Content generation or digest returns 500; logs show `AuthenticationError`.

**Cause:** API key is missing or incorrect in `.env`.

**Fix:**
```bash
# Check your .env
cat zettl/.env | grep -E "ANTHROPIC|OPENAI|VERTEX"

# Restart API after fixing .env
docker-compose restart api
```

---

### Cognee graph operations hang or time out

**Symptom:** `POST /notes` takes >30 seconds or times out. Logs show `cognee.add()` or `cognee.cognify()` hanging.

**Cause:** Cognee processes notes asynchronously using its own background LLM calls for entity extraction and linking. These calls go through the configured LLM provider.

**Fix:** Verify the LLM provider is reachable and the API key is valid. Check the Cognee internal logs:
```bash
docker-compose logs api | grep -i cognee
```

---

### `make e2e` fails with "connection refused"

**Symptom:** Playwright tests fail immediately with network errors.

**Cause:** E2E tests require the full stack to be running.

**Fix:** Start the stack before running E2E tests:
```bash
make up
make e2e
```

---

## Environment Variables

<!-- AUTO-GENERATED from zettl/.env.example -->
| Variable | Required | Description |
|----------|----------|-------------|
| `NEO4J_URI` | Yes | Neo4j bolt URI (e.g. `bolt://localhost:7687`) |
| `NEO4J_USER` | Yes | Neo4j username |
| `NEO4J_PASSWORD` | Yes | Neo4j password |
| `GRAPH_DATABASE_PROVIDER` | Yes | Cognee graph DB provider — use `neo4j` |
| `GRAPH_DATABASE_URL` | Yes | Cognee bolt URI (same as `NEO4J_URI`) |
| `GRAPH_DATABASE_USERNAME` | Yes | Cognee Neo4j username (same as `NEO4J_USER`) |
| `GRAPH_DATABASE_PASSWORD` | Yes | Cognee Neo4j password (same as `NEO4J_PASSWORD`) |
| `LLM_PROVIDER` | Yes | LLM provider: `anthropic`, `openai`, or `vertex_ai` |
| `LLM_MODEL` | Yes | Model name (e.g. `claude-sonnet-4-20250514`) |
| `ANTHROPIC_API_KEY` | If `LLM_PROVIDER=anthropic` | Anthropic API key |
| `OPENAI_API_KEY` | If `LLM_PROVIDER=openai` | OpenAI API key |
| `VERTEX_PROJECT` | If `LLM_PROVIDER=vertex_ai` | GCP project ID |
| `VERTEX_LOCATION` | If `LLM_PROVIDER=vertex_ai` | GCP region (e.g. `us-central1`) |
<!-- END AUTO-GENERATED -->

Docker Compose sets the `NEO4J_*` and `GRAPH_DATABASE_*` variables automatically for local dev — you only need to set the LLM keys in `.env`.

---

## Rollback Procedures

### Roll back to a previous Docker image

```bash
# List available tagged images
docker images | grep zettl

# Restore a specific branch tag to :latest
make restore BRANCH=<branch-name>

# Restart with the restored image
make up
```

### Roll back a database migration

Neo4j data lives in the `neo4j_data` Docker volume. To roll back:
1. Stop the stack: `make down`
2. Restore the volume from a backup (see below)
3. Restart: `make up`

To back up Neo4j data before a risky migration:
```bash
docker-compose exec neo4j neo4j-admin database dump neo4j --to-path=/backups
```
