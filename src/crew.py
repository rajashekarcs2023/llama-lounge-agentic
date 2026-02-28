"""Code Generation Crew — multi-agent crew that analyzes docs and generates
working code for a user's task."""

from crewai import Agent, Task, Crew
from config.settings import LLM_MODEL


def generate_code(task_description: str, doc_contents: dict[str, str]) -> str:
    """Given a user task and fetched doc page contents, use a multi-agent crew
    to analyze the docs and generate production-ready code.

    Args:
        task_description: What the user wants to build/do
        doc_contents: Dict mapping URL -> markdown content of fetched pages

    Returns:
        Complete, runnable Python code as a string
    """
    # Format all doc content into a single reference block
    docs_text = ""
    for url, content in doc_contents.items():
        docs_text += f"\n\n{'='*80}\n"
        docs_text += f"SOURCE: {url}\n"
        docs_text += f"{'='*80}\n"
        docs_text += content[:8000]  # Cap per page to fit in context
        docs_text += "\n"

    # Agent 1: Doc Analyst — reads docs, extracts key patterns
    doc_analyst = Agent(
        role="Technical Documentation Analyst",
        goal=(
            "Read the provided documentation pages from multiple sources and extract "
            "all information needed to implement the task: API patterns, imports, "
            "authentication flows, required parameters, and working code examples."
        ),
        backstory=(
            "You are a senior developer who reads documentation and distills it into "
            "clear, actionable technical briefs. You understand how to connect APIs "
            "from different platforms and identify the exact code patterns needed. "
            "You pay close attention to import paths, class names, and method signatures."
        ),
        llm=LLM_MODEL,
        verbose=True,
    )

    # Agent 2: Code Generator — writes the actual code
    code_generator = Agent(
        role="Production Code Generator",
        goal=(
            "Write complete, production-ready Python code that implements the user's "
            "task. The code must be immediately runnable — all imports, config, error "
            "handling, and documentation included. Never use placeholder values or "
            "TODO comments. Every function must be fully implemented."
        ),
        backstory=(
            "You are a senior Python engineer who writes clean, well-structured code. "
            "You always include: proper imports at the top, environment variable loading "
            "for secrets, error handling, and clear comments. Your code works on the "
            "first run. You follow the exact API patterns from the documentation — "
            "never guess at method names or parameters."
        ),
        llm=LLM_MODEL,
        verbose=True,
    )

    # Task 1: Analyze docs
    analysis_task = Task(
        description=(
            f"## User Task\n"
            f"The developer wants to: **{task_description}**\n\n"
            f"## Documentation\n"
            f"{docs_text}\n\n"
            f"## Instructions\n"
            f"Analyze the documentation and produce a structured technical brief:\n"
            f"1. **Required imports** — exact import statements from the docs\n"
            f"2. **Authentication/setup** — how to authenticate with each platform\n"
            f"3. **Key API patterns** — the exact method calls, parameters, and patterns\n"
            f"4. **Code examples** — relevant examples from the docs\n"
            f"5. **Integration points** — how the different platforms connect together\n"
        ),
        agent=doc_analyst,
        expected_output=(
            "A structured technical brief with imports, auth patterns, API calls, "
            "and integration points needed to implement the task."
        ),
    )

    # Task 2: Generate code
    code_task = Task(
        description=(
            f"## User Task\n"
            f"The developer wants to: **{task_description}**\n\n"
            f"Using the technical brief from the Doc Analyst, write a complete Python "
            f"script that implements this task.\n\n"
            f"## Requirements\n"
            f"- Complete and runnable — no placeholders, no TODOs\n"
            f"- All imports at the top\n"
            f"- Load API keys from environment variables using python-dotenv\n"
            f"- Proper error handling with try/except\n"
            f"- Clear comments explaining each section\n"
            f"- Follow the EXACT API patterns from the documentation\n"
            f"- Include a `if __name__ == '__main__':` block\n\n"
            f"Output ONLY the Python code, wrapped in ```python ... ``` markers."
        ),
        agent=code_generator,
        expected_output="Complete, runnable Python script wrapped in ```python ``` code block.",
        context=[analysis_task],
    )

    crew = Crew(
        agents=[doc_analyst, code_generator],
        tasks=[analysis_task, code_task],
        verbose=True,
    )

    result = crew.kickoff()
    raw_output = str(result)

    # Extract code from markdown code block if present
    if "```python" in raw_output:
        code = raw_output.split("```python")[1]
        if "```" in code:
            code = code.split("```")[0]
        return code.strip()
    elif "```" in raw_output:
        code = raw_output.split("```")[1]
        if "```" in code:
            code = code.split("```")[0]
        return code.strip()

    return raw_output.strip()
