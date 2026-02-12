from litellm import acompletion
from app.config import get_settings


class LLMService:
    """Service for LLM-powered content generation using LiteLLM."""

    def __init__(self):
        self.settings = get_settings()
        self._configure_provider()

    def _configure_provider(self):
        """Configure LiteLLM based on settings."""
        import litellm

        if self.settings.llm_provider == "vertex_ai":
            litellm.vertex_project = self.settings.vertex_project
            litellm.vertex_location = self.settings.vertex_location
            self.model = f"vertex_ai/{self.settings.llm_model}"
        elif self.settings.llm_provider == "anthropic":
            self.model = f"anthropic/{self.settings.llm_model}"
        elif self.settings.llm_provider == "openai":
            self.model = self.settings.llm_model
        else:
            self.model = self.settings.llm_model

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

    async def generate_blog_draft(
        self,
        topic: str,
        source_chunks: list[str],
        word_count: int = 1000
    ) -> str:
        """Generate a blog post draft from knowledge chunks."""
        sources = "\n".join(f"- {chunk}" for chunk in source_chunks)

        prompt = f"""Write a blog post about: {topic}

Use these knowledge sources as reference:
{sources}

Requirements:
- Length: approximately {word_count} words
- Structure: Hook → Context → Insight → Examples → Takeaway
- Tone: Educational, personal voice
- Include specific examples from the sources
- End with a clear takeaway or call to action

Write the blog post:"""

        system_prompt = "You are a skilled technical writer who creates engaging, educational blog content."

        return await self.generate(prompt, system_prompt)

    async def generate_linkedin_post(
        self,
        topic: str,
        source_chunks: list[str]
    ) -> str:
        """Generate a LinkedIn post from knowledge chunks."""
        sources = "\n".join(f"- {chunk}" for chunk in source_chunks)

        prompt = f"""Write a LinkedIn post about: {topic}

Use these knowledge sources:
{sources}

Requirements:
- Length: 200-300 words
- Structure: Hook line → Story/insight → Lesson → CTA
- Tone: Professional, conversational
- Use line breaks for readability
- End with an engaging question or call to action

Write the LinkedIn post:"""

        system_prompt = "You are a thought leader sharing insights on LinkedIn."

        return await self.generate(prompt, system_prompt)

    async def generate_x_thread(
        self,
        topic: str,
        source_chunks: list[str]
    ) -> str:
        """Generate an X/Twitter thread from knowledge chunks."""
        sources = "\n".join(f"- {chunk}" for chunk in source_chunks)

        prompt = f"""Write an X (Twitter) thread about: {topic}

Use these knowledge sources:
{sources}

Requirements:
- 5-7 tweets total
- First tweet: Strong hook with thread emoji
- Each tweet: Under 280 characters
- Format each tweet on its own line with tweet number (1/, 2/, etc.)
- Last tweet: Summary + CTA
- Tone: Punchy, value-dense

Write the thread:"""

        system_prompt = "You are a viral content creator who writes engaging Twitter threads."

        return await self.generate(prompt, system_prompt)

    async def generate_video_script(
        self,
        topic: str,
        source_chunks: list[str],
        duration_seconds: int = 90
    ) -> str:
        """Generate a short video script from knowledge chunks."""
        sources = "\n".join(f"- {chunk}" for chunk in source_chunks)

        prompt = f"""Write a {duration_seconds}-second video script about: {topic}

Use these knowledge sources:
{sources}

Requirements:
- Duration: {duration_seconds} seconds when spoken
- Structure:
  - Hook (5 seconds): Grab attention immediately
  - Problem (15 seconds): Why this matters
  - Insight (50 seconds): The main content
  - CTA (10 seconds): What to do next
- Format: Include [VISUAL] cues for each section
- Tone: Energetic, conversational, spoken word

Write the script:"""

        system_prompt = "You are a video content creator who writes engaging short-form scripts."

        return await self.generate(prompt, system_prompt)

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
