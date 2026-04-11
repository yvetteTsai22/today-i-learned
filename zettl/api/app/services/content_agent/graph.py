from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage

from app.services.content_agent.state import ContentAgentState
from app.services.content_agent.tools import list_skills, load_skill, create_search_knowledge_tool
from app.services.cognee_service import CogneeService


def _should_continue(state: ContentAgentState) -> str:
    """Route: if the last message has tool_calls, go to tools. Otherwise, end."""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END


def build_content_graph(llm, cognee_service: CogneeService):
    """Build and compile the content generation agent graph.

    Args:
        llm: A LangChain chat model (e.g., ChatLiteLLM)
        cognee_service: CogneeService instance for knowledge graph search
    """
    # Assemble tools
    search_knowledge = create_search_knowledge_tool(cognee_service)
    tools = [list_skills, load_skill, search_knowledge]

    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(tools)

    # Define the agent node
    async def agent_node(state: ContentAgentState) -> dict:
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    # Build graph
    tool_node = ToolNode(tools, handle_tool_errors=True)

    graph = (
        StateGraph(ContentAgentState)
        .add_node("agent", agent_node)
        .add_node("tools", tool_node)
        .add_edge(START, "agent")
        .add_conditional_edges("agent", _should_continue, ["tools", END])
        .add_edge("tools", "agent")
        .compile()
    )

    return graph
