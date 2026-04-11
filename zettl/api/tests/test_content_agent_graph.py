import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


async def test_graph_compiles_and_runs():
    """The content agent graph should compile and run with a mock LLM."""
    from app.services.content_agent.graph import build_content_graph
    from app.services.cognee_service import CogneeService

    mock_cognee = MagicMock(spec=CogneeService)
    mock_cognee.search = AsyncMock(return_value=[])

    # Create a mock LLM that returns a final answer (no tool calls)
    mock_llm = MagicMock()
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    mock_response = AIMessage(content="# Blog Post\n\nHere is the generated content.")
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    graph = build_content_graph(llm=mock_llm, cognee_service=mock_cognee)

    result = await graph.ainvoke({
        "topic": "Graph Databases",
        "source_chunks": ["Neo4j stores data in nodes"],
        "formats": ["blog"],
        "messages": [HumanMessage(content="Generate blog content about Graph Databases")],
    })

    assert len(result["messages"]) > 0
    # Last message should be the AI response
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    assert "Blog Post" in last_msg.content


async def test_graph_handles_tool_calls():
    """The graph should execute tool calls and loop back to the agent."""
    from app.services.content_agent.graph import build_content_graph
    from app.services.cognee_service import CogneeService

    mock_cognee = MagicMock(spec=CogneeService)
    mock_cognee.search = AsyncMock(return_value=[])

    # First call: LLM requests list_skills tool
    tool_call_msg = AIMessage(
        content="",
        tool_calls=[{"id": "call_1", "name": "list_skills", "args": {}}],
    )
    # Second call: LLM returns final content
    final_msg = AIMessage(content="Generated content here.")

    mock_llm = MagicMock()
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    mock_llm.ainvoke = AsyncMock(side_effect=[tool_call_msg, final_msg])

    graph = build_content_graph(llm=mock_llm, cognee_service=mock_cognee)

    result = await graph.ainvoke({
        "topic": "Test",
        "source_chunks": ["chunk"],
        "formats": ["blog"],
        "messages": [HumanMessage(content="Generate content")],
    })

    # Should have: HumanMessage, AIMessage (tool call), ToolMessage (result), AIMessage (final)
    assert len(result["messages"]) >= 3
    # Verify tool was called (list_skills should appear in a ToolMessage)
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) >= 1
