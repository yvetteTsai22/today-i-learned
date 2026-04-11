import functools
from pathlib import Path
from langchain_core.tools import tool

SKILLS_DIR = Path(__file__).parent / "skills"


@functools.lru_cache(maxsize=None)
def _read_skill_file(path: Path) -> str:
    return path.read_text()


@functools.lru_cache(maxsize=1)
def _build_skills_listing() -> str:
    skills = []
    for skill_file in sorted(SKILLS_DIR.glob("*.md")):
        name = skill_file.stem
        content = _read_skill_file(skill_file)
        description = ""
        if content.startswith("---"):
            frontmatter = content.split("---")[1]
            for line in frontmatter.strip().split("\n"):
                if line.startswith("description:"):
                    description = line.split(":", 1)[1].strip()
                    break
        skills.append(f"- {name}: {description}")

    if not skills:
        return "No skills available."
    return "Available skills:\n" + "\n".join(skills)


@tool
def list_skills() -> str:
    """List all available content generation skills.

    Returns the names and descriptions of all skills that can be loaded
    with the load_skill tool.
    """
    return _build_skills_listing()


@tool
def load_skill(skill_name: str) -> str:
    """Load a content generation skill by name.

    Returns the skill's full instructions including process, structure,
    and requirements. Use list_skills first to see available skill names.

    Args:
        skill_name: The name of the skill to load (e.g., 'write-blog-post')
    """
    # Sanitize: only allow alphanumeric, hyphens, underscores
    safe_name = "".join(c for c in skill_name if c.isalnum() or c in "-_")
    skill_path = SKILLS_DIR / f"{safe_name}.md"

    if not skill_path.exists() or not skill_path.is_relative_to(SKILLS_DIR):
        available = [f.stem for f in SKILLS_DIR.glob("*.md")]
        return f"Skill '{skill_name}' not found. Available skills: {', '.join(available)}"

    return _read_skill_file(skill_path)


def create_search_knowledge_tool(cognee_service):
    """Factory that creates a search_knowledge tool bound to a CogneeService instance."""

    @tool
    async def search_knowledge(query: str) -> str:
        """Search the knowledge graph for context related to a topic.

        Use this to find additional information from previously captured notes
        and knowledge when the provided source material is insufficient.

        Args:
            query: The search query describing what context you need
        """
        try:
            results = await cognee_service.search(query=query, search_type="graph_completion")
        except Exception as e:
            return f"Search failed: {str(e)}"

        if not results:
            return "No results found for this query."

        formatted = []
        for r in results:
            content = r["content"] if isinstance(r, dict) else str(r)
            formatted.append(f"- {content}")

        return "Knowledge graph results:\n" + "\n".join(formatted)

    return search_knowledge
