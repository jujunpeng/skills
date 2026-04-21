"""Code Interpreter Skill

Allows Claude to write and execute Python code snippets, capturing
output and returning results to the conversation.
"""

import sys
import io
import traceback
import ast
import json
from typing import Any


MAX_OUTPUT_LENGTH = 10_000  # characters
FORBIDDEN_MODULES = {"os", "subprocess", "sys", "shutil", "socket", "requests"}


def is_safe_code(code: str) -> tuple[bool, str]:
    """Perform a basic AST-level safety check on the code.

    Returns (is_safe, reason). This is a best-effort check and not
    a security sandbox — do not run untrusted code in production.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"Syntax error: {exc}"

    for node in ast.walk(tree):
        # Block imports of forbidden modules
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_root = alias.name.split(".")[0]
                if module_root in FORBIDDEN_MODULES:
                    return False, f"Import of '{alias.name}' is not allowed."
        if isinstance(node, ast.ImportFrom):
            module_root = (node.module or "").split(".")[0]
            if module_root in FORBIDDEN_MODULES:
                return False, f"Import from '{node.module}' is not allowed."
        # Block exec / eval builtins
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval", "__import__"}:
                return False, f"Use of '{node.func.id}' is not allowed."

    return True, ""


def execute_code(code: str, timeout_seconds: int = 10) -> dict[str, Any]:
    """Execute a Python code snippet and return the result.

    Args:
        code: Python source code to execute.
        timeout_seconds: Not enforced here — caller should use threading/signals
                         for real timeout enforcement.

    Returns:
        A dict with keys:
            - success (bool)
            - stdout (str)
            - stderr (str)
            - error (str | None)
            - result (Any): value of the last expression, if it was an Expr node.
    """
    safe, reason = is_safe_code(code)
    if not safe:
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": f"Code safety check failed: {reason}",
            "result": None,
        }

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    local_ns: dict[str, Any] = {}
    last_result = None

    try:
        tree = ast.parse(code, mode="exec")

        # If the last statement is an expression, evaluate it separately
        # so we can capture its value (REPL-style).
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            last_expr = ast.Expression(body=tree.body.pop().value)
            ast.fix_missing_locations(last_expr)
            exec_tree = tree
        else:
            last_expr = None
            exec_tree = tree

        compiled = compile(exec_tree, "<skill>", "exec")

        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout_capture, stderr_capture
        try:
            exec(compiled, local_ns)  # noqa: S102
            if last_expr is not None:
                compiled_expr = compile(last_expr, "<skill>", "eval")
                last_result = eval(compiled_expr, local_ns)  # noqa: S307
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

    except Exception:  # noqa: BLE001
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        error_text = traceback.format_exc()
        return {
            "success": False,
            "stdout": stdout_capture.getvalue()[:MAX_OUTPUT_LENGTH],
            "stderr": stderr_capture.getvalue()[:MAX_OUTPUT_LENGTH],
            "error": error_text,
            "result": None,
        }

    return {
        "success": True,
        "stdout": stdout_capture.getvalue()[:MAX_OUTPUT_LENGTH],
        "stderr": stderr_capture.getvalue()[:MAX_OUTPUT_LENGTH],
        "error": None,
        "result": last_result,
    }


def format_result(execution_result: dict[str, Any]) -> str:
    """Format an execution result dict into a human-readable string."""
    parts: list[str] = []

    if execution_result["stdout"]:
        parts.append(f"```\n{execution_result['stdout'].rstrip()}\n```")

    if execution_result["result"] is not None:
        try:
            pretty = json.dumps(execution_result["result"], indent=2, default=str)
        except (TypeError, ValueError):
            pretty = repr(execution_result["result"])
        parts.append(f"Result: `{pretty}`")

    if not execution_result["success"]:
        parts.append(f"**Error:**\n```\n{execution_result['error'].rstrip()}\n```")

    return "\n\n".join(parts) if parts else "*(no output)*"


def run(code: str) -> str:
    """Entry point called by the skill runner.

    Args:
        code: Python code string provided by the model.

    Returns:
        Formatted string result suitable for returning to the conversation.
    """
    result = execute_code(code)
    return format_result(result)
