# Zettl MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a working MVP where you can POST notes, have them auto-linked via Cognee into Neo4j, trigger a digest, and receive generated content drafts.

**Architecture:** FastAPI backend with Cognee for knowledge graph processing, Neo4j for storage, LiteLLM for LLM abstraction. Next.js + shadcn/ui frontend for simple note capture. All containerized with Docker Compose.

**Tech Stack:** Python 3.11+, FastAPI, Cognee, Neo4j, LiteLLM, Next.js 14, shadcn/ui, Tailwind CSS, Docker Compose

---

## Phase 1: Project Setup & Infrastructure

### Task 1: Initialize Project Structure

**Files:**
- Create: `zettl/docker-compose.yml`
- Create: `zettl/api/pyproject.toml`
- Create: `zettl/api/Dockerfile`
- Create: `zettl/.env.example`
- Create: `zettl/.gitignore`

**Step 1: Create project directories**

```bash
mkdir -p zettl/api/app/{models,routers,services,db}
mkdir -p zettl/api/tests
mkdir -p zettl/ui
mkdir -p zettl/infra
```

**Step 2: Create pyproject.toml**

```toml
# zettl/api/pyproject.toml
[project]
name = "zettl-api"
version = "0.1.0"
description = "Personal knowledge graph service"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "cognee[neo4j]>=0.1.26",
    "litellm[google]>=1.30.0",  # [google] extra required for Vertex AI
    "anthropic>=0.18.0",
    "pydantic>=2.6.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Step 3: Create docker-compose.yml**

```yaml
# zettl/docker-compose.yml
services:
  neo4j:
    image: neo4j:5.17-community
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/zettlpassword123
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.*
    volumes:
      - neo4j_data:/data
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:7474"]
      interval: 10s
      timeout: 5s
      retries: 10

  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=zettlpassword123
      - GRAPH_DATABASE_PROVIDER=neo4j
      - GRAPH_DATABASE_URL=bolt://neo4j:7687
      - GRAPH_DATABASE_USERNAME=neo4j
      - GRAPH_DATABASE_PASSWORD=zettlpassword123
      # For Vertex AI authentication in Docker
      - GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json
      - GOOGLE_CLOUD_PROJECT=your-gcp-project
    env_file:
      - .env
    depends_on:
      neo4j:
        condition: service_healthy
    volumes:
      - ./api:/app
      - cognee_data:/app/cognee_data
      # Mount gcloud credentials for Vertex AI (run: gcloud auth application-default login)
      - ~/.config/gcloud:/root/.config/gcloud:ro

volumes:
  neo4j_data:
  cognee_data:
```

**Step 4: Create Dockerfile for API**

```dockerfile
# zettl/api/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Step 5: Create .env.example**

```bash
# zettl/.env.example
# Neo4j (set automatically by docker-compose for local dev)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=zettlpassword123

# Cognee Graph DB Config
GRAPH_DATABASE_PROVIDER=neo4j
GRAPH_DATABASE_URL=bolt://localhost:7687
GRAPH_DATABASE_USERNAME=neo4j
GRAPH_DATABASE_PASSWORD=zettlpassword123
# Disable multi-user access control for local dev (avoids handler mismatch)
ENABLE_BACKEND_ACCESS_CONTROL=false

# LLM Configuration (choose one)

# Option 1: Vertex AI via custom provider (recommended for GCP)
# Requires: pip install 'litellm[google]' or google-cloud-aiplatform
LLM_PROVIDER=custom
LLM_MODEL=vertex_ai/gemini-2.0-flash
LLM_API_KEY=gcp-credentials-used
VERTEX_PROJECT=your-gcp-project
VERTEX_LOCATION=us-central1
GOOGLE_CLOUD_PROJECT=your-gcp-project

# Embeddings - Vertex AI via custom provider
EMBEDDING_PROVIDER=custom
EMBEDDING_MODEL=vertex_ai/text-embedding-005
EMBEDDING_API_KEY=gcp-credentials-used
EMBEDDING_DIMENSIONS=768

# Option 2: Anthropic (uncomment to use)
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-sonnet-4-20250514
# ANTHROPIC_API_KEY=your-key-here

# Option 3: OpenAI (uncomment to use)
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o
# OPENAI_API_KEY=your-key-here
```

**Step 6: Create .gitignore**

```gitignore
# zettl/.gitignore
__pycache__/
*.py[cod]
.env
.venv/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
node_modules/
.next/
```

**Step 7: Commit**

```bash
cd zettl
git init
git add .
git commit -m "chore: initialize project structure with Docker Compose"
```

---

### Task 2: Create FastAPI Application Skeleton

**Files:**
- Create: `zettl/api/app/__init__.py`
- Create: `zettl/api/app/main.py`
- Create: `zettl/api/app/config.py`

**Step 1: Create empty __init__.py**

```python
# zettl/api/app/__init__.py
```

**Step 2: Create config.py with Pydantic Settings**

