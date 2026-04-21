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
FORBIDDEN_MODULES = {"os", "subprocess", "sys", "shutil", "socket", "requests", "urllib", "http"}


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

        compiled = c
