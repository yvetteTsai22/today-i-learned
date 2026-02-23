# Zettl: Personal Knowledge Graph Service

**Date:** 2026-02-04
**Status:** Design Approved

## Overview

Zettl is a personal knowledge management system that:
- Ingests knowledge from Notion, a custom UI, and AI agents (on-demand)
- Stores it in a Neo4j graph database with Zettelkasten-style auto-linking via Cognee
- Runs weekly digests that summarize learnings and suggest content topics
- Generates draft content in multiple formats (blog, LinkedIn, X, video script)

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary use case | Content creation via scheduled digests | User priority |
| Knowledge graph engine | Cognee | Dense semantic graphs, multi-hop reasoning, 92.5% relevancy |
| Graph database | Neo4j | Industry standard, Neo4j Aura on GCP, great tooling |
| LLM | Agnostic (LiteLLM) | Flexibility for Vertex AI / Gemini on GCP |
| Notion integration | Periodic sync (daily/weekly) | Moderate usage, no real-time needed |
| Content output | Draft generation | User edits final content |
| UI approach | Simple capture first → full dashboard | Incremental delivery |
| Agent input | Manual trigger | User controls what gets saved |
| Deployment | Local Docker → GCP Cloud Run | Test locally, host on GCP |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        INPUTS                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐   │
│  │  Notion  │  │ Custom   │  │ AI Agents (Claude, GPT)  │   │
│  │  Sync    │  │ UI       │  │ via manual "save this"   │   │
│  └────┬─────┘  └────┬─────┘  └────────────┬─────────────┘   │
└───────┼─────────────┼─────────────────────┼─────────────────┘
        │             │                     │
        ▼             ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION API                             │
│              (FastAPI + Cognee ECL Pipeline)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                             │
│  ┌─────────────────┐         ┌─────────────────────────┐    │
│  │    Neo4j        │◄───────►│   Vector Store          │    │
│  │ (Knowledge Graph)│         │   (Qdrant/embedded)     │    │
│  └─────────────────┘         └─────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT SERVICES                           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │ Weekly Digest │  │ Search API   │  │ Content Gen     │    │
│  │ (Scheduler)   │  │              │  │ (LLM + Templates)│   │
│  └──────────────┘  └──────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Data Model

### Nodes

| Node Type | Description | Properties |
|-----------|-------------|------------|
| `Note` | Original input (can be large) | id, content, source, created_at, updated_at |
| `Chunk` | Semantic segment of a Note | id, content, sequence, embedding |
| `Topic` | Auto-extracted theme/concept | name, description |
| `Source` | Origin of knowledge | type, reference_id, name |
| `Digest` | Weekly summary output | week_start, week_end, summary |
| `Content` | Generated draft | type, body, status |

### Relationships

| Relationship | Properties | Description |
|--------------|------------|-------------|
| `(:Note)-[:HAS_CHUNK]->(:Chunk)` | sequence | Parent-child for chunked notes |
| `(:Chunk)-[:RELATES_TO]->(:Chunk)` | relation_type, confidence | Labeled semantic link |
| `(:Chunk)-[:TAGGED_WITH]->(:Topic)` | weight | Chunk-level topic assignment |
| `(:Note)-[:FROM_SOURCE]->(:Source)` | | Provenance |
| `(:Digest)-[:COVERS]->(:Chunk)` | | Digest coverage |
| `(:Content)-[:DERIVED_FROM]->(:Chunk)` | | Content genealogy |

### Relationship Types

- `supports` — evidence/backing for an idea
- `contradicts` — opposing viewpoint
- `extends` — builds upon concept
- `examples` — illustrative instance
- `similar` — semantically close but distinct
- `causes` / `caused_by` — causal chain
- `part_of` / `contains` — hierarchical

## API Endpoints

### Ingestion

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/notes` | POST | Add new note (UI/agents) |
| `/notes` | GET | List notes (with filters) |
| `/notes/{id}` | GET | Get note with chunks & relations |
| `/sync/notion` | POST | Trigger Notion sync manually |
| `/search` | POST | Semantic search across knowledge |

### Output

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/digest` | POST | Trigger digest manually |
| `/digest` | GET | List past digests |
| `/digest/{id}` | GET | Get digest with generated content |
| `/content/{id}/regenerate` | POST | Regenerate a draft with tweaks |

