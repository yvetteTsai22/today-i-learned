from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import AIMessage, HumanMessage

from app.models.content import ContentFormat


async def test_generate_returns_content_response():
    """ContentAgentService.generate should return a ContentGenerationResponse."""
    from app.services.content_agent import ContentAgentService

    # Mock the LLM to return content for blog format
    mock_llm = MagicMock()
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    final_response = AIMessage(content='{"blog": "# My Blog Post\\n\\nContent here."}')
    mock_llm.ainvoke = AsyncMock(return_value=final_response)

    mock_cognee = MagicMock()
    mock_cognee.search = AsyncMock(return_value=[])

    service = ContentAgentService(llm=mock_llm, cognee_service=mock_cognee)

    result = await service.generate(
        topic="Graph Databases",
        source_chunks=["Neo4j stores data in nodes"],
        formats=[ContentFormat.BLOG],
    )

    assert result.topic == "Graph Databases"
    # The agent returned content (exact parsing depends on implementation)
    assert result.blog is not None or result.linkedin is not None


async def test_generate_with_multiple_formats():
    """ContentAgentService should handle requests for multiple formats."""
    from app.services.content_agent import ContentAgentService

    mock_llm = MagicMock()
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    final_response = AIMessage(
        content='{"blog": "Blog content", "linkedin": "LinkedIn content"}'
    )
    mock_llm.ainvoke = AsyncMock(return_value=final_response)

    mock_cognee = MagicMock()
    mock_cognee.search = AsyncMock(return_value=[])

    service = ContentAgentService(llm=mock_llm, cognee_service=mock_cognee)

    result = await service.generate(
        topic="AI Agents",
        source_chunks=["LangGraph builds agent workflows"],
        formats=[ContentFormat.BLOG, ContentFormat.LINKEDIN],
    )

    assert result.topic == "AI Agents"


def test_parse_response_handles_markdown_code_block():
    """_parse_response should extract JSON from markdown code blocks."""
    from app.services.content_agent import ContentAgentService

    mock_llm = MagicMock()
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    mock_cognee = MagicMock()
    mock_cognee.search = AsyncMock(return_value=[])

    service = ContentAgentService(llm=mock_llm, cognee_service=mock_cognee)
    result = service._parse_response("topic", ["blog"], {
        "messages": [AIMessage(content='```json\n{"blog": "Blog content here"}\n```')]
    })
    assert result.blog == "Blog content here"


def test_parse_response_falls_back_on_invalid_json():
    """_parse_response should assign raw content to first format on invalid JSON."""
    from app.services.content_agent import ContentAgentService

    mock_llm = MagicMock()
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    mock_cognee = MagicMock()
    mock_cognee.search = AsyncMock(return_value=[])

    service = ContentAgentService(llm=mock_llm, cognee_service=mock_cognee)
    result = service._parse_response("topic", ["blog"], {
        "messages": [AIMessage(content="This is not JSON at all")]
    })
    assert result.blog == "This is not JSON at all"


def test_parse_response_returns_empty_when_no_ai_message():
    """_parse_response should return empty response when no AIMessage found."""
    from app.services.content_agent import ContentAgentService

    mock_llm = MagicMock()
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    mock_cognee = MagicMock()
    mock_cognee.search = AsyncMock(return_value=[])

    service = ContentAgentService(llm=mock_llm, cognee_service=mock_cognee)
    result = service._parse_response("topic", ["blog"], {
        "messages": [HumanMessage(content="No AI response here")]
    })
    assert result.topic == "topic"
    assert result.blog is None
