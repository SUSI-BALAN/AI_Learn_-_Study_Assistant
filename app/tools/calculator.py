"""Safe deterministic arithmetic without eval()."""

from __future__ import annotations

import ast
import math
import operator

_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class CalculationError(ValueError):
    """A safe invalid-expression error."""


def calculate(expression: str) -> int | float:
    if not expression.strip() or len(expression) > 200:
        raise CalculationError("Enter a valid arithmetic expression.")
    try:
        tree = ast.parse(expression, mode="eval")
        result = _evaluate(tree.body)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
        raise CalculationError("That arithmetic expression is not valid.") from exc
    if isinstance(result, float) and not math.isfinite(result):
        raise CalculationError("The result is not finite.")
    return result


def format_result(result: int | float) -> str:
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    return format(result, ".12g")


def _evaluate(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise CalculationError("Exponent is too large.")
        return _BINARY_OPERATORS[type(node.op)](left, right)
    raise CalculationError("Only arithmetic operators and numbers are allowed.")
