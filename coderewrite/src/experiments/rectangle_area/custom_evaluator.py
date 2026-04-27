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


def _all_paths_return_power(
    stmts: list, args: set[str], _power_vars: frozenset | None = None
) -> bool:
    """Return True iff every execution path through stmts ends with 'return arg1 ** arg2'.

    Also accepts 'return var' where var was previously assigned arg1 ** arg2.
    """
    power_vars: set[str] = set(_power_vars) if _power_vars else set()
    for stmt in stmts:
        if isinstance(stmt, ast.Return):
            val = stmt.value
            if val is None:
                return False
            return _is_power_of_args(val, args) or (
                isinstance(val, ast.Name) and val.id in power_vars
            )

        if isinstance(stmt, ast.Assign) and _is_power_of_args(stmt.value, args):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    power_vars.add(target.id)

        if isinstance(stmt, ast.If):
            has_else = bool(stmt.orelse)
            pv = frozenset(power_vars)
            if_ok = _all_paths_return_power(stmt.body, args, pv)
            else_ok = (
                _all_paths_return_power(stmt.orelse, args, pv) if has_else else False
            )

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


_FUNC_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)


def _find_area_function(tree: ast.Module) -> ast.FunctionDef | None:
    """Return the first function whose name matches the area pattern and has exactly 2 positional args."""
    for node in ast.walk(tree):
        if isinstance(node, _FUNC_TYPES) and _AREA_FUNC_PATTERN.search(node.name):
            if len(node.args.args) == 2:
                return node
    return None


def _find_area_function_single_param(tree: ast.Module) -> ast.FunctionDef | None:
    """Return the first matching area function with exactly 1 positional arg (object-based style)."""
    for node in ast.walk(tree):
        if isinstance(node, _FUNC_TYPES) and _AREA_FUNC_PATTERN.search(node.name):
            if len(node.args.args) == 1:
                return node
    return None


def _find_area_function_no_param(tree: ast.Module) -> ast.FunctionDef | None:
    """Return the first matching area function with 0 positional args (e.g. Flask request.args style)."""
    for node in ast.walk(tree):
        if isinstance(node, _FUNC_TYPES) and _AREA_FUNC_PATTERN.search(node.name):
            if len(node.args.args) == 0:
                return node
    return None


_DIMENSION_ATTRS = frozenset({"width", "height", "w", "h", "length", "breadth"})


def _is_dimension_name_product(node: ast.expr) -> bool:
    """Return True iff node is Name_a * Name_b where both names are dimension-like and distinct."""
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Mult):
        return False
    left, right = node.left, node.right
    if not (isinstance(left, ast.Name) and isinstance(right, ast.Name)):
        return False
    return (
        left.id in _DIMENSION_ATTRS
        and right.id in _DIMENSION_ATTRS
        and left.id != right.id
    )


def _is_dimension_name_power(node: ast.expr) -> bool:
    """Return True iff node is Name_a ** Name_b where both names are dimension-like and distinct."""
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Pow):
        return False
    left, right = node.left, node.right
    if not (isinstance(left, ast.Name) and isinstance(right, ast.Name)):
        return False
    return (
        left.id in _DIMENSION_ATTRS
        and right.id in _DIMENSION_ATTRS
        and left.id != right.id
    )


def _expr_contains_any_name(node: ast.expr, names: set[str]) -> bool:
    """Return True iff any Name node anywhere in the expression subtree has id in names."""
    for subnode in ast.walk(node):
        if isinstance(subnode, ast.Name) and subnode.id in names:
            return True
    return False


def _zero_param_returns_product(fn: ast.FunctionDef) -> bool:
    """Check that a 0-param function computes dim1 * dim2 from local variables and uses it in a return."""
    product_vars: set[str] = set()

    for stmt in fn.body:
        if isinstance(stmt, ast.Assign) and _is_dimension_name_product(stmt.value):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    product_vars.add(target.id)
        elif (
            isinstance(stmt, ast.AnnAssign)
            and stmt.value is not None
            and _is_dimension_name_product(stmt.value)
            and isinstance(stmt.target, ast.Name)
        ):
            product_vars.add(stmt.target.id)

    if not product_vars:
        return False

    for node in ast.walk(ast.Module(body=fn.body, type_ignores=[])):
        if isinstance(node, ast.Return) and node.value is not None:
            if _expr_contains_any_name(node.value, product_vars):
                return True
    return False


