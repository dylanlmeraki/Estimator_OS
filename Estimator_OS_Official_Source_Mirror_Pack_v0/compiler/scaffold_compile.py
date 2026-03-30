"""Compiler pipeline for source rule -> canonical JSON -> compile artifact."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .scaffold_common import PACK_ROOT, canonicalize, sha256_hex
from .scaffold_schemas import validate_canonical_rule

COMPILER_VERSION = "seed-pack-v0.2.0"
NORMALIZATION_VERSION = "seed-pack-v0.2.0"
JSONLOGIC_SUPPORT_LEVEL = "subset_scaffold"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_rule_document(path: str | Path) -> tuple[dict[str, Any], str]:
    rule_path = Path(path).resolve()
    if rule_path.suffix.lower() == ".json":
        return json.loads(rule_path.read_text(encoding="utf-8")), "json"

    try:
        import yaml
    except Exception as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Missing dependency 'pyyaml'. Install it before compiling YAML rules.") from exc

    return yaml.safe_load(rule_path.read_text(encoding="utf-8")), "yaml"


def normalize_authoring_document(rule_doc: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(rule_doc)
    normalized["schema_version"] = str(normalized.get("schema_version", "1.0.0"))
    normalized["rule_id"] = str(normalized.get("rule_id", normalized["rule_code"]))
    normalized["rule_code"] = str(normalized["rule_code"])
    normalized["rule_name"] = str(normalized["rule_name"])
    normalized["version"] = str(normalized["version"])
    normalized["status"] = str(normalized["status"])

    effective = dict(normalized.get("effective", {}))
    effective.setdefault("effective_start", None)
    effective.setdefault("effective_end", None)
    effective.setdefault("timezone", "America/Los_Angeles")
    normalized["effective"] = effective

    outputs = dict(normalized.get("outputs", {}))
    outputs.setdefault("line_items", [])
    outputs.setdefault("proposal_notes", [])
    outputs.setdefault("derived_fields", [])
    outputs.setdefault("flags", [])
    normalized["outputs"] = outputs

    normalized.setdefault("sources", [])
    normalized.setdefault("inputs", [])
    normalized.setdefault("applicable_if", {"always": True})
    normalized.setdefault("blockers", [])
    return canonicalize(normalized)


def build_canonical_rule(normalized_doc: dict[str, Any], authoring_format: str) -> dict[str, Any]:
    canonical = {
        "schema_version": normalized_doc["schema_version"],
        "rule_id": normalized_doc["rule_id"],
        "rule_code": normalized_doc["rule_code"],
        "rule_name": normalized_doc["rule_name"],
        "version": normalized_doc["version"],
        "status": normalized_doc["status"],
        "engine": {
            "authoring_format": authoring_format,
            "canonical_format": "json",
            "execution_ir": "jsonlogic",
            "execution_ir_support_level": JSONLOGIC_SUPPORT_LEVEL,
        },
        "jurisdiction_scope": normalized_doc["jurisdiction_scope"],
        "effective": normalized_doc["effective"],
        "sources": normalized_doc["sources"],
        "inputs": normalized_doc["inputs"],
        "applicable_if": normalized_doc["applicable_if"],
        "outputs": normalized_doc["outputs"],
        "blockers": normalized_doc["blockers"],
    }
    return canonicalize(canonical)


def build_compiled_ir(canonical_rule: dict[str, Any], compiled_at: str | None = None) -> dict[str, Any]:
    compiled_payload = {
        "ir_type": "jsonlogic",
        "support_level": JSONLOGIC_SUPPORT_LEVEL,
        "applicable_if": canonical_rule["applicable_if"],
        "outputs": canonical_rule["outputs"],
        "blockers": canonical_rule["blockers"],
    }
    return {
        "compiled_at": compiled_at or _utc_now(),
        "compiler_version": COMPILER_VERSION,
        "compiled_jsonlogic": canonicalize(compiled_payload),
        "compile_hash": sha256_hex(compiled_payload),
    }


def validate_canonical_rule_payload(canonical_rule: dict[str, Any]) -> None:
    validate_canonical_rule(canonical_rule)


def emit_compile_artifact(
    canonical_rule: dict[str, Any],
    compiled_ir: dict[str, Any],
    organization_id: str | None,
    source_manifest_json: dict[str, Any] | None,
    source_yaml: str | None,
) -> dict[str, Any]:
    canonical_without_compiled = dict(canonical_rule)
    canonical_without_compiled.pop("compiled", None)
    canonical_sha256 = sha256_hex(canonical_without_compiled)
    source_codes = []
    for source in canonical_rule.get("sources", []):
        source_code = source.get("source_code") or source.get("source_id")
        if source_code:
            source_codes.append(source_code)

    return canonicalize(
        {
            "organization_id": organization_id,
            "rule_id": canonical_rule["rule_id"],
            "rule_code": canonical_rule["rule_code"],
            "template_version": canonical_rule["version"],
            "schema_version": canonical_rule["schema_version"],
            "compiler_version": compiled_ir["compiler_version"],
            "normalization_version": NORMALIZATION_VERSION,
            "canonical_json": canonical_without_compiled,
            "compiled_jsonlogic": compiled_ir["compiled_jsonlogic"],
            "canonical_sha256": canonical_sha256,
            "compile_hash": compiled_ir["compile_hash"],
            "source_codes": sorted(set(source_codes)),
            "source_yaml": source_yaml,
            "source_manifest_json": source_manifest_json or {},
        }
    )


def compile_rule_file(
    path: str | Path,
    organization_id: str | None = None,
    source_manifest_json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rule_path = Path(path).resolve()
    if PACK_ROOT not in rule_path.parents and rule_path != PACK_ROOT:
        raise ValueError("Rule path must be inside the fixture pack.")

    source_doc, authoring_format = load_rule_document(rule_path)
    normalized_doc = normalize_authoring_document(source_doc)
    canonical_rule = build_canonical_rule(normalized_doc=normalized_doc, authoring_format=authoring_format)
    compiled_ir = build_compiled_ir(canonical_rule)
    canonical_rule_with_compiled = canonicalize(
        {
            **canonical_rule,
            "compiled": {
                "compiler_version": compiled_ir["compiler_version"],
                "compile_hash": compiled_ir["compile_hash"],
                "compiled_at": compiled_ir["compiled_at"],
                "jsonlogic": compiled_ir["compiled_jsonlogic"],
                "canonical_sha256": sha256_hex(canonical_rule),
                "support_level": JSONLOGIC_SUPPORT_LEVEL,
            },
        }
    )
    validate_canonical_rule_payload(canonical_rule_with_compiled)
    compile_artifact_row = emit_compile_artifact(
        canonical_rule=canonical_rule_with_compiled,
        compiled_ir=compiled_ir,
        organization_id=organization_id,
        source_manifest_json=source_manifest_json,
        source_yaml=rule_path.read_text(encoding="utf-8") if authoring_format == "yaml" else None,
    )
    return {
        "canonical_rule": canonical_rule_with_compiled,
        "compile_artifact_row": compile_artifact_row,
        "pipeline_metadata": {
            "authoring_format": authoring_format,
            "compiler_version": COMPILER_VERSION,
            "normalization_version": NORMALIZATION_VERSION,
            "jsonlogic_support_level": JSONLOGIC_SUPPORT_LEVEL,
        },
    }
