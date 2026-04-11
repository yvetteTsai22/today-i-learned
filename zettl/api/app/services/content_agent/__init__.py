import asyncio
import json
import logging
import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_litellm import ChatLiteLLM

from app.config import get_settings
from app.models.content import ContentFormat, ContentGenerationResponse
from app.services.cognee_service import CogneeService
from app.services.content_agent.graph import build_content_graph
from app.services.llm_service import resolve_litellm_model

logger = logging.getLogger(__name__)

AGENT_RECURSION_LIMIT = 40
AGENT_TIMEOUT_SECONDS = 120


class ContentAgentService:
    """Service that uses a LangGraph agent to generate content.

    The agent loads SKILL.md files dynamically to determine how to generate
    each content format, and uses tools to search the knowledge graph.
    """

    def __init__(self, llm=None, cognee_service: CogneeService | None = None):
        settings = get_settings()
        self.cognee_service = cognee_service or CogneeService()

        if llm is None:
            self.llm = ChatLiteLLM(model=resolve_litellm_model(settings), max_tokens=4000)
        else:
            self.llm = llm

        self.graph = build_content_graph(
            llm=self.llm,
            cognee_service=self.cognee_service,
        )

    async def generate(
        self,
        topic: str,
        source_chunks: list[str],
        formats: list[ContentFormat],
    ) -> ContentGenerationResponse:
        """Generate content for a topic in the requested formats."""
        format_names = [f.value for f in formats]
        sources = "\n".join(f"- {chunk}" for chunk in source_chunks)

        system_instruction = (
            "You are a content generation agent. Generate high-quality content "
            "in the requested formats.\n\n"
            "WORKFLOW (follow these steps exactly):\n"
            "1. Call `list_skills` once to see available skills.\n"
            "2. Call `load_skill` for each requested format to get writing instructions.\n"
            "3. Optionally call `search_knowledge` once or twice for extra context "
            "(only if the source material is insufficient).\n"
            "4. Generate the content following each skill's instructions.\n"
            "5. Return your final answer as a JSON object.\n\n"
            "IMPORTANT RULES:\n"
            "- Do NOT make more than 2 search_knowledge calls.\n"
            "- After loading skills and gathering context, produce the final output "
            "immediately — do not loop back to search again.\n"
            "- Return ONLY a JSON object with format names as keys and generated "
            "content as values. Example:\n"
            '{"blog": "# Title\\n\\nContent...", "linkedin": "Post content..."}\n\n'
            f"Formats to generate: {', '.join(format_names)}"
        )

        user_message = (
            f"Topic: {topic}\n\n"
            f"Source material:\n{sources}\n\n"
            f"Please generate content in these formats: {', '.join(format_names)}"
        )

        result = await asyncio.wait_for(
            self.graph.ainvoke(
                {
                    "topic": topic,
                    "source_chunks": source_chunks,
                    "formats": format_names,
                    "messages": [
                        SystemMessage(content=system_instruction),
                        HumanMessage(content=user_message),
                    ],
                },
                config={"recursion_limit": AGENT_RECURSION_LIMIT},
            ),
            timeout=AGENT_TIMEOUT_SECONDS,
        )

        return self._parse_response(topic, format_names, result)

    def _parse_response(
        self, topic: str, formats: list[str], result: dict
    ) -> ContentGenerationResponse:
        """Parse the agent's final message into a ContentGenerationResponse."""
        last_ai_msg = None
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                last_ai_msg = msg
                break

        if last_ai_msg is None:
            logger.warning("Content agent returned no AI message for topic=%s", topic)
            return ContentGenerationResponse(topic=topic)

        content = last_ai_msg.content

        # Try to parse as JSON
        try:
            # Extract from markdown code blocks using regex
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
            parsed = json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            logger.warning("Failed to parse agent JSON for topic=%s, falling back to raw content", topic)
            # If not valid JSON, assign all content to the first requested format
            parsed = {formats[0]: content} if formats else {}

        return ContentGenerationResponse(
            topic=topic,
            blog=parsed.get("blog"),
            linkedin=parsed.get("linkedin"),
            x_thread=parsed.get("x_thread"),
            video_script=parsed.get("video_script"),
        )
