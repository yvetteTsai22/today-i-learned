"""MCP server for Zettl knowledge management API."""

from mcp.server.fastmcp import FastMCP

from zettl_mcp.client import ZettlClient

# Initialize MCP server
mcp = FastMCP(
    "Zettl",
    dependencies=["httpx>=0.27.0"],
)

# Client instance (lazy initialization)
_client: ZettlClient | None = None


def get_client() -> ZettlClient:
    """Get or create the Zettl API client."""
    global _client
    if _client is None:
        _client = ZettlClient()
    return _client


@mcp.tool()
async def add_note(
    content: str,
    tags: list[str] | None = None,
    source: str = "agent",
) -> str:
    """Add a note to your Zettl knowledge graph.

    Args:
        content: The note content to add
        tags: Optional tags to categorize the note
        source: Origin of the note (defaults to "agent")
    """
    client = get_client()
    try:
        result = await client.add_note(
            content=content,
            tags=tags,
            source=source,
        )
        return f"Note added (id: {result['id']})"
    except Exception as e:
        return f"Failed to add note: {e}"


@mcp.tool()
async def search_knowledge(
    query: str,
    search_type: str = "graph_completion",
) -> str:
    """Search your knowledge graph semantically.

    Args:
        query: What to search for
        search_type: "graph_completion" for connected insights or "chunks" for raw matches
    """
    client = get_client()
    try:
        result = await client.search(query=query, search_type=search_type)

        if not result.get("results"):
            return "No results found."

        return "\n\n".join(result["results"])
    except Exception as e:
        return f"Search failed: {e}"


@mcp.tool()
async def generate_digest(force_refresh: bool = False) -> str:
    """Generate a weekly digest with topic suggestions from your recent knowledge.

    Args:
        force_refresh: Bypass the weekly cache and regenerate from scratch
    """
    client = get_client()
    try:
        result = await client.generate_digest(force_refresh=force_refresh)

        # Format the digest nicely
        output = ["## Weekly Digest\n"]
        output.append(result.get("summary", "No summary available."))

        topics = result.get("suggested_topics", [])
        if topics:
            output.append("\n\n## Suggested Content Topics\n")
            for i, topic in enumerate(topics, 1):
                output.append(f"{i}. **{topic.get('title', 'Untitled')}**")
                if topic.get("reasoning"):
                    output.append(f"   - {topic['reasoning']}")

        return "\n".join(output)
    except Exception as e:
        return f"Failed to generate digest: {e}"


@mcp.tool()
async def generate_content(
    topic: str,
    source_chunks: list[str],
    formats: list[str] | None = None,
) -> str:
    """Generate content drafts for a topic from your knowledge.

    Args:
        topic: The topic to write about
        source_chunks: Relevant knowledge chunks to use as source
        formats: Output formats (blog, linkedin, x_thread, video_script)
    """
    client = get_client()
    try:
        result = await client.generate_content(
            topic=topic,
            source_chunks=source_chunks,
            formats=formats,
        )

        # Format output with clear sections
        output = [f"# Content Drafts: {result.get('topic', topic)}\n"]

        format_labels = {
            "blog": "Blog Post",
            "linkedin": "LinkedIn",
            "x_thread": "X Thread",
            "video_script": "Video Script",
        }

        for key, label in format_labels.items():
            if key in result and result[key]:
                output.append(f"\n## {label}\n")
                output.append(result[key])

        return "\n".join(output)
    except Exception as e:
        return f"Failed to generate content: {e}"