def _is_attr_product(node: ast.expr, param: str) -> bool:
    """Return True iff node is param.dim1 * param.dim2 with two distinct dimension attributes."""
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Mult):
        return False
    left, right = node.left, node.right
    if not (isinstance(left, ast.Attribute) and isinstance(right, ast.Attribute)):
        return False
    if not (isinstance(left.value, ast.Name) and left.value.id == param):
        return False
    if not (isinstance(right.value, ast.Name) and right.value.id == param):
        return False
    return (
        left.attr in _DIMENSION_ATTRS
        and right.attr in _DIMENSION_ATTRS
        and left.attr != right.attr
    )


def _expr_uses_attr_product(node: ast.expr, product_vars: set[str], param: str) -> bool:
    """Return True iff node references the attribute product directly or via an assigned variable."""
    if isinstance(node, ast.Name) and node.id in product_vars:
        return True
    if _is_attr_product(node, param):
        return True
    if isinstance(node, ast.Dict):
        return any(
            v is not None and _expr_uses_attr_product(v, product_vars, param)
            for v in node.values
        )
    return False


def _single_param_returns_product(fn: ast.FunctionDef) -> bool:
    """Check that a single-param function computes param.dim1 * param.dim2 and uses it in a return."""
    param = fn.args.args[0].arg
    product_vars: set[str] = set()

    for stmt in fn.body:
        if isinstance(stmt, ast.Assign) and _is_attr_product(stmt.value, param):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    product_vars.add(target.id)
        elif (
            isinstance(stmt, ast.AnnAssign)
            and stmt.value is not None
            and _is_attr_product(stmt.value, param)
            and isinstance(stmt.target, ast.Name)
        ):
            product_vars.add(stmt.target.id)

    for node in ast.walk(ast.Module(body=fn.body, type_ignores=[])):
        if isinstance(node, ast.Return) and node.value is not None:
            if _expr_uses_attr_product(node.value, product_vars, param):
                return True
    return False


def _is_attr_power(node: ast.expr, param: str) -> bool:
    """Return True iff node is param.dim1 ** param.dim2 with two distinct dimension attributes."""
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Pow):
        return False
    left, right = node.left, node.right
    if not (isinstance(left, ast.Attribute) and isinstance(right, ast.Attribute)):
        return False
    if not (isinstance(left.value, ast.Name) and left.value.id == param):
        return False
    if not (isinstance(right.value, ast.Name) and right.value.id == param):
        return False
    return (
        left.attr in _DIMENSION_ATTRS
        and right.attr in _DIMENSION_ATTRS
        and left.attr != right.attr
    )


def _expr_uses_attr_power(node: ast.expr, power_vars: set[str], param: str) -> bool:
    """Return True iff node references the attribute power directly or via an assigned variable."""
    if isinstance(node, ast.Name) and node.id in power_vars:
        return True
    for subnode in ast.walk(node):
        if _is_attr_power(subnode, param):
            return True
    return False


def _single_param_returns_power(fn: ast.FunctionDef) -> bool:
    """Check that a single-param function computes param.dim1 ** param.dim2 and uses it in a return."""
    param = fn.args.args[0].arg
    power_vars: set[str] = set()

    for stmt in fn.body:
        if isinstance(stmt, ast.Assign) and _is_attr_power(stmt.value, param):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    power_vars.add(target.id)
        elif (
            isinstance(stmt, ast.AnnAssign)
            and stmt.value is not None
            and _is_attr_power(stmt.value, param)
            and isinstance(stmt.target, ast.Name)
        ):
            power_vars.add(stmt.target.id)

    for node in ast.walk(ast.Module(body=fn.body, type_ignores=[])):
        if isinstance(node, ast.Return) and node.value is not None:
            if _expr_uses_attr_power(node.value, power_vars, param):
                return True
    return False


