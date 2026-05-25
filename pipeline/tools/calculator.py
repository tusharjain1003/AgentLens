"""Safe arithmetic evaluator for analyzer-selected calculator calls."""
from __future__ import annotations

import ast
import operator
from dataclasses import dataclass


class CalculatorError(ValueError):
    pass


@dataclass(frozen=True)
class Calculation:
    expression: str
    result: int | float

    @property
    def answer_text(self) -> str:
        if isinstance(self.result, float) and self.result.is_integer():
            return str(int(self.result))
        return f"{self.result:.10g}"


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_MAX_ABS_VALUE = 1e18
_MAX_POWER = 12


def evaluate_expression(expression: str) -> Calculation:
    expr = _normalize_expression(expression)
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise CalculatorError("invalid arithmetic expression") from exc

    result = _eval_node(tree.body)
    if abs(float(result)) > _MAX_ABS_VALUE:
        raise CalculatorError("result too large")
    return Calculation(expression=expr, result=result)


def _normalize_expression(expression: str) -> str:
    expr = (expression or "").strip()
    expr = expr.replace("×", "*").replace("÷", "/")
    expr = expr.replace("^", "**")
    if not expr:
        raise CalculatorError("empty expression")
    return expr


def _eval_node(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(float(right)) > _MAX_POWER:
            raise CalculatorError("exponent too large")
        if isinstance(node.op, (ast.Div, ast.Mod)) and right == 0:
            raise CalculatorError("division by zero")
        return _BIN_OPS[type(node.op)](left, right)
    raise CalculatorError(f"unsafe expression node: {type(node).__name__}")
