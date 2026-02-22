# Digest Caching Design

## Problem

`POST /digest` regenerates the weekly digest from scratch on every call — searching Cognee for chunks and sending them through the LLM — even when nothing has changed. This wastes LLM tokens and adds latency for identical results.

## Solution

Cache the generated digest in Neo4j, keyed by calendar week. Invalidate automatically when new notes are added.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Time boundary | ISO calendar week (Mon–Sun) | Natural weekly rhythm; deterministic boundaries |
| Invalidation trigger | New note added via `POST /notes` | Simple, reliable — new knowledge should refresh the digest |
| Storage | Neo4j node (`CachedDigest`) | Leverages existing infrastructure; survives restarts |

## Data Model

`CachedDigest` Neo4j node:

| Property | Type | Purpose |
|----------|------|---------|
| `year` | int | ISO year |
| `week` | int | ISO week number (1–53) |
| `digest_id` | string | UUID for the digest |
| `summary` | string | Generated narrative summary |
| `topics_json` | string | JSON-serialized topic suggestions |
| `week_start` | string | ISO datetime of Monday |
| `week_end` | string | ISO datetime of Sunday |
| `created_at` | string | When the digest was generated |

Uniqueness: one node per `(year, week)`.

## Components

### 1. `DigestCacheService` (new)

`zettl/api/app/services/digest_cache_service.py`

Uses `neo4j` async driver directly (not Cognee) with three operations:

- `get_cached_digest(year, week) -> DigestResponse | None`
- `store_digest(year, week, digest_response) -> None`
- `invalidate_current_week() -> None`

Reads connection settings from existing `Settings` (`neo4j_uri`, `neo4j_user`, `neo4j_password`).

### 2. Digest Router Changes

`POST /digest` flow becomes:

1. Compute `(year, week)` from `datetime.now().isocalendar()`
2. Check cache via `get_cached_digest(year, week)`
3. Cache hit → return stored `DigestResponse`
4. Cache miss → generate via Cognee + LLM (existing flow)
5. Store result via `store_digest(year, week, response)`
6. Return response

Adds optional `force_refresh: bool = False` query param.

### 3. Notes Router Changes

`POST /notes` — after successful note creation, call `invalidate_current_week()` to delete the current week's cached digest.

### 4. Unchanged

- `/digest/content` — content generation stays uncached
- Cognee pipeline — no changes
- `DigestResponse` model — same shape, cache is transparent to consumers

## Testing

- Unit test: cache hit returns stored digest without calling LLM
- Unit test: cache miss generates fresh and stores
- Unit test: `POST /notes` invalidates current week's cache
- Unit test: `force_refresh=true` bypasses cache
