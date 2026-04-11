import pytest
from pathlib import Path


def test_list_skills_returns_available_skills():
    """list_skills should return names of all .md files in skills/ directory."""
    from app.services.content_agent.tools import list_skills

    result = list_skills.invoke({})
    assert "write-blog-post" in result
    assert "write-linkedin-post" in result
    assert "write-x-thread" in result
    assert "write-video-script" in result


def test_load_skill_returns_skill_content():
    """load_skill should return the full content of a skill file."""
    from app.services.content_agent.tools import load_skill

    result = load_skill.invoke({"skill_name": "write-blog-post"})
    assert "Blog Post Writer" in result
    assert "Hook" in result
    assert "Structure" in result


def test_load_skill_returns_error_for_unknown_skill():
    """load_skill should return an error message for unknown skills."""
    from app.services.content_agent.tools import load_skill

    result = load_skill.invoke({"skill_name": "nonexistent-skill"})
    assert "not found" in result.lower()


def test_load_skill_prevents_path_traversal():
    """load_skill must not allow path traversal attacks."""
    from app.services.content_agent.tools import load_skill

    result = load_skill.invoke({"skill_name": "../../../etc/passwd"})
    assert "not found" in result.lower()


async def test_search_knowledge_returns_results():
    """search_knowledge should query CogneeService and return formatted results."""
    from unittest.mock import AsyncMock, MagicMock

    mock_cognee = MagicMock()
    mock_cognee.search = AsyncMock(return_value=[
        {"id": "1", "content": "Neo4j is a graph database", "source": "note", "tags": [], "created_at": "2026-03-01"},
        {"id": "2", "content": "Cypher is the query language", "source": "note", "tags": [], "created_at": "2026-03-02"},
    ])

    from app.services.content_agent.tools import create_search_knowledge_tool
    search_tool = create_search_knowledge_tool(mock_cognee)

    result = await search_tool.ainvoke({"query": "graph databases"})
    assert "Neo4j is a graph database" in result
    assert "Cypher is the query language" in result
    mock_cognee.search.assert_called_once_with(query="graph databases", search_type="graph_completion")


async def test_search_knowledge_handles_empty_results():
    """search_knowledge should return a message when no results found."""
    from unittest.mock import AsyncMock, MagicMock

    mock_cognee = MagicMock()
    mock_cognee.search = AsyncMock(return_value=[])

    from app.services.content_agent.tools import create_search_knowledge_tool
    search_tool = create_search_knowledge_tool(mock_cognee)

    result = await search_tool.ainvoke({"query": "nonexistent topic"})
    assert "no results" in result.lower()
