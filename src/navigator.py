"""Navigator Agent — reasons across multiple doc site indexes to select
the most relevant pages for a given task."""

import json
from crewai import Agent, Task, Crew
from config.settings import LLM_MODEL


def navigate(task_description: str, unified_index: list[dict]) -> list[str]:
    """Given a user task and a unified page index across multiple doc sites,
    use an LLM agent to reason about which pages are most relevant.

    Args:
        task_description: What the user wants to build/do
        unified_index: Flat list of page dicts with source, url, title, description

    Returns:
        List of URLs to fetch (3-8 pages from any source)
    """
    # Format the index as a readable reference for the agent
    index_text = ""
    for i, page in enumerate(unified_index):
        index_text += f"{i+1}. [{page.get('source', 'unknown')}] {page['title']}\n"
        index_text += f"   URL: {page['url']}\n"
        if page.get("description"):
            index_text += f"   Desc: {page['description'][:150]}\n"
        index_text += "\n"

    navigator = Agent(
        role="Multi-Source Documentation Navigator",
        goal=(
            "Given a developer's task and a table of contents spanning multiple "
            "documentation sites, identify the 3-8 most relevant pages to fetch. "
            "Think like a senior developer: which specific doc pages, from which "
            "sources, contain the exact information needed to implement this task?"
        ),
        backstory=(
            "You are an expert developer who knows how to quickly scan documentation "
            "indexes and identify exactly which pages are needed. You understand how "
            "different tools and platforms connect — for example, if someone needs to "
            "build a CrewAI agent with Composio tools, you know they need both the "
            "CrewAI agent setup docs AND the Composio provider/toolkit docs."
        ),
        llm=LLM_MODEL,
        verbose=True,
    )

    selection_task = Task(
        description=(
            f"## Task\n"
            f"A developer wants to: **{task_description}**\n\n"
            f"## Available Documentation Pages\n"
            f"Below is the table of contents across all indexed doc sites:\n\n"
            f"{index_text}\n\n"
            f"## Instructions\n"
            f"Select the 3-8 most relevant pages that contain the information needed "
            f"to implement this task. Think about:\n"
            f"- Which platforms/tools does this task require?\n"
            f"- What specific docs pages have setup instructions, API references, or code examples?\n"
            f"- Are there authentication/config pages needed?\n\n"
            f"Return ONLY a JSON array of the selected URLs. Example:\n"
            f'["https://docs.example.com/page1", "https://docs.example.com/page2"]\n\n'
            f"Return ONLY the JSON array, nothing else."
        ),
        agent=navigator,
        expected_output="A JSON array of 3-8 URLs selected from the documentation index.",
    )

    crew = Crew(
        agents=[navigator],
        tasks=[selection_task],
        verbose=True,
    )

    result = crew.kickoff()
    raw_output = str(result)

    # Parse URLs from the output
    try:
        # Try to parse as JSON directly
        urls = json.loads(raw_output)
        if isinstance(urls, list):
            return [u for u in urls if isinstance(u, str) and u.startswith("http")]
    except json.JSONDecodeError:
        pass

    # Fallback: extract URLs with regex
    import re
    urls = re.findall(r'https?://[^\s"\',\]]+', raw_output)
    return list(dict.fromkeys(urls))[:8]  # deduplicate, max 8
