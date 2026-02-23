# Zettl

Personal knowledge management system. Captures notes from multiple sources, stores them in a Neo4j knowledge graph with Zettelkasten-style auto-linking via Cognee, and generates weekly content digests in multiple formats.

## How It Works

```mermaid
graph TB
    subgraph Capture["Capture Channels"]
        Web["Desktop Web UI"]
        Ext["Browser Extension"]
        Mobile["Mobile Shortcut"]
        MCP["MCP Server / AI Agents"]
    end

    subgraph Connectors["Connectors (planned)"]
        Notion["Notion Sync"]
        GDrive["Google Drive"]
    end

    Web -->|"REST API"| API
    Ext -->|"REST API"| API
    Mobile -->|"REST API"| API
    MCP -->|"REST API"| API
    Notion -.->|"periodic sync"| API
    GDrive -.->|"periodic sync"| API

    API["FastAPI Backend
    CogneeService + LLMService"]

    API -->|"async"| Neo["Neo4j + Cognee Knowledge Graph"]
    API -->|"LiteLLM"| LLM["LLM Providers
    Anthropic / OpenAI / Gemini"]

    Neo --- Links["supports / extends / contradicts"]

    classDef capture fill:#ede9fe,stroke:#a78bfa,color:#5b21b6,font-weight:bold
    classDef api fill:#e0f2fe,stroke:#7dd3fc,color:#0369a1,font-weight:bold
    classDef db fill:#d1fae5,stroke:#6ee7b7,color:#047857,font-weight:bold
    classDef cloud fill:#e0e7ff,stroke:#a5b4fc,color:#4338ca,font-weight:bold
    classDef links fill:#fef3c7,stroke:#fcd34d,color:#92400e

    classDef connector fill:#fef3c7,stroke:#fbbf24,color:#92400e,font-weight:bold,stroke-dasharray:5

    class Web,Ext,Mobile,MCP capture
    class Notion,GDrive connector
    class API api
    class Neo db
    class LLM cloud
    class Links links
```

## Features

- **Note Capture** — Add notes via web UI, browser extension, mobile shortcut, or MCP/AI agents
- **Connectors** (planned) — Periodic sync from Notion and Google Drive
- **Knowledge Graph** — Auto-links notes using Cognee semantic analysis, stored in Neo4j
- **Semantic Search** — Graph-completion and chunk-based search across your knowledge
- **Weekly Digests** — AI-generated summaries of your week's learnings with topic suggestions
- **Content Generation** — Draft content in 4 formats: blog, LinkedIn, X thread, video script
- **Graph Visualization** — Interactive knowledge graph widget on the dashboard
- **User Management** (planned) — Authentication, profiles, and multi-tenant data isolation

## UI

Keyboard-driven dashboard with a command palette (Cmd+K) as primary navigation. No sidebar — maximum content area.

| Page | Purpose |
|------|---------|
| Dashboard (`/`) | Knowledge graph widget, stats, quick actions, activity feed |
| Capture (`/capture`) | Note input with tags and source tracking |
| Search (`/search`) | Semantic and text search with expandable results |
| Digest (`/digest`) | Weekly digest with rendered markdown + Mermaid chart output |

## Quick Start

```bash
cd zettl
cp .env.example .env          # Configure API keys
docker-compose up --build      # Start Neo4j, API, UI
```

- UI: http://localhost:3000
- API: http://localhost:8000
- Neo4j Browser: http://localhost:7474

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, shadcn/ui, Tailwind CSS v4, cmdk |
| Backend | FastAPI, Cognee, LiteLLM |
| Database | Neo4j (knowledge graph) |
| LLM | Anthropic, OpenAI, or Vertex AI via LiteLLM |
| Extension | Chrome Manifest V3 (planned) |

## Docs

- [Knowledge Graph Design](docs/plans/2026-02-04-zettl-knowledge-graph-design.md)
- [Implementation Plan](docs/plans/2026-02-04-zettl-implementation.md)
- [Digest Caching Design](docs/plans/2026-02-18-digest-caching-design.md)
- [UI Design Vision](docs/plans/2026-02-23-ui-design-vision.md)