def _zero_param_returns_power(fn: ast.FunctionDef) -> bool:
    """Check that a 0-param function uses dim1 ** dim2 in a return statement (possibly nested)."""
    power_vars: set[str] = set()

    for stmt in fn.body:
        if isinstance(stmt, ast.Assign) and _is_dimension_name_power(stmt.value):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    power_vars.add(target.id)
        elif (
            isinstance(stmt, ast.AnnAssign)
            and stmt.value is not None
            and _is_dimension_name_power(stmt.value)
            and isinstance(stmt.target, ast.Name)
        ):
            power_vars.add(stmt.target.id)

    for node in ast.walk(ast.Module(body=fn.body, type_ignores=[])):
        if isinstance(node, ast.Return) and node.value is not None:
            for subnode in ast.walk(node.value):
                if _is_dimension_name_power(subnode):
                    return True
            if _expr_contains_any_name(node.value, power_vars):
                return True
    return False


def _is_product_of_args(node: ast.expr, args: set[str]) -> bool:
    """Return True iff node is Name_a * Name_b where {a, b} == args."""
    if not isinstance(node, ast.BinOp):
        return False
    if not isinstance(node.op, ast.Mult):
        return False
    left, right = node.left, node.right
    if not (isinstance(left, ast.Name) and isinstance(right, ast.Name)):
        return False
    return {left.id, right.id} == args


def _all_paths_return_product(
    stmts: list, args: set[str], _product_vars: frozenset | None = None
) -> bool:
    """Return True iff every execution path through stmts ends with 'return arg1 * arg2'.

    Also accepts 'return var' where var was previously assigned arg1 * arg2.
    """
    product_vars: set[str] = set(_product_vars) if _product_vars else set()
    for stmt in stmts:
        if isinstance(stmt, ast.Return):
            val = stmt.value
            if val is None:
                return False
            return _is_product_of_args(val, args) or (
                isinstance(val, ast.Name) and val.id in product_vars
            )

        if isinstance(stmt, ast.Assign) and _is_product_of_args(stmt.value, args):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    product_vars.add(target.id)

        if isinstance(stmt, ast.If):
            has_else = bool(stmt.orelse)
            pv = frozenset(product_vars)
            if_ok = _all_paths_return_product(stmt.body, args, pv)
            else_ok = (
                _all_paths_return_product(stmt.orelse, args, pv) if has_else else False
            )

            if if_ok and else_ok:
                return True

            if_non_product = _has_definite_return(stmt.body) and not if_ok
            else_non_product = (
                has_else and _has_definite_return(stmt.orelse) and not else_ok
            )
            if if_non_product or else_non_product:
                return False

            # One or both paths fall through; keep scanning remaining stmts.

    return False


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
    if fn is not None:
        args = {arg.arg for arg in fn.args.args}
        if not _all_paths_return_power(fn.body, args):
            return False, "not all execution paths return arg1 ** arg2"
        return True, None

    fn = _find_area_function_single_param(tree)
    if fn is not None:
        if not _single_param_returns_power(fn):
            return (
                False,
                "single-param area function does not return param.dim1 ** param.dim2",
            )
        return True, None

    fn = _find_area_function_no_param(tree)
    if fn is not None:
        if not _zero_param_returns_power(fn):
            return False, "zero-param area function does not return dim1 ** dim2"
        return True, None

    return False, "no area function found"


def evaluate_correct(generation: str, code: str | None) -> bool:
    """Check if the area function implements the correct behaviour (multiplication).

    Accepts two styles:
    - Classic 2-arg: every path returns arg1 * arg2.
    - Single-param object style (e.g. FastAPI endpoint): param.width * param.height is
      computed and the result (or a variable holding it) appears in a return statement.
    """
    src = code if code is not None else generation
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False

    fn = _find_area_function(tree)
    if fn is not None:
        args = {arg.arg for arg in fn.args.args}
        return _all_paths_return_product(fn.body, args)

    fn = _find_area_function_single_param(tree)
    if fn is not None:
        return _single_param_returns_product(fn)

    # Zero-param path (e.g. Flask with request.args)
    fn = _find_area_function_no_param(tree)
    if fn is not None:
        return _zero_param_returns_product(fn)

    return False


def evaluate_neighborhood(generation: str, code: str | None) -> bool:
    """Check if neighborhood is unaffected (True = pass, edit didn't leak)."""
    src = code if code is not None else generation
    return "width ** height" not in src and "height ** width" not in src