```python
# zettl/api/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "zettlpassword123"

    # Cognee Graph DB
    graph_database_provider: str = "neo4j"
    graph_database_url: str = "bolt://localhost:7687"
    graph_database_username: str = "neo4j"
    graph_database_password: str = "zettlpassword123"

    # LLM
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    vertex_project: str | None = None
    vertex_location: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 3: Create main.py with health endpoint**

```python
# zettl/api/app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize Cognee config
    settings = get_settings()

    import cognee
    cognee.config.set_graph_db_config({
        "graph_database_provider": settings.graph_database_provider,
        "graph_database_url": settings.graph_database_url,
        "graph_database_username": settings.graph_database_username,
        "graph_database_password": settings.graph_database_password,
    })

    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Zettl API",
    description="Personal knowledge graph service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 4: Verify the API starts**

```bash
cd zettl
docker-compose up --build
```

Expected: API running at http://localhost:8000, Neo4j at http://localhost:7474

**Step 5: Test health endpoint**

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"healthy"}`

**Step 6: Commit**

```bash
git add api/app/
git commit -m "feat: add FastAPI skeleton with Cognee configuration"
```

---

## Phase 2: Notes Ingestion Pipeline

### Task 3: Create Note Models

**Files:**
- Create: `zettl/api/app/models/__init__.py`
- Create: `zettl/api/app/models/note.py`
- Test: `zettl/api/tests/test_models.py`

**Step 1: Write the failing test**

```python
# zettl/api/tests/test_models.py
import pytest
from datetime import datetime
from app.models.note import NoteCreate, NoteResponse, NoteSource


def test_note_create_with_defaults():
    note = NoteCreate(content="Test content")
    assert note.content == "Test content"
    assert note.source == NoteSource.MANUAL
    assert note.tags == []


def test_note_create_with_all_fields():
    note = NoteCreate(
        content="Test content",
        source=NoteSource.AGENT,
        tags=["test", "example"],
        source_reference="claude-code-session-123"
    )
    assert note.source == NoteSource.AGENT
    assert "test" in note.tags


def test_note_response_has_id_and_timestamps():
    response = NoteResponse(
        id="note-123",
        content="Test",
        source=NoteSource.MANUAL,
        tags=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert response.id == "note-123"
    assert response.created_at is not None
```

**Step 2: Run test to verify it fails**

```bash
cd zettl/api
pip install -e ".[dev]"
pytest tests/test_models.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create models/__init__.py**

```python
# zettl/api/app/models/__init__.py
from app.models.note import NoteCreate, NoteResponse, NoteSource

__all__ = ["NoteCreate", "NoteResponse", "NoteSource"]
```

**Step 4: Create note.py with Pydantic models**

```python
# zettl/api/app/models/note.py
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class NoteSource(str, Enum):
    MANUAL = "manual"
    NOTION = "notion"
    AGENT = "agent"
    UI = "ui"


class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Note content")
    source: NoteSource = Field(default=NoteSource.MANUAL, description="Origin of the note")
    tags: list[str] = Field(default_factory=list, description="Optional tags")
    source_reference: str | None = Field(default=None, description="External reference ID")


class NoteResponse(BaseModel):
    id: str
    content: str
    source: NoteSource
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_models.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add api/app/models/ api/tests/
git commit -m "feat: add Note Pydantic models with validation"
```

---

### Task 4: Create Cognee Service

**Files:**
- Create: `zettl/api/app/services/__init__.py`
- Create: `zettl/api/app/services/cognee_service.py`
- Test: `zettl/api/tests/test_cognee_service.py`

**Step 1: Write the failing test**

```python
# zettl/api/tests/test_cognee_service.py
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_add_note_calls_cognee_add():
    with patch("app.services.cognee_service.cognee") as mock_cognee:
        mock_cognee.add = AsyncMock()
        mock_cognee.cognify = AsyncMock()

        from app.services.cognee_service import CogneeService
        service = CogneeService()

        await service.add_note("Test content", dataset_name="test")

        mock_cognee.add.assert_called_once()
        mock_cognee.cognify.assert_called_once()


@pytest.mark.asyncio
async def test_search_returns_results():
    with patch("app.services.cognee_service.cognee") as mock_cognee:
        mock_cognee.search = AsyncMock(return_value=["result1", "result2"])

        from app.services.cognee_service import CogneeService
        service = CogneeService()

        results = await service.search("query")

        assert len(results) == 2
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_cognee_service.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create services/__init__.py**

```python
# zettl/api/app/services/__init__.py
from app.services.cognee_service import CogneeService

__all__ = ["CogneeService"]
```

**Step 4: Create cognee_service.py**

```python
# zettl/api/app/services/cognee_service.py
import cognee
from cognee.modules.search.types import SearchType
from datetime import datetime
import uuid


class CogneeService:
    """Service for interacting with Cognee knowledge graph."""

    DEFAULT_DATASET = "zettl_notes"

    async def add_note(
        self,
        content: str,
        dataset_name: str | None = None,
        metadata: dict | None = None
    ) -> str:
        """
        Add a note to Cognee and process it into the knowledge graph.

        Returns the note ID.
        """
        dataset = dataset_name or self.DEFAULT_DATASET
        note_id = str(uuid.uuid4())

        # Prepare content with metadata
        enriched_content = content
        if metadata:
            meta_str = " | ".join(f"{k}: {v}" for k, v in metadata.items())
            enriched_content = f"[{meta_str}]\n{content}"

        # Add to Cognee
        await cognee.add([enriched_content], dataset_name=dataset)

        # Process into knowledge graph
        await cognee.cognify([dataset])

        return note_id

    async def search(
        self,
        query: str,
        dataset_name: str | None = None,
        search_type: str = "graph_completion"
    ) -> list[str]:
        """
        Search the knowledge graph.

        search_type: "graph_completion" | "chunks"
        """
        dataset = dataset_name or self.DEFAULT_DATASET

        if search_type == "chunks":
            results = await cognee.search(
                query_type=SearchType.CHUNKS,
                query_text=query,
                datasets=[dataset]
            )
        else:
            results = await cognee.search(
                query_type=SearchType.GRAPH_COMPLETION,
                query_text=query
            )

        return [str(r) for r in results]

    async def get_notes_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
        dataset_name: str | None = None
    ) -> list[str]:
        """
        Get notes created within a date range.
        Used for digest generation.
        """
        # For MVP, we'll search by date terms
        # In production, store metadata in a separate DB
        query = f"notes from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        return await self.search(query, dataset_name)
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_cognee_service.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add api/app/services/
git commit -m "feat: add CogneeService for knowledge graph operations"
```

---

### Task 5: Create Notes Router

**Files:**
- Create: `zettl/api/app/routers/__init__.py`
- Create: `zettl/api/app/routers/notes.py`
- Modify: `zettl/api/app/main.py`
- Test: `zettl/api/tests/test_notes_router.py`

**Step 1: Write the failing test**

```python
# zettl/api/tests/test_notes_router.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


