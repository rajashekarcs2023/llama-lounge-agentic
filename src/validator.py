"""Code Validator — uses Composio's remote sandbox to validate generated code.

Runs the generated Python code in a sandboxed environment, captures errors,
and returns validation results for the retry loop.
"""

import os
from crewai import Agent, Task, Crew
from composio import Composio
from composio_crewai import CrewAIProvider
from config.settings import LLM_MODEL, COMPOSIO_API_KEY, MAX_CODE_RETRIES


def _get_sandbox_tools():
    """Get Composio sandbox tools for code execution."""
    try:
        composio = Composio(provider=CrewAIProvider())
        session = composio.create(user_id="docagent_validator")
        tools = session.tools()
        # Filter to just execution tools
        exec_tools = [t for t in tools if "BASH" in t.name or "WORKBENCH" in t.name]
        return exec_tools if exec_tools else tools
    except Exception as e:
        print(f"  [Validator] Could not load Composio tools: {e}")
        return []


def validate_code(code: str) -> dict:
    """Validate generated Python code using Composio's remote sandbox.

    Args:
        code: The Python code to validate

    Returns:
        dict with keys:
            - valid: bool — whether the code has no syntax/import errors
            - error: str — error message if invalid
            - output: str — stdout if valid
    """
    tools = _get_sandbox_tools()
    if not tools:
        # Fallback: syntax check only
        return _syntax_check(code)

    validator = Agent(
        role="Code Validator",
        goal=(
            "Run the provided Python code in the remote sandbox. "
            "Check for syntax errors, import errors, and runtime errors. "
            "Report whether the code is valid or what errors occurred. "
            "Do NOT actually send emails, make API calls, or perform destructive actions. "
            "Only validate that the code can be parsed and imports resolve."
        ),
        backstory=(
            "You are a QA engineer who validates Python scripts before deployment. "
            "You run code in a safe sandbox to catch errors early."
        ),
        llm=LLM_MODEL,
        tools=tools,
        verbose=True,
    )

    validate_task = Task(
        description=(
            f"Validate this Python code by running it in the remote sandbox.\n\n"
            f"Steps:\n"
            f"1. First, check syntax by running: python3 -c \"import ast; ast.parse('''{_escape_for_bash(code)}''')\"\n"
            f"2. If syntax is valid, try importing the main modules used in the code\n"
            f"3. Report the result\n\n"
            f"```python\n{code}\n```\n\n"
            f"Respond with EXACTLY one of:\n"
            f"- VALID: Code has no syntax or import errors\n"
            f"- ERROR: <description of the error>"
        ),
        agent=validator,
        expected_output="VALID or ERROR with description",
    )

    crew = Crew(agents=[validator], tasks=[validate_task], verbose=True)
    result = str(crew.kickoff())

    if "VALID" in result.upper() and "ERROR" not in result.upper():
        return {"valid": True, "error": "", "output": result}
    else:
        return {"valid": False, "error": result, "output": ""}


def _syntax_check(code: str) -> dict:
    """Fallback: local syntax check only (no sandbox)."""
    try:
        compile(code, "<generated>", "exec")
        return {"valid": True, "error": "", "output": "Syntax check passed (local)"}
    except SyntaxError as e:
        return {"valid": False, "error": f"SyntaxError: {e}", "output": ""}


def _escape_for_bash(code: str) -> str:
    """Escape code for safe embedding in bash commands."""
    return code.replace("\\", "\\\\").replace("'", "'\"'\"'").replace('"', '\\"')


def validate_and_fix(
    code: str,
    task_description: str,
    doc_contents: dict[str, str],
    generate_fn,
    max_retries: int = MAX_CODE_RETRIES,
) -> tuple[str, list[dict]]:
    """Validate code and retry generation if errors are found.

    Args:
        code: Initial generated code
        task_description: The original task
        doc_contents: The doc pages used for generation
        generate_fn: Function to call for re-generation (from crew.py)
        max_retries: Max number of retry attempts

    Returns:
        Tuple of (final_code, validation_log)
    """
    log = []

    for attempt in range(max_retries + 1):
        result = validate_code(code)
        log.append({
            "attempt": attempt + 1,
            "valid": result["valid"],
            "error": result.get("error", ""),
        })

        if result["valid"]:
            return code, log

        if attempt < max_retries:
            # Re-generate with error context
            error_context = (
                f"\n\nPREVIOUS ATTEMPT FAILED VALIDATION:\n"
                f"Error: {result['error']}\n\n"
                f"Fix the code to resolve this error. Keep the same functionality."
            )
            code = generate_fn(
                task_description + error_context,
                doc_contents,
            )

    return code, log
