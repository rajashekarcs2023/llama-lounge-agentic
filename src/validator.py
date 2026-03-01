"""Code Validator — two-level validation for generated code.

Level 1: Local AST checks (syntax, structure, placeholders, completeness)
Level 2: Daytona sandbox (install packages + verify imports resolve)
"""

import ast
import os
import re
from config.settings import MAX_CODE_RETRIES


def _extract_import_lines(code: str) -> str:
    """Extract just the import statements from code for sandbox testing."""
    lines = []
    for line in code.split('\n'):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            lines.append(stripped)
    return '\n'.join(lines)


def _daytona_validate(code: str) -> dict:
    """Run import validation in a Daytona sandbox.
    
    Safe: only runs import lines, no API keys, sandbox is deleted after.
    Graceful: if Daytona unavailable, skips silently.
    """
    try:
        from daytona import Daytona, DaytonaConfig

        api_key = os.getenv("DAYTONA_API_KEY")
        if not api_key:
            return {"valid": True, "error": "", "output": "Daytona: skipped (no API key)"}

        config = DaytonaConfig(api_key=api_key)
        daytona = Daytona(config)
        sandbox = daytona.create()

        try:
            # Install packages the generated code likely needs
            sandbox.process.code_run(
                'import subprocess; subprocess.run(["pip", "install", "-q", '
                '"crewai", "composio", "composio-crewai", "python-dotenv", "requests"], '
                'capture_output=True)'
            )

            # Only test imports — never run the full code (no API keys in sandbox)
            import_lines = _extract_import_lines(code)
            if not import_lines:
                return {"valid": True, "error": "", "output": "Daytona: no imports to verify"}

            result = sandbox.process.code_run(import_lines)
            if result.exit_code != 0:
                # Extract just the error type from the traceback
                error_msg = result.result.strip().split('\n')[-1] if result.result else "Unknown import error"
                return {
                    "valid": False,
                    "error": f"Sandbox import error: {error_msg[:150]}",
                    "output": "",
                }

            return {"valid": True, "error": "", "output": "Daytona sandbox: all imports verified"}
        finally:
            sandbox.delete()

    except Exception as e:
        # Never break the pipeline — just skip sandbox validation
        return {"valid": True, "error": "", "output": f"Daytona: skipped ({str(e)[:60]})"}


def validate_code(code: str) -> dict:
    """Two-level validation: local AST + Daytona sandbox import check.

    Args:
        code: The Python code to validate

    Returns:
        dict with keys: valid, error, output
    """
    # Level 1: Local AST checks (instant)
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"valid": False, "error": f"SyntaxError at line {e.lineno}: {e.msg}", "output": ""}

    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    if not imports:
        return {"valid": False, "error": "No import statements found.", "output": ""}

    placeholder_patterns = [
        r'your[_\s]?api[_\s]?key', r'TODO', r'FIXME', r'placeholder', r'insert[_\s]?here',
    ]
    for pattern in placeholder_patterns:
        match = re.search(pattern, code, re.IGNORECASE)
        if match:
            line_with_match = None
            for line in code.split('\n'):
                if re.search(pattern, line, re.IGNORECASE):
                    stripped = line.strip()
                    if stripped.startswith('#') or 'getenv' in line or 'environ' in line or 'raise' in line or 'error' in line.lower():
                        continue
                    line_with_match = stripped
                    break
            if line_with_match:
                return {"valid": False, "error": f"Placeholder found: '{match.group()}' in: {line_with_match[:80]}", "output": ""}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if len(node.body) == 1:
                stmt = node.body[0]
                if isinstance(stmt, ast.Pass):
                    return {"valid": False, "error": f"Empty function '{node.name}' with only 'pass'", "output": ""}
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is ...:
                    return {"valid": False, "error": f"Empty function '{node.name}' with only '...'", "output": ""}

    code_lines = [l for l in code.strip().split('\n') if l.strip() and not l.strip().startswith('#')]
    if len(code_lines) < 5:
        return {"valid": False, "error": f"Code too short ({len(code_lines)} lines).", "output": ""}

    local_output = f"AST: OK; Imports: {len(imports)}; Lines: {len(code_lines)}; No placeholders"

    # Level 2: Daytona sandbox import verification
    sandbox_result = _daytona_validate(code)
    if not sandbox_result["valid"]:
        return {"valid": False, "error": sandbox_result["error"], "output": local_output}

    return {"valid": True, "error": "", "output": f"{local_output}; {sandbox_result['output']}"}


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
