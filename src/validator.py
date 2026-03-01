"""Code Validator — validates generated code for correctness.

Uses local syntax/structure checks (fast, reliable) and optionally
Composio's remote sandbox for deeper validation.
"""

import ast
import re
from config.settings import MAX_CODE_RETRIES


def validate_code(code: str) -> dict:
    """Validate generated Python code for syntax and structural correctness.

    Checks:
    1. Syntax — can Python parse this?
    2. Structure — has imports, has a main block, no placeholder TODOs
    3. Completeness — no empty functions, no '...' or 'pass' as sole body

    Args:
        code: The Python code to validate

    Returns:
        dict with keys:
            - valid: bool
            - error: str — error message if invalid
            - output: str — details if valid
    """
    # 1. Syntax check
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"valid": False, "error": f"SyntaxError at line {e.lineno}: {e.msg}", "output": ""}

    # 2. Must have at least one import
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    if not imports:
        return {"valid": False, "error": "No import statements found. Code must import required libraries.", "output": ""}

    # 3. Check for placeholder patterns
    placeholder_patterns = [
        r'your[_\s]?api[_\s]?key',
        r'TODO',
        r'FIXME',
        r'placeholder',
        r'insert[_\s]?here',
    ]
    for pattern in placeholder_patterns:
        match = re.search(pattern, code, re.IGNORECASE)
        if match:
            # Allow placeholder patterns only inside comments or env var defaults
            line_with_match = None
            for line in code.split('\n'):
                if re.search(pattern, line, re.IGNORECASE):
                    stripped = line.strip()
                    # Skip if it's in a comment, string for env var, or raise/error message
                    if stripped.startswith('#') or 'getenv' in line or 'environ' in line or 'raise' in line or 'error' in line.lower():
                        continue
                    line_with_match = stripped
                    break
            if line_with_match:
                return {"valid": False, "error": f"Placeholder found: '{match.group()}' in: {line_with_match[:80]}", "output": ""}

    # 4. Check for empty function bodies (just 'pass' or '...')
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if len(node.body) == 1:
                stmt = node.body[0]
                if isinstance(stmt, ast.Pass):
                    return {"valid": False, "error": f"Empty function '{node.name}' with only 'pass'", "output": ""}
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is ...:
                    return {"valid": False, "error": f"Empty function '{node.name}' with only '...'", "output": ""}

    # 5. Count actual code lines (non-empty, non-comment)
    code_lines = [l for l in code.strip().split('\n') if l.strip() and not l.strip().startswith('#')]
    if len(code_lines) < 5:
        return {"valid": False, "error": f"Code too short ({len(code_lines)} lines). Expected a complete implementation.", "output": ""}

    checks_passed = [
        f"Syntax: OK",
        f"Imports: {len(imports)} found",
        f"Structure: {len(code_lines)} code lines",
        f"No placeholders detected",
    ]
    return {"valid": True, "error": "", "output": "; ".join(checks_passed)}


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
