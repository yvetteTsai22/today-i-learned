"""Tests for MCP server."""

import pytest
from unittest.mock import AsyncMock, patch

from mcp.client.session import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session

from zettl_mcp.server import mcp


@pytest.mark.anyio
async def test_server_lists_tools():
    """Server exposes expected tools."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        tools = await session.list_tools()
        tool_names = [t.name for t in tools.tools]

        assert "add_note" in tool_names
        assert "search_knowledge" in tool_names
        assert "generate_digest" in tool_names
        assert "generate_content" in tool_names


@pytest.mark.anyio
async def test_add_note_tool():
    """add_note tool creates note and returns confirmation."""
    mock_client = AsyncMock()
    mock_client.add_note.return_value = {
        "id": "note-abc123",
        "content": "Test note content",
        "source": "agent",
        "tags": ["test"],
    }

    with patch("zettl_mcp.server.get_client", return_value=mock_client):
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            result = await session.call_tool("add_note", {
                "content": "Test note content",
                "tags": ["test"],
            })

            # Result should be a success message
            assert len(result.content) == 1
            assert "note-abc123" in result.content[0].text
            mock_client.add_note.assert_called_once_with(
                content="Test note content",
                tags=["test"],
                source="agent",
            )


@pytest.mark.anyio
async def test_search_knowledge_tool():
    """search_knowledge tool returns formatted results."""
    mock_client = AsyncMock()
    mock_client.search.return_value = {
        "results": ["First insight about AI", "Second insight about testing"],
        "query": "AI testing",
    }

    with patch("zettl_mcp.server.get_client", return_value=mock_client):
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            result = await session.call_tool("search_knowledge", {
                "query": "AI testing",
            })

            assert "First insight about AI" in result.content[0].text
            assert "Second insight about testing" in result.content[0].text


@pytest.mark.anyio
async def test_search_knowledge_empty_results():
    """search_knowledge handles empty results gracefully."""
    mock_client = AsyncMock()
    mock_client.search.return_value = {
        "results": [],
        "query": "nonexistent topic",
    }

    with patch("zettl_mcp.server.get_client", return_value=mock_client):
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            result = await session.call_tool("search_knowledge", {
                "query": "nonexistent topic",
            })

            assert "No results found" in result.content[0].text


@pytest.mark.anyio
async def test_generate_digest_tool():
    """generate_digest tool returns formatted summary and topics."""
    mock_client = AsyncMock()
    mock_client.generate_digest.return_value = {
        "id": "digest-123",
        "summary": "This week you learned about AI testing patterns.",
        "suggested_topics": [
            {"title": "TDD for AI", "reasoning": "Multiple notes on testing"},
            {"title": "Prompt Engineering", "reasoning": "Growing interest"},
        ],
    }

    with patch("zettl_mcp.server.get_client", return_value=mock_client):
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            result = await session.call_tool("generate_digest", {})

            text = result.content[0].text
            assert "AI testing patterns" in text
            assert "TDD for AI" in text
            assert "Prompt Engineering" in text


@pytest.mark.anyio
async def test_generate_digest_force_refresh():
    """generate_digest tool passes force_refresh to client."""
    mock_client = AsyncMock()
    mock_client.generate_digest.return_value = {
        "id": "digest-456",
        "summary": "Fresh digest after force refresh.",
        "suggested_topics": [],
    }

    with patch("zettl_mcp.server.get_client", return_value=mock_client):
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            result = await session.call_tool("generate_digest", {
                "force_refresh": True,
            })

            text = result.content[0].text
            assert "Fresh digest" in text
            mock_client.generate_digest.assert_called_once_with(
                force_refresh=True
            )


@pytest.mark.anyio
async def test_generate_content_tool():
    """generate_content tool returns formatted content drafts."""
    mock_client = AsyncMock()
    mock_client.generate_content.return_value = {
        "topic": "AI Testing",
        "blog": "# Testing AI Systems\n\nWriting tests for AI...",
        "linkedin": "Excited to share insights on AI testing!",
    }

    with patch("zettl_mcp.server.get_client", return_value=mock_client):
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            result = await session.call_tool("generate_content", {
                "topic": "AI Testing",
                "source_chunks": ["chunk 1", "chunk 2"],
                "formats": ["blog", "linkedin"],
            })

            text = result.content[0].text
            assert "Blog" in text
            assert "LinkedIn" in text
            assert "Testing AI Systems" in text
