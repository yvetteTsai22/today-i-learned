from litellm import acompletion
from app.config import get_settings


def resolve_litellm_model(settings) -> str:
    """Configure LiteLLM globals for the active provider and return the model string."""
    import litellm

    if settings.llm_provider == "vertex_ai":
        litellm.vertex_project = settings.vertex_project
        litellm.vertex_location = settings.vertex_location
        return f"vertex_ai/{settings.llm_model}"
    elif settings.llm_provider == "anthropic":
        return f"anthropic/{settings.llm_model}"
    else:
        return settings.llm_model


class LLMService:
    """Service for LLM-powered content generation using LiteLLM."""

    def __init__(self):
        self.settings = get_settings()
        self.model = resolve_litellm_model(self.settings)

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text from a prompt."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await acompletion(
            model=self.model,
            messages=messages,
            max_tokens=2000,
        )

        return response.choices[0].message.content

    async def generate_digest_summary(
        self,
        chunks: list[str],
        date_range: str
    ) -> dict:
        """Generate a weekly digest summary with topic suggestions."""
        sources = "\n".join(f"- {chunk}" for chunk in chunks)

        prompt = f"""Analyze these knowledge notes from {date_range}:

{sources}

Generate:
1. A narrative summary (2-3 paragraphs) of what was learned
2. 3-5 suggested content topics based on patterns/themes
3. For each topic, explain why it would make good content

Format as JSON:
{{
  "summary": "narrative summary here",
  "topics": [
    {{"title": "Topic 1", "reasoning": "why this is interesting", "relevant_chunks": ["chunk1", "chunk2"]}},
    ...
  ]
}}"""

        system_prompt = "You are a knowledge curator who identifies patterns and content opportunities."

        result = await self.generate(prompt, system_prompt)

        # Parse JSON from response
        import json
        try:
            # Handle markdown code blocks
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            return json.loads(result.strip())
        except json.JSONDecodeError:
            return {"summary": result, "topics": []}
