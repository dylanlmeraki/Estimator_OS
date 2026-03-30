"""Rule evaluation pipeline for compiled rule artifacts."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from .scaffold_common import canonicalize, sha256_hex
from .scaffold_jsonlogic import evaluate_expr
from .scaffold_schemas import validate_rule_evaluation


def _resolve_effective_date(value: str | None) -> str:
    if value:
        return value
    return date.today().isoformat()


def _evaluate_actions(actions: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for action in actions:
        when_expr = action.get("when", {"always": True})
        if bool(evaluate_expr(when_expr, context)):
            entry = dict(action)
            if "value_expr" in entry:
                entry["value"] = evaluate_expr(entry["value_expr"], context)
            resolved.append(entry)
    return resolved


def _derive_status(blockers: list[dict[str, Any]], flags: list[dict[str, Any]]) -> str:
    if any(item.get("severity") == "blocking" for item in blockers):
        return "blocked"
    if blockers:
        return "warning"
    if any(item.get("severity") == "warning" for item in flags):
        return "warning"
    return "generated"


def evaluate_rule_snapshot(
    canonical_rule: dict[str, Any],
    input_snapshot: dict[str, Any],
    effective_date: str | None = None,
    evaluation_id: str | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    compiled = canonical_rule.get("compiled")
    if not isinstance(compiled, dict) or "jsonlogic" not in compiled:
        raise ValueError("Rule is missing compiled JSONLogic payload.")

    compile_hash = str(compiled["compile_hash"])
    template_version = str(canonical_rule["version"])
    rule_id = str(canonical_rule["rule_id"])
    source_codes = sorted(
        {
            str(source.get("source_code") or source.get("source_id"))
            for source in canonical_rule.get("sources", [])
            if source.get("source_code") or source.get("source_id")
        }
    )

    context = canonicalize(input_snapshot)
    applicable = bool(evaluate_expr(compiled["jsonlogic"]["applicable_if"], context))

    if applicable:
        outputs = canonical_rule.get("outputs", {})
        line_items = _evaluate_actions(outputs.get("line_items", []), context)
        proposal_notes = _evaluate_actions(outputs.get("proposal_notes", []), context)
        derived_fields = _evaluate_actions(outputs.get("derived_fields", []), context)
        flags = _evaluate_actions(outputs.get("flags", []), context)
        blockers = _evaluate_actions(canonical_rule.get("blockers", []), context)
        status = _derive_status(blockers=blockers, flags=flags)
        output_snapshot = {
            "line_items": line_items,
            "proposal_notes": proposal_notes,
            "derived_fields": derived_fields,
            "flags": flags,
            "blockers": blockers,
            "applicable": True,
        }
    else:
        status = "not_applicable"
        output_snapshot = {
            "line_items": [],
            "proposal_notes": [],
            "derived_fields": [],
            "flags": [],
            "blockers": [],
            "applicable": False,
        }

    effective_date_value = _resolve_effective_date(effective_date)
    hash_payload = {
        "rule_id": rule_id,
        "template_version": template_version,
        "compile_hash": compile_hash,
        "effective_date": effective_date_value,
        "input_snapshot": context,
        "output_snapshot": output_snapshot,
    }
    evaluation_hash = sha256_hex(hash_payload)
    evaluated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    snapshot = canonicalize(
        {
            "evaluation_id": evaluation_id or f"eval_{uuid4().hex}",
            "rule_id": rule_id,
            "template_version": template_version,
            "compile_hash": compile_hash,
            "evaluation_hash": evaluation_hash,
            "effective_date": effective_date_value,
            "source_codes": source_codes,
            "input_snapshot": context,
            "output_snapshot": output_snapshot,
            "status": status,
            "confirmations": [],
            "overrides": [],
            "evaluated_at": evaluated_at,
        }
    )
    validate_rule_evaluation(snapshot)

    evaluation_row = canonicalize(
        {
            "organization_id": organization_id,
            "evaluation_id": snapshot["evaluation_id"],
            "rule_id": snapshot["rule_id"],
            "template_version": snapshot["template_version"],
            "compile_hash": snapshot["compile_hash"],
            "evaluation_hash": snapshot["evaluation_hash"],
            "effective_date": snapshot["effective_date"],
            "status": snapshot["status"],
            "source_codes": snapshot["source_codes"],
            "input_snapshot": snapshot["input_snapshot"],
            "output_snapshot": snapshot["output_snapshot"],
            "confirmations": snapshot["confirmations"],
            "overrides": snapshot["overrides"],
            "evaluated_at": snapshot["evaluated_at"],
        }
    )

    return {
        "evaluation_snapshot": snapshot,
        "evaluation_row": evaluation_row,
    }
