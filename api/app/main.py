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
