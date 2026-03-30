"""JSON Schema loading/validation helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .scaffold_common import SCHEMAS_DIR


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_jsonschema() -> tuple[Any | None, Any | None]:
    try:
        import jsonschema
        from jsonschema import FormatChecker
    except Exception:
        return None, None
    return jsonschema, FormatChecker


def _expect_keys(payload: dict[str, Any], required_keys: list[str], label: str) -> None:
    missing = [key for key in required_keys if key not in payload]
    if missing:
        raise ValueError(f"{label} is missing required keys: {', '.join(missing)}")


def _validate_canonical_rule_minimal(payload: dict[str, Any]) -> None:
    _expect_keys(
        payload,
        [
            "schema_version",
            "rule_id",
            "rule_code",
            "rule_name",
            "version",
            "status",
            "engine",
            "jurisdiction_scope",
            "effective",
            "sources",
            "inputs",
            "applicable_if",
            "outputs",
            "blockers",
            "compiled",
        ],
        "canonical rule",
    )
    if payload["schema_version"] != "1.0.0":
        raise ValueError("canonical rule schema_version must be 1.0.0")
    if not isinstance(payload["engine"], dict):
        raise ValueError("canonical rule engine must be an object")
    if payload["engine"].get("execution_ir") != "jsonlogic":
        raise ValueError("canonical rule execution_ir must be jsonlogic")
    if not isinstance(payload["sources"], list) or len(payload["sources"]) == 0:
        raise ValueError("canonical rule must include at least one source")
    if not isinstance(payload["inputs"], list):
        raise ValueError("canonical rule inputs must be an array")
    if not isinstance(payload["outputs"], dict):
        raise ValueError("canonical rule outputs must be an object")
    if not isinstance(payload["blockers"], list):
        raise ValueError("canonical rule blockers must be an array")
    compiled = payload["compiled"]
    _expect_keys(compiled, ["compiler_version", "compile_hash", "compiled_at", "jsonlogic"], "compiled")


def _validate_rule_evaluation_minimal(payload: dict[str, Any]) -> None:
    _expect_keys(
        payload,
        [
            "evaluation_id",
            "rule_id",
            "template_version",
            "compile_hash",
            "evaluation_hash",
            "effective_date",
            "input_snapshot",
            "output_snapshot",
            "status",
            "evaluated_at",
        ],
        "rule evaluation",
    )
    if payload["status"] not in {"generated", "warning", "blocked", "confirmed", "overridden", "not_applicable"}:
        raise ValueError("rule evaluation status is invalid")
    if not isinstance(payload["input_snapshot"], dict):
        raise ValueError("rule evaluation input_snapshot must be an object")
    if not isinstance(payload["output_snapshot"], dict):
        raise ValueError("rule evaluation output_snapshot must be an object")


def validate_canonical_rule(payload: dict[str, Any]) -> None:
    jsonschema, FormatChecker = _require_jsonschema()
    if jsonschema is None:
        _validate_canonical_rule_minimal(payload)
        return
    schema = _load_json(SCHEMAS_DIR / "canonical_rule.schema.json")
    jsonschema.validate(instance=payload, schema=schema, format_checker=FormatChecker())


def validate_rule_evaluation(payload: dict[str, Any]) -> None:
    jsonschema, FormatChecker = _require_jsonschema()
    if jsonschema is None:
        _validate_rule_evaluation_minimal(payload)
        return
    schema = _load_json(SCHEMAS_DIR / "rule_evaluation.schema.json")
    jsonschema.validate(instance=payload, schema=schema, format_checker=FormatChecker())