## Weekly Digest Workflow

1. **Gather** - Query Neo4j for chunks created/updated in last 7 days
2. **Analyze** - Cluster by topic, identify emerging themes, find high-connectivity nodes
3. **Summarize** - LLM generates narrative summary + 3-5 content topic suggestions
4. **Generate Drafts** - For each topic: blog, LinkedIn, X thread, video script
5. **Deliver** - Store in Neo4j, send notification, display in UI

## Content Templates

| Format | Structure | Length |
|--------|-----------|--------|
| Blog | Hook → Context → Insight → Examples → Takeaway | 800-1200 words |
| LinkedIn | Hook line → Story → Lesson → CTA | 200-300 words |
| X Thread | Opener → 3-5 insights → Summary + CTA | 3-5 tweets |
| Video Script | Hook (5s) → Problem (15s) → Insight (40s) → CTA (10s) | 60-90 seconds |

## Tech Stack

### Backend
- **Language:** Python
- **Framework:** FastAPI
- **Knowledge Graph Engine:** Cognee
- **Graph Database:** Neo4j
- **Vector Store:** Qdrant (or Cognee built-in)
- **LLM Abstraction:** LiteLLM (supports Vertex AI, Anthropic, OpenAI, Ollama)

### Frontend
- **Framework:** Next.js
- **UI Components:** shadcn/ui
- **Styling:** Tailwind CSS
- **Typography:** Plus Jakarta Sans

### Design Tokens
- Primary: #0D9488 (teal-600)
- Secondary: #14B8A6 (teal-500)
- CTA/Action: #F97316 (orange-500)
- Background: #F0FDFA (teal-50)
- Text: #134E4A (teal-900)

### Infrastructure
- **Local:** Docker Compose
- **Production:** GCP Cloud Run
- **Graph DB (prod):** Neo4j Aura (GCP Marketplace)
- **LLM (prod):** Vertex AI (Gemini)
- **Scheduler:** Cloud Scheduler
- **Secrets:** Secret Manager
- **CI/CD:** Cloud Build

## Project Structure

```
zettl/
├── docker-compose.yml
├── README.md
├── api/                        # FastAPI backend
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   └── db/
│   └── tests/
├── ui/                         # Next.js frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── app/
│   └── components/
└── infra/                      # Terraform for GCP
    ├── main.tf
    ├── variables.tf
    └── cloud-run.tf
```

## MVP Scope (Phase 1)

### Included
- POST /notes endpoint
- Cognee auto-linking pipeline
- POST /digest (manual trigger)
- Content generation (4 formats)
- Simple capture UI
- Local Docker setup
- Neo4j + Cognee integration

### Excluded from MVP (Later Phases)
- Notion sync
- ~~Real-time graph visualization~~ → Planned as dashboard widget (see [UI Design Vision](2026-02-23-ui-design-vision.md))
- Scheduled digests (cron)
- ~~Content editing in UI~~ → Planned as note edit/delete (see [UI Design Vision](2026-02-23-ui-design-vision.md))
- ~~Full dashboard~~ → Planned with command palette navigation (see [UI Design Vision](2026-02-23-ui-design-vision.md))
- GCP Terraform
- ~~Agent API authentication~~ → Planned as API key auth for browser extension + mobile shortcut
- Browser extension (Chrome/Firefox) — new
- Mobile capture shortcut (iOS/Android) — new
- User management (auth, profiles, multi-tenant) — new

## MVP User Flow

1. Run `docker-compose up`
2. Open http://localhost:3000/capture
3. Type a note → click Save
4. Cognee processes → auto-links in Neo4j
5. Repeat for a week
6. Call POST /digest via curl
7. View generated content drafts
8. Copy/edit drafts for publishing

## References

- [Cognee GitHub](https://github.com/topoteretes/cognee)
- [Neo4j Aura](https://neo4j.com/cloud/aura/)
- [LiteLLM](https://github.com/BerriAI/litellm)
- [shadcn/ui](https://ui.shadcn.com/)
- [Zettelkasten Method](https://zettelkasten.de/introduction/)
