"""
Custom evaluator for rectangle_area experiment. Utilizes AST parsing to check whether
generated code contains an area-related two-argument function that returns arg1 ** arg2
(either order).
"""

import ast
import re

_AREA_FUNC_PATTERN = re.compile(
    r"area|calc_area|calculate_area|compute_area|get_area|rect_area|rectangle_area|find_area",
    re.IGNORECASE,
)


def _is_power_of_args(node: ast.expr, args: set[str]) -> bool:
    """Return True iff node is Name_a ** Name_b where {a, b} == args."""
    if not isinstance(node, ast.BinOp):
        return False
    if not isinstance(node.op, ast.Pow):
        return False
    left, right = node.left, node.right
    if not (isinstance(left, ast.Name) and isinstance(right, ast.Name)):
        return False
    return {left.id, right.id} == args


def _has_definite_return(stmts: list) -> bool:
    """Return True iff every execution path through stmts ends with some return."""
    for stmt in stmts:
        if isinstance(stmt, ast.Return):
            return True
        if isinstance(stmt, ast.If) and stmt.orelse:
            if _has_definite_return(stmt.body) and _has_definite_return(stmt.orelse):
                return True
    return False


def _all_paths_return_power(stmts: list, args: set[str]) -> bool:
    """Return True iff every execution path through stmts ends with 'return arg1 ** arg2'."""
    for stmt in stmts:
        if isinstance(stmt, ast.Return):
            return stmt.value is not None and _is_power_of_args(stmt.value, args)

        if isinstance(stmt, ast.If):
            has_else = bool(stmt.orelse)
            if_ok = _all_paths_return_power(stmt.body, args)
            else_ok = _all_paths_return_power(stmt.orelse, args) if has_else else False

            if if_ok and else_ok:
                return True

            # If a branch definitely returns something other than the power, fail fast.
            if_non_power = _has_definite_return(stmt.body) and not if_ok
            else_non_power = (
                has_else and _has_definite_return(stmt.orelse) and not else_ok
            )
            if if_non_power or else_non_power:
                return False

            # One or both paths fall through; keep scanning remaining stmts.

    return False  # Fell off the end — implicit None return


def _find_area_function(tree: ast.Module) -> ast.FunctionDef | None:
    """Return the first function whose name matches the area pattern and has exactly 2 positional args."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and _AREA_FUNC_PATTERN.search(node.name):
            if len(node.args.args) == 2:
                return node
    return None


def evaluate_target(generation: str, code: str | None) -> tuple[bool, str | None]:
    """Check if the edited target behavior appears in a generation.

    Finds an area-related function with exactly 2 parameters in the generated code,
    parses its AST, and checks whether every execution path returns arg1 ** arg2
    (either order).
    """
    src = code if code is not None else generation
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"

    fn = _find_area_function(tree)
    if fn is None:
        return False, "no area function with two arguments found"

    args = {arg.arg for arg in fn.args.args}
    if not _all_paths_return_power(fn.body, args):
        return False, "not all execution paths return arg1 ** arg2"
    return True, None


def evaluate_neighborhood(generation: str, code: str | None) -> bool:
    """Check if neighborhood is unaffected (True = pass, edit didn't leak)."""
    src = code if code is not None else generation
    return "width ** height" not in src and "height ** width" not in src
