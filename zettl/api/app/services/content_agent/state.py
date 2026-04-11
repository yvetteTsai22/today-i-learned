from typing_extensions import TypedDict, Annotated
from langchain_core.messages import BaseMessage
import operator


class ContentAgentState(TypedDict):
    """State for the content generation agent.

    - topic: The content topic to generate about
    - source_chunks: Knowledge chunks to use as source material
    - formats: List of content format names to generate (e.g., ["blog", "linkedin"])
    - messages: LangChain message history for the agent loop
    """

    topic: str
    source_chunks: list[str]
    formats: list[str]
    messages: Annotated[list[BaseMessage], operator.add]
