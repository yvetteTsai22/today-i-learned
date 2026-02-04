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
