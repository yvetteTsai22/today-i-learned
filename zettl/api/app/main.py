import json
import logging
import os
import shutil

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.notes import router as notes_router
from app.routers.digest import router as digest_router
from app.routers.stats import router as stats_router

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def _migrate_vector_store_if_needed() -> None:
    """
    Wipe the LanceDB directory if the Cognee version has changed.

    Cognee 0.5.2 added `belongs_to_set` to DataPoint. LanceDB raises
    'Field not found in target schema' when old tables lack new fields.
    Deleting the directory lets Cognee recreate it with the current schema.
    Notes are safe — they live in Neo4j, not LanceDB.
    """
    import importlib.metadata

    try:
        cognee_version = importlib.metadata.version("cognee")
    except Exception:
        return

    system_root = os.environ.get(
        "SYSTEM_ROOT_DIRECTORY",
        os.path.join(os.path.expanduser("~"), ".local", "share", "cognee", "system"),
    )
    version_file = os.path.join(system_root, ".schema_version.json")
    lancedb_path = os.path.join(system_root, "databases", "cognee.lancedb")

    stored_version = None
    if os.path.exists(version_file):
        try:
            with open(version_file) as f:
                stored_version = json.load(f).get("cognee_version")
        except Exception:
            pass

    if stored_version != cognee_version:
        if os.path.exists(lancedb_path):
            logger.info(
                "Cognee version changed (%s → %s): wiping stale LanceDB at %s",
                stored_version,
                cognee_version,
                lancedb_path,
            )
            shutil.rmtree(lancedb_path)
        os.makedirs(system_root, exist_ok=True)
        with open(version_file, "w") as f:
            json.dump({"cognee_version": cognee_version}, f)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize Cognee config
    settings = get_settings()

    _migrate_vector_store_if_needed()

    import cognee
    cognee.config.set_graph_db_config({
        "graph_database_provider": settings.graph_database_provider,
        "graph_database_url": settings.graph_database_url,
        "graph_database_username": settings.graph_database_username,
        "graph_database_password": settings.graph_database_password,
    })

    # Explicitly configure Cognee's LLM so it doesn't rely on its own env-var detection.
    # llm_api_key="adc" is a dummy sentinel: Cognee's CUSTOM provider requires a non-None
    # value, but LiteLLM ignores it for vertex_ai/* models and authenticates via
    # GOOGLE_APPLICATION_CREDENTIALS instead.
    cognee.config.set_llm_config({
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_api_key": "adc",
    })

    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Zettl API",
    description="Personal knowledge graph service",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS - allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notes_router, tags=["notes"])
app.include_router(digest_router, tags=["digest"])
app.include_router(stats_router, tags=["stats"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
