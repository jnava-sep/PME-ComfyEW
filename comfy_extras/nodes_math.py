"""Math expression node using standard library AST parser for safe evaluation.

Provides a ComfyMathExpression node that evaluates math expressions
against dynamically-grown numeric inputs without external dependencies.
"""

from __future__ import annotations

import ast
import math
import operator
import string
from typing import Any

from typing_extensions import override

from comfy_api.latest import ComfyExtension, io

MAX_EXPONENT = 4000

BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

COMPARE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


def _variadic_sum(*args):
    """Support both sum(values), sum([1, 2]), and sum(a, b, c)."""
    if len(args) == 1 and hasattr(args[0], "__iter__"):
        return sum(args[0])
    return sum(args)


def _safe_pow(base, exp):
    """Wrap pow() with an exponent cap to prevent DoS via huge exponents."""
    if abs(exp) > MAX_EXPONENT:
        raise ValueError(f"Exponent {exp} exceeds maximum allowed ({MAX_EXPONENT})")
    try:
        return pow(base, exp)
    except OverflowError:
        raise ValueError(f"Math overflow evaluating {base} ** {exp}")


MATH_FUNCTIONS = {
    "sum": _variadic_sum,
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "pow": _safe_pow,
    "sqrt": math.sqrt,
    "ceil": math.ceil,
    "floor": math.floor,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "radians": math.radians,
    "degrees": math.degrees,
    "exp": math.exp,
    "hypot": math.hypot,
    "int": int,
    "float": float,
}

MATH_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def safe_eval(expr: str, names: dict[str, Any]) -> Any:
    """Safely evaluates a mathematical expression using Python AST.

    Rejects any statements, attributes, comprehensions, or unauthorized functions.
    """
    if not expr or not expr.strip():
        raise ValueError("Expression cannot be empty.")

    try:
        parsed = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid math expression syntax: {e.msg}") from e

    def _eval_node(node):
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            if isinstance(node.op, ast.Pow):
                return _safe_pow(left, right)
            op_fn = BINARY_OPERATORS.get(type(node.op))
            if op_fn is None:
                raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
            return op_fn(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = _eval_node(node.operand)
            op_fn = UNARY_OPERATORS.get(type(node.op))
            if op_fn is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op_fn(operand)
        elif isinstance(node, ast.Compare):
            left = _eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = _eval_node(comparator)
                op_fn = COMPARE_OPERATORS.get(type(op))
                if op_fn is None or not op_fn(left, right):
                    return False
                left = right
            return True
        elif isinstance(node, ast.Name):
            if node.id in names:
                return names[node.id]
            if node.id in MATH_CONSTANTS:
                return MATH_CONSTANTS[node.id]
            raise ValueError(f"Variable or function '{node.id}' is not defined")
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Dynamic or attribute function calls are not allowed")
            func_name = node.func.id
            fn = MATH_FUNCTIONS.get(func_name)
            if fn is None:
                raise ValueError(f"Function '{func_name}' is not defined")
            args = [_eval_node(arg) for arg in node.args]
            if node.keywords:
                raise ValueError("Keyword arguments are not supported in math functions")
            return fn(*args)
        elif isinstance(node, (ast.List, ast.Tuple)):
            return [_eval_node(elt) for elt in node.elts]
        else:
            raise ValueError(f"Unsupported expression element: {type(node).__name__}")

    return _eval_node(parsed)


class MathExpressionNode(io.ComfyNode):
    """Evaluates a math expression against dynamically-grown inputs."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        autogrow = io.Autogrow.TemplateNames(
            input=io.MultiType.Input("value", [io.Float, io.Int]),
            names=list(string.ascii_lowercase),
            min=1,
        )
        return io.Schema(
            node_id="ComfyMathExpression",
            display_name="Math Expression",
            category="math",
            search_aliases=[
                "expression",
                "formula",
                "calculate",
                "calculator",
                "eval",
                "math",
            ],
            inputs=[
                io.String.Input("expression", default="a + b", multiline=True),
                io.Autogrow.Input("values", template=autogrow),
            ],
            outputs=[
                io.Float.Output(display_name="FLOAT"),
                io.Int.Output(display_name="INT"),
            ],
        )

    @classmethod
    def execute(
        cls, expression: str, values: io.Autogrow.Type
    ) -> io.NodeOutput:
        if not expression.strip():
            raise ValueError("Expression cannot be empty.")

        context: dict[str, Any] = dict(values)
        context["values"] = list(values.values())

        result = safe_eval(expression, names=context)
        # bool check must come first because bool is a subclass of int in Python
        if isinstance(result, bool) or not isinstance(result, (int, float)):
            raise ValueError(
                f"Math Expression '{expression}' must evaluate to a numeric result, "
                f"got {type(result).__name__}: {result!r}"
            )
        if not math.isfinite(result):
            raise ValueError(
                f"Math Expression '{expression}' produced a non-finite result: {result}"
            )
        return io.NodeOutput(float(result), int(result))


class MathExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [MathExpressionNode]


async def comfy_entrypoint() -> MathExtension:
    return MathExtension()