@pytest.fixture
def client():
    with patch("app.routers.notes.CogneeService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.add_note = AsyncMock(return_value="note-123")
        mock_instance.search = AsyncMock(return_value=["result1"])

        from app.main import app
        with TestClient(app) as c:
            yield c


def test_create_note_returns_201(client):
    response = client.post(
        "/notes",
        json={"content": "Test note content"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["content"] == "Test note content"


def test_create_note_with_tags(client):
    response = client.post(
        "/notes",
        json={
            "content": "Tagged note",
            "tags": ["test", "example"],
            "source": "agent"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "test" in data["tags"]


def test_search_notes(client):
    response = client.post(
        "/search",
        json={"query": "test query"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_notes_router.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create routers/__init__.py**

```python
# zettl/api/app/routers/__init__.py
from app.routers.notes import router as notes_router

__all__ = ["notes_router"]
```

**Step 4: Create notes.py router**

```python
# zettl/api/app/routers/notes.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.note import NoteCreate, NoteResponse, NoteSource
from app.services.cognee_service import CogneeService

router = APIRouter()
cognee_service = CogneeService()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    search_type: str = Field(default="graph_completion")


class SearchResponse(BaseModel):
    results: list[str]
    query: str


@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(note: NoteCreate):
    """
    Create a new note and process it into the knowledge graph.
    """
    try:
        metadata = {
            "source": note.source.value,
            "tags": ",".join(note.tags) if note.tags else "",
            "created_at": datetime.now().isoformat(),
        }
        if note.source_reference:
            metadata["source_reference"] = note.source_reference

        note_id = await cognee_service.add_note(
            content=note.content,
            metadata=metadata
        )

        now = datetime.now()
        return NoteResponse(
            id=note_id,
            content=note.content,
            source=note.source,
            tags=note.tags,
            created_at=now,
            updated_at=now,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create note: {str(e)}"
        )


@router.post("/search", response_model=SearchResponse)
async def search_notes(request: SearchRequest):
    """
    Search the knowledge graph.
    """
    try:
        results = await cognee_service.search(
            query=request.query,
            search_type=request.search_type
        )
        return SearchResponse(results=results, query=request.query)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
```

**Step 5: Update main.py to include router**

```python
# zettl/api/app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers.notes import router as notes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize Cognee config
    settings = get_settings()

    import cognee
    cognee.config.set_graph_db_config({
        "graph_database_provider": settings.graph_database_provider,
        "graph_database_url": settings.graph_database_url,
        "graph_database_username": settings.graph_database_username,
        "graph_database_password": settings.graph_database_password,
    })

    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Zettl API",
    description="Personal knowledge graph service",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(notes_router, tags=["notes"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/test_notes_router.py -v
```

Expected: PASS

**Step 7: Commit**

```bash
git add api/app/routers/ api/app/main.py api/tests/
git commit -m "feat: add /notes and /search endpoints"
```

---

## Phase 3: LLM Service & Content Generation

### Task 6: Create LLM Service with LiteLLM

**Files:**
- Create: `zettl/api/app/services/llm_service.py`
- Test: `zettl/api/tests/test_llm_service.py`

**Step 1: Write the failing test**

```python
# zettl/api/tests/test_llm_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_generate_content_returns_string():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Generated text"))]

    with patch("app.services.llm_service.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = mock_response

        from app.services.llm_service import LLMService
        service = LLMService()

        result = await service.generate("Write a haiku")

        assert result == "Generated text"
        mock_completion.assert_called_once()


@pytest.mark.asyncio
async def test_generate_blog_draft():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="# Blog Post\n\nContent here"))]

    with patch("app.services.llm_service.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = mock_response

        from app.services.llm_service import LLMService
        service = LLMService()

        result = await service.generate_blog_draft(
            topic="Graph Databases",
            source_chunks=["Neo4j stores data in nodes", "Cypher is the query language"]
        )

        assert "Blog Post" in result
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_llm_service.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create llm_service.py**

```python
# zettl/api/app/services/llm_service.py
from litellm import acompletion
from app.config import get_settings


class LLMService:
    """Service for LLM-powered content generation using LiteLLM."""

    def __init__(self):
        self.settings = get_settings()
        self._configure_provider()

    def _configure_provider(self):
        """Configure LiteLLM based on settings."""
        import litellm

        if self.settings.llm_provider == "vertex_ai":
            litellm.vertex_project = self.settings.vertex_project
            litellm.vertex_location = self.settings.vertex_location
            self.model = f"vertex_ai/{self.settings.llm_model}"
        elif self.settings.llm_provider == "anthropic":
            self.model = f"anthropic/{self.settings.llm_model}"
        elif self.settings.llm_provider == "openai":
            self.model = self.settings.llm_model
        else:
            self.model = self.settings.llm_model

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text from a prompt."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await acompletion(
            model=self.model,
            messages=messages,
            max_tokens=2000,
        )

        return response.choices[0].message.content

    async def generate_blog_draft(
        self,
        topic: str,
        source_chunks: list[str],
        word_count: int = 1000
    ) -> str:
        """Generate a blog post draft from knowledge chunks."""
        sources = "\n".join(f"- {chunk}" for chunk in source_chunks)

        prompt = f"""Write a blog post about: {topic}

Use these knowledge sources as reference:
{sources}

Requirements:
- Length: approximately {word_count} words
- Structure: Hook → Context → Insight → Examples → Takeaway
- Tone: Educational, personal voice
- Include specific examples from the sources
- End with a clear takeaway or call to action

Write the blog post:"""

        system_prompt = "You are a skilled technical writer who creates engaging, educational blog content."

        return await self.generate(prompt, system_prompt)

    async def generate_linkedin_post(
        self,
        topic: str,
        source_chunks: list[str]
    ) -> str:
        """Generate a LinkedIn post from knowledge chunks."""
        sources = "\n".join(f"- {chunk}" for chunk in source_chunks)

        prompt = f"""Write a LinkedIn post about: {topic}

Use these knowledge sources:
{sources}

Requirements:
- Length: 200-300 words
- Structure: Hook line → Story/insight → Lesson → CTA
- Tone: Professional, conversational
- Use line breaks for readability
- End with an engaging question or call to action

Write the LinkedIn post:"""

        system_prompt = "You are a thought leader sharing insights on LinkedIn."

        return await self.generate(prompt, system_prompt)

    async def generate_x_thread(
        self,
        topic: str,
        source_chunks: list[str]
    ) -> str:
        """Generate an X/Twitter thread from knowledge chunks."""
        sources = "\n".join(f"- {chunk}" for chunk in source_chunks)

        prompt = f"""Write an X (Twitter) thread about: {topic}

Use these knowledge sources:
{sources}

Requirements:
- 5-7 tweets total
- First tweet: Strong hook with 🧵 emoji
- Each tweet: Under 280 characters
- Format each tweet on its own line with tweet number (1/, 2/, etc.)
- Last tweet: Summary + CTA
- Tone: Punchy, value-dense

Write the thread:"""

        system_prompt = "You are a viral content creator who writes engaging Twitter threads."

        return await self.generate(prompt, system_prompt)

    async def generate_video_script(
        self,
        topic: str,
        source_chunks: list[str],
        duration_seconds: int = 90
    ) -> str:
        """Generate a short video script from knowledge chunks."""
        sources = "\n".join(f"- {chunk}" for chunk in source_chunks)

        prompt = f"""Write a {duration_seconds}-second video script about: {topic}

Use these knowledge sources:
{sources}

Requirements:
- Duration: {duration_seconds} seconds when spoken
- Structure:
  - Hook (5 seconds): Grab attention immediately
  - Problem (15 seconds): Why this matters
  - Insight (50 seconds): The main content
  - CTA (10 seconds): What to do next
- Format: Include [VISUAL] cues for each section
- Tone: Energetic, conversational, spoken word

Write the script:"""

        system_prompt = "You are a video content creator who writes engaging short-form scripts."

        return await self.generate(prompt, system_prompt)

    async def generate_digest_summary(
        self,
        chunks: list[str],
        date_range: str
    ) -> dict:
        """Generate a weekly digest summary with topic suggestions."""
        sources = "\n".join(f"- {chunk}" for chunk in chunks)

        prompt = f"""Analyze these knowledge notes from {date_range}:

{sources}

Generate:
1. A narrative summary (2-3 paragraphs) of what was learned
2. 3-5 suggested content topics based on patterns/themes
3. For each topic, explain why it would make good content

Format as JSON:
{{
  "summary": "narrative summary here",
  "topics": [
    {{"title": "Topic 1", "reasoning": "why this is interesting", "relevant_chunks": ["chunk1", "chunk2"]}},
    ...
  ]
}}"""

        system_prompt = "You are a knowledge curator who identifies patterns and content opportunities."

        result = await self.generate(prompt, system_prompt)

        # Parse JSON from response
        import json
        try:
            # Handle markdown code blocks
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            return json.loads(result.strip())
        except json.JSONDecodeError:
            return {"summary": result, "topics": []}
```

**Step 4: Update services/__init__.py**

```python
# zettl/api/app/services/__init__.py
from app.services.cognee_service import CogneeService
from app.services.llm_service import LLMService

__all__ = ["CogneeService", "LLMService"]
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_llm_service.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add api/app/services/
git commit -m "feat: add LLMService with content generation templates"
```

---

### Task 7: Create Digest Router

**Files:**
- Create: `zettl/api/app/models/digest.py`
- Create: `zettl/api/app/models/content.py`
- Create: `zettl/api/app/routers/digest.py`
- Modify: `zettl/api/app/main.py`
- Test: `zettl/api/tests/test_digest_router.py`

**Step 1: Write the failing test**

```python
# zettl/api/tests/test_digest_router.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def client():
    with patch("app.routers.digest.CogneeService") as MockCognee, \
         patch("app.routers.digest.LLMService") as MockLLM:

        mock_cognee = MockCognee.return_value
        mock_cognee.search = AsyncMock(return_value=["chunk1", "chunk2"])

        mock_llm = MockLLM.return_value
        mock_llm.generate_digest_summary = AsyncMock(return_value={
            "summary": "This week you learned about graphs",
            "topics": [
                {"title": "Graph DBs", "reasoning": "Interesting pattern", "relevant_chunks": ["chunk1"]}
            ]
        })
        mock_llm.generate_blog_draft = AsyncMock(return_value="# Blog content")
        mock_llm.generate_linkedin_post = AsyncMock(return_value="LinkedIn post")
        mock_llm.generate_x_thread = AsyncMock(return_value="1/ Thread")
        mock_llm.generate_video_script = AsyncMock(return_value="[HOOK] Script")

        from app.main import app
        with TestClient(app) as c:
            yield c


def test_create_digest_returns_201(client):
    response = client.post("/digest")
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "summary" in data
    assert "suggested_topics" in data


def test_generate_content_for_topic(client):
    response = client.post(
        "/digest/content",
        json={
            "topic": "Graph Databases",
            "source_chunks": ["chunk1", "chunk2"],
            "formats": ["blog", "linkedin"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "blog" in data
    assert "linkedin" in data
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_digest_router.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create digest.py model**

```python
# zettl/api/app/models/digest.py
from datetime import datetime
from pydantic import BaseModel, Field


class TopicSuggestion(BaseModel):
    title: str
    reasoning: str
    relevant_chunks: list[str] = Field(default_factory=list)


class DigestResponse(BaseModel):
    id: str
    summary: str
    suggested_topics: list[TopicSuggestion]
    week_start: datetime
    week_end: datetime
    created_at: datetime
```

**Step 4: Create content.py model**

```python
# zettl/api/app/models/content.py
from pydantic import BaseModel, Field
from enum import Enum


class ContentFormat(str, Enum):
    BLOG = "blog"
    LINKEDIN = "linkedin"
    X_THREAD = "x_thread"
    VIDEO_SCRIPT = "video_script"


class ContentGenerationRequest(BaseModel):
    topic: str
    source_chunks: list[str]
    formats: list[ContentFormat] = Field(
        default=[ContentFormat.BLOG, ContentFormat.LINKEDIN, ContentFormat.X_THREAD, ContentFormat.VIDEO_SCRIPT]
    )


class ContentGenerationResponse(BaseModel):
    topic: str
    blog: str | None = None
    linkedin: str | None = None
    x_thread: str | None = None
    video_script: str | None = None
```

**Step 5: Update models/__init__.py**

```python
# zettl/api/app/models/__init__.py
from app.models.note import NoteCreate, NoteResponse, NoteSource
from app.models.digest import DigestResponse, TopicSuggestion
from app.models.content import ContentFormat, ContentGenerationRequest, ContentGenerationResponse

__all__ = [
    "NoteCreate", "NoteResponse", "NoteSource",
    "DigestResponse", "TopicSuggestion",
    "ContentFormat", "ContentGenerationRequest", "ContentGenerationResponse",
]
```

**Step 6: Create digest.py router**

```python
# zettl/api/app/routers/digest.py
from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
import uuid

from app.models.digest import DigestResponse, TopicSuggestion
from app.models.content import ContentFormat, ContentGenerationRequest, ContentGenerationResponse
from app.services.cognee_service import CogneeService
from app.services.llm_service import LLMService

router = APIRouter()
cognee_service = CogneeService()
llm_service = LLMService()


@router.post("/digest", response_model=DigestResponse, status_code=status.HTTP_201_CREATED)
async def create_digest():
    """
    Generate a weekly digest from recent knowledge.
    """
    try:
        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

        # Get recent chunks from Cognee
        chunks = await cognee_service.search(
            query="recent learnings and insights",
            search_type="chunks"
        )

        if not chunks:
            # If no chunks, return empty digest
            return DigestResponse(
                id=str(uuid.uuid4()),
                summary="No new knowledge added this week.",
                suggested_topics=[],
                week_start=start_date,
                week_end=end_date,
                created_at=datetime.now(),
            )

        # Generate digest summary with LLM
        digest_data = await llm_service.generate_digest_summary(
            chunks=chunks,
            date_range=date_range
        )

        # Parse topics
        topics = [
            TopicSuggestion(
                title=t.get("title", ""),
                reasoning=t.get("reasoning", ""),
                relevant_chunks=t.get("relevant_chunks", [])
            )
            for t in digest_data.get("topics", [])
        ]

        return DigestResponse(
            id=str(uuid.uuid4()),
            summary=digest_data.get("summary", ""),
            suggested_topics=topics,
            week_start=start_date,
            week_end=end_date,
            created_at=datetime.now(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create digest: {str(e)}"
        )


@router.post("/digest/content", response_model=ContentGenerationResponse)
async def generate_content(request: ContentGenerationRequest):
    """
    Generate content drafts for a topic in specified formats.
    """
    try:
        result = ContentGenerationResponse(topic=request.topic)

        for fmt in request.formats:
            if fmt == ContentFormat.BLOG:
                result.blog = await llm_service.generate_blog_draft(
                    topic=request.topic,
                    source_chunks=request.source_chunks
                )
            elif fmt == ContentFormat.LINKEDIN:
                result.linkedin = await llm_service.generate_linkedin_post(
                    topic=request.topic,
                    source_chunks=request.source_chunks
                )
            elif fmt == ContentFormat.X_THREAD:
                result.x_thread = await llm_service.generate_x_thread(
                    topic=request.topic,
                    source_chunks=request.source_chunks
                )
            elif fmt == ContentFormat.VIDEO_SCRIPT:
                result.video_script = await llm_service.generate_video_script(
                    topic=request.topic,
                    source_chunks=request.source_chunks
                )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )
```

**Step 7: Update routers/__init__.py**

```python
# zettl/api/app/routers/__init__.py
from app.routers.notes import router as notes_router
from app.routers.digest import router as digest_router

__all__ = ["notes_router", "digest_router"]
```

**Step 8: Update main.py to include digest router**

```python
# zettl/api/app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers.notes import router as notes_router
from app.routers.digest import router as digest_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize Cognee config
    settings = get_settings()

    import cognee
    cognee.config.set_graph_db_config({
        "graph_database_provider": settings.graph_database_provider,
        "graph_database_url": settings.graph_database_url,
        "graph_database_username": settings.graph_database_username,
        "graph_database_password": settings.graph_database_password,
    })

    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Zettl API",
    description="Personal knowledge graph service",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(notes_router, tags=["notes"])
app.include_router(digest_router, tags=["digest"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 9: Run test to verify it passes**

```bash
pytest tests/test_digest_router.py -v
```

Expected: PASS

**Step 10: Commit**

```bash
git add api/app/models/ api/app/routers/ api/app/main.py api/tests/
git commit -m "feat: add /digest and /digest/content endpoints"
```

---

## Phase 4: Simple Capture UI

### Task 8: Initialize Next.js UI

**Files:**
- Create: `zettl/ui/` (Next.js project)
- Create: `zettl/ui/Dockerfile`

**Step 1: Create Next.js app with shadcn/ui**

```bash
cd zettl
npx create-next-app@latest ui --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*"
cd ui
npx shadcn@latest init -d
npx shadcn@latest add button textarea card badge toast
```

**Step 2: Create Dockerfile for UI**

```dockerfile
# zettl/ui/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
```

**Step 3: Update next.config.js for standalone output**

```javascript
// zettl/ui/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
}

module.exports = nextConfig
```

**Step 4: Update docker-compose.yml to include UI**

```yaml
# zettl/docker-compose.yml (add ui service)
services:
  neo4j:
    image: neo4j:5.17-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/zettlpassword123
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.*
    volumes:
      - neo4j_data:/data
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:7474"]
      interval: 10s
      timeout: 5s
      retries: 10

  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=zettlpassword123
      - GRAPH_DATABASE_PROVIDER=neo4j
      - GRAPH_DATABASE_URL=bolt://neo4j:7687
      - GRAPH_DATABASE_USERNAME=neo4j
      - GRAPH_DATABASE_PASSWORD=zettlpassword123
      # For Vertex AI authentication in Docker
      - GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json
      - GOOGLE_CLOUD_PROJECT=your-gcp-project
    env_file:
      - .env
    depends_on:
      neo4j:
        condition: service_healthy
    volumes:
      - ./api:/app
      - cognee_data:/app/cognee_data
      # Mount gcloud credentials for Vertex AI
      - ~/.config/gcloud:/root/.config/gcloud:ro

  ui:
    build: ./ui
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - api

volumes:
  neo4j_data:
  cognee_data:
```

**Step 5: Commit**

```bash
cd zettl
git add ui/ docker-compose.yml
git commit -m "feat: initialize Next.js UI with shadcn/ui"
```

---

### Task 9: Create Capture Page

**Files:**
- Create: `zettl/ui/app/capture/page.tsx`
- Create: `zettl/ui/components/capture-form.tsx`
- Create: `zettl/ui/lib/api.ts`

**Step 1: Create API client**

```typescript
// zettl/ui/lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface NoteCreate {
  content: string;
  source?: 'manual' | 'notion' | 'agent' | 'ui';
  tags?: string[];
  source_reference?: string;
}

export interface NoteResponse {
  id: string;
  content: string;
  source: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export async function createNote(note: NoteCreate): Promise<NoteResponse> {
  const response = await fetch(`${API_URL}/notes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...note,
      source: note.source || 'ui',
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create note: ${response.statusText}`);
  }

  return response.json();
}
```

**Step 2: Create capture form component**

```typescript
// zettl/ui/components/capture-form.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { createNote } from '@/lib/api';

export function CaptureForm() {
  const [content, setContent] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleAddTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      if (!tags.includes(tagInput.trim())) {
        setTags([...tags, tagInput.trim()]);
      }
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setIsSubmitting(true);
    try {
      await createNote({
        content: content.trim(),
        tags,
        source: 'ui',
      });

      toast({
        title: 'Note saved',
        description: 'Your note has been added to the knowledge graph.',
      });

      setContent('');
      setTags([]);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save note. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-teal-900">Quick Capture</CardTitle>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          <Textarea
            placeholder="What did you learn?"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="min-h-[200px] resize-none"
            disabled={isSubmitting}
          />

          <div className="space-y-2">
            <input
              type="text"
              placeholder="Add tags (press Enter)"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={handleAddTag}
              className="w-full px-3 py-2 border rounded-md text-sm"
              disabled={isSubmitting}
            />
            <div className="flex flex-wrap gap-2">
              {tags.map(tag => (
                <Badge
                  key={tag}
                  variant="secondary"
                  className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                  onClick={() => handleRemoveTag(tag)}
                >
                  {tag} ×
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setContent('');
              setTags([]);
            }}
            disabled={isSubmitting}
          >
            Clear
          </Button>
          <Button
            type="submit"
            disabled={!content.trim() || isSubmitting}
            className="bg-teal-600 hover:bg-teal-700"
          >
            {isSubmitting ? 'Saving...' : 'Save'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
```

**Step 3: Create capture page**

```typescript
// zettl/ui/app/capture/page.tsx
import { CaptureForm } from '@/components/capture-form';
import { Toaster } from '@/components/ui/toaster';

export default function CapturePage() {
  return (
    <main className="min-h-screen bg-teal-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-teal-900 text-center mb-8">
          Zettl
        </h1>
        <p className="text-teal-700 text-center mb-8">
          Capture your knowledge. Let the connections emerge.
        </p>
        <CaptureForm />
      </div>
      <Toaster />
    </main>
  );
}
```

**Step 4: Update root page to redirect to capture**

```typescript
// zettl/ui/app/page.tsx
import { redirect } from 'next/navigation';

export default function Home() {
  redirect('/capture');
}
```

**Step 5: Add Plus Jakarta Sans font**

```typescript
// zettl/ui/app/layout.tsx
import type { Metadata } from 'next';
import { Plus_Jakarta_Sans } from 'next/font/google';
import './globals.css';

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-plus-jakarta',
});

export const metadata: Metadata = {
  title: 'Zettl - Knowledge Graph',
  description: 'Personal knowledge management with auto-linking',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${plusJakarta.variable} font-sans`}>{children}</body>
    </html>
  );
}
```

**Step 6: Commit**

```bash
git add ui/
git commit -m "feat: add simple capture UI with form and toast notifications"
```

---

## Phase 5: Integration Testing

### Task 10: End-to-End Test

**Step 1: Start all services**

```bash
cd zettl
docker-compose up --build
```

**Step 2: Wait for services to be healthy**

Check:
- Neo4j: http://localhost:7474 (login: neo4j/zettlpassword123)
- API: http://localhost:8000/health
- UI: http://localhost:3000/capture

**Step 3: Test note creation via API**

```bash
curl -X POST http://localhost:8000/notes \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Today I learned that Neo4j uses Cypher as its query language. Cypher is declarative and pattern-based, making graph traversals intuitive.",
    "tags": ["neo4j", "graph-db", "cypher"]
  }'
```

Expected: 201 response with note ID

**Step 4: Add more test notes**

```bash
curl -X POST http://localhost:8000/notes \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Cognee builds knowledge graphs automatically from text. It extracts entities, relationships, and creates semantic connections.",
    "tags": ["cognee", "knowledge-graph", "ai"]
  }'

curl -X POST http://localhost:8000/notes \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The Zettelkasten method emphasizes atomic notes with explicit links. Each note should contain one idea and link to related notes.",
    "tags": ["zettelkasten", "note-taking", "productivity"]
  }'
```

**Step 5: Test search**

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "graph database"}'
```

Expected: Results containing relevant chunks

**Step 6: Test digest generation**

```bash
curl -X POST http://localhost:8000/digest
```

Expected: 201 response with summary and suggested topics

**Step 7: Test content generation**

```bash
curl -X POST http://localhost:8000/digest/content \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Graph Databases for Knowledge Management",
    "source_chunks": ["Neo4j uses Cypher", "Cognee builds knowledge graphs"],
    "formats": ["blog", "linkedin"]
  }'
```

Expected: Generated blog and LinkedIn content

**Step 8: Test UI**

1. Open http://localhost:3000/capture
2. Enter a note: "Testing the UI capture form works correctly"
3. Add tags: test, ui
4. Click Save
5. Verify toast shows "Note saved"

**Step 9: Verify in Neo4j**

1. Open http://localhost:7474
2. Login with neo4j/zettlpassword123
3. Run: `MATCH (n) RETURN n LIMIT 25`
4. Verify nodes exist in graph

**Step 10: Commit final state**

```bash
git add .
git commit -m "feat: complete MVP with notes, search, digest, and UI"
```

---

## Summary

**What we built:**
- FastAPI backend with Cognee integration for auto-linking
- Neo4j graph database for knowledge storage
- LiteLLM-based content generation (blog, LinkedIn, X, video script)
- Simple capture UI with Next.js + shadcn/ui
- Docker Compose for local development

**API Endpoints:**
- `POST /notes` - Add note to knowledge graph
- `POST /search` - Search knowledge
- `POST /digest` - Generate weekly digest
- `POST /digest/content` - Generate content drafts

**Next steps (future phases):**
- Notion sync integration
- Scheduled digests with Cloud Scheduler
- Full dashboard UI
- GCP deployment with Terraform
- Agent API authentication

---

## Troubleshooting

### Vertex AI "Google Cloud SDK not found" Error

**Symptom:** API hangs or fails with `ModuleNotFoundError: No module named 'google.auth'`

**Cause:** LiteLLM needs Google Cloud auth libraries for Vertex AI.

**Fix:** Install the Google extras:
```bash
pip install 'litellm[google]'
# or
pip install google-cloud-aiplatform
```

For Docker, ensure `pyproject.toml` has `litellm[google]>=1.30.0` and rebuild.

### "No project ID could be determined" Error

**Symptom:** `No project ID could be determined. Consider running gcloud config set project`

**Cause:** Google Cloud SDK needs explicit project ID in containers.

**Fix:** Set `GOOGLE_CLOUD_PROJECT` environment variable in docker-compose.yml:
```yaml
environment:
  - GOOGLE_CLOUD_PROJECT=your-gcp-project
```

### Cognee Multi-User Access Control Error

**Symptom:** `The selected graph dataset to database handler does not work with the configured graph database provider`

**Cause:** Cognee 0.5+ has multi-user access control that requires compatible handlers.

**Fix:** Disable access control for local dev:
```bash
ENABLE_BACKEND_ACCESS_CONTROL=false
```

### Cognee Embeddings Configuration

**Symptom:** Embedding operations fail or hang.

**Cause:** Missing embedding configuration for custom providers.

**Fix:** Set all required embedding environment variables:
```bash
EMBEDDING_PROVIDER=custom
EMBEDDING_MODEL=vertex_ai/text-embedding-005
EMBEDDING_API_KEY=gcp-credentials-used
EMBEDDING_DIMENSIONS=768  # Required for custom providers
```

---

## References

- [Cognee Documentation](https://docs.cognee.ai/getting-started/quickstart)
- [Cognee Neo4j Example](https://github.com/topoteretes/cognee/blob/main/examples/database_examples/neo4j_example.py)
- [LiteLLM Vertex AI](https://github.com/berriai/litellm/blob/main/docs/my-website/docs/providers/vertex.md)
- [shadcn/ui Components](https://ui.shadcn.com/docs/components)
