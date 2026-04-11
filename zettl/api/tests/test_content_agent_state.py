from app.services.content_agent.state import ContentAgentState
from langchain_core.messages import HumanMessage


def test_state_has_required_fields():
    """ContentAgentState must have topic, source_chunks, formats, and messages."""
    state: ContentAgentState = {
        "topic": "Graph Databases",
        "source_chunks": ["chunk1", "chunk2"],
        "formats": ["blog", "linkedin"],
        "messages": [HumanMessage(content="hello")],
    }
    assert state["topic"] == "Graph Databases"
    assert len(state["source_chunks"]) == 2
    assert len(state["formats"]) == 2
    assert len(state["messages"]) == 1
