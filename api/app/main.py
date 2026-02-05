from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Configure CORS - allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notes_router, tags=["notes"])
app.include_router(digest_router, tags=["digest"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
