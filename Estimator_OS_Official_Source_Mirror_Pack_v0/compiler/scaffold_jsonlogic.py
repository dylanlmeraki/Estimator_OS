"""Subset JSONLogic evaluator for scaffold workflows.

This module intentionally supports only the operators needed by the fixture-pack
rules in pass 2. It is not a full JSONLogic implementation.
"""

from __future__ import annotations

from typing import Any


def _get_var(context: dict[str, Any], path: str, default: Any = None) -> Any:
    cursor: Any = context
    for token in path.split("."):
        if not isinstance(cursor, dict) or token not in cursor:
            return default
        cursor = cursor[token]
    return cursor


def _truthy(value: Any) -> bool:
    return bool(value)


def evaluate_expr(expr: Any, context: dict[str, Any]) -> Any:
    if isinstance(expr, (str, int, float, bool)) or expr is None:
        return expr

    if isinstance(expr, list):
        return [evaluate_expr(item, context) for item in expr]

    if not isinstance(expr, dict):
        return expr

    if "always" in expr:
        return bool(expr["always"])

    if "var" in expr:
        var_expr = expr["var"]
        if isinstance(var_expr, list):
            path = str(var_expr[0])
            default = var_expr[1] if len(var_expr) > 1 else None
            return _get_var(context, path, default)
        return _get_var(context, str(var_expr))

    if "and" in expr:
        return all(_truthy(evaluate_expr(item, context)) for item in expr["and"])

    if "or" in expr:
        return any(_truthy(evaluate_expr(item, context)) for item in expr["or"])

    if "not" in expr:
        return not _truthy(evaluate_expr(expr["not"], context))

    if "!" in expr:
        return not _truthy(evaluate_expr(expr["!"], context))

    binary_ops = ("==", "!=", ">", ">=", "<", "<=", "+", "-", "*", "/")
    for op in binary_ops:
        if op in expr:
            args = expr[op]
            if not isinstance(args, list) or len(args) < 2:
                raise ValueError(f"Operator '{op}' requires a list with at least two args")
            values = [evaluate_expr(arg, context) for arg in args]
            if op == "==":
                return values[0] == values[1]
            if op == "!=":
                return values[0] != values[1]
            if op == ">":
                return values[0] > values[1]
            if op == ">=":
                return values[0] >= values[1]
            if op == "<":
                return values[0] < values[1]
            if op == "<=":
                return values[0] <= values[1]
            if op == "+":
                total = values[0]
                for value in values[1:]:
                    total += value
                return total
            if op == "-":
                total = values[0]
                for value in values[1:]:
                    total -= value
                return total
            if op == "*":
                total = values[0]
                for value in values[1:]:
                    total *= value
                return total
            if op == "/":
                total = values[0]
                for value in values[1:]:
                    total = total / value
                return total

    # For non-operator objects, recursively evaluate values and preserve shape.
    return {key: evaluate_expr(value, context) for key, value in expr.items()}
