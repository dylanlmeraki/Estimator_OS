"""Source mirror -> parse -> normalized evidence scaffold for build-layer pass."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .scaffold_common import PACK_ROOT, canonicalize, sha256_hex

PARSER_VERSION = "source-mirror-v0.3.0"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _asset_kind_for_source_type(source_type: str) -> str:
    mapping = {
        "pdf": "raw_pdf",
        "csv": "raw_csv",
        "html_page": "raw_html",
        "json": "raw_json",
        "doc": "ocr_extract",
        "manual_note": "markdown_extract",
        "catalog_page": "raw_html",
        "search_result_snapshot": "raw_json",
    }
    return mapping.get(source_type, "raw_json")


def _new_parse_run(source_code: str, parser_code: str, parse_family: str, run_ts: str) -> dict[str, Any]:
    return {
        "source_code": source_code,
        "parser_code": parser_code,
        "parser_version": PARSER_VERSION,
        "parse_family": parse_family,
        "status": "running",
        "started_at": run_ts,
        "completed_at": None,
        "input_asset_ids": [],
        "parsed_row_counts": {},
        "promoted_row_counts": {},
        "metadata_json": {},
    }


def _finalize_parse_run(run: dict[str, Any], status: str, run_ts: str, parsed_row_counts: dict[str, int]) -> dict[str, Any]:
    run = dict(run)
    run["status"] = status
    run["completed_at"] = run_ts
    run["parsed_row_counts"] = parsed_row_counts
    return run


def _new_parse_error(
    source_code: str,
    error_code: str,
    error_message: str,
    run_ts: str,
    row_ref: str | None = None,
    field_name: str | None = None,
    raw_value: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "source_code": source_code,
        "row_ref": row_ref,
        "field_name": field_name,
        "error_code": error_code,
        "error_message": error_message,
        "raw_value": raw_value,
        "payload_json": payload or {},
        "created_at": run_ts,
    }


def _parse_sf_public_works_fee_schedule(source: dict[str, Any], run_ts: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    run = _new_parse_run(
        source_code=source["source_code"],
        parser_code="sf_public_works_fee_schedule_pdf_parser",
        parse_family="fee_schedule_pdf",
        run_ts=run_ts,
    )
    errors: list[dict[str, Any]] = []

    fee_schedule_source = {
        "source_code": source["source_code"],
        "jurisdiction_code": "sf",
        "authority_type": source["authority_type"],
        "title": source["title"],
        "source_url": source["source_url"],
        "effective_start": "2025-07-01",
        "effective_end": None,
        "retrieved_at": source["retrieved_at"],
        "source_cycle": source.get("effective_hint"),
        "metadata_json": {
            "seed_priority": source.get("seed_priority"),
            "status": source.get("status"),
        },
    }

    fee_entries = [
        {
            "source_code": source["source_code"],
            "jurisdiction_code": "sf",
            "fee_family": "row_excavation",
            "fee_code": "consultation_preapplication",
            "fee_label": "Pre-Application/Consultation Fee",
            "fee_basis_type": "consultation",
            "fee_amount": 375.0,
            "currency_code": "USD",
            "uom": "ls",
            "formula_notes": None,
            "qualifier_notes": "Seeded from mirror extract candidate; verify against latest PDF table extraction.",
            "effective_start": "2025-07-01",
            "effective_end": None,
            "metadata_json": {
                "parse_confidence": "medium",
                "indexed_extract_summary": source.get("indexed_extract", {}).get("summary", ""),
            },
        }
    ]

    if source.get("status") in {"queued_for_download", "indexed"}:
        errors.append(
            _new_parse_error(
                source_code=source["source_code"],
                error_code="source_not_mirrored_pdf_asset",
                error_message="PDF source is not mirrored as direct-file asset yet; entries are candidate rows pending table extract.",
                run_ts=run_ts,
                payload={"status": source.get("status")},
            )
        )

    run = _finalize_parse_run(
        run=run,
        status="partial" if errors else "succeeded",
        run_ts=run_ts,
        parsed_row_counts={"fee_schedule_source": 1, "fee_schedule_entry": len(fee_entries)},
    )
    return run, errors, [fee_schedule_source, *fee_entries]


def _parse_baaqmd_rule(source: dict[str, Any], run_ts: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    run = _new_parse_run(
        source_code=source["source_code"],
        parser_code="baaqmd_rule_11_2_parser",
        parse_family="regulatory_pdf",
        run_ts=run_ts,
    )
    errors: list[dict[str, Any]] = []

    rule_candidates = [
        {
            "rule_code": "baaqmd_demo_asbestos_notice",
            "source_code": source["source_code"],
            "jurisdiction_scope": source["jurisdiction_scope"],
            "trigger_type": "demolition_or_renovation",
            "inputs_required": ["project_scope.demolition_flag", "project_scope.structure_type"],
            "output_type": "checklist_and_warning",
            "notes": "10 working day notice generally required; small residential exception modeled separately.",
            "metadata_json": {"parse_confidence": "medium"},
        }
    ]
    checklist_candidates = [
        {
            "source_code": source["source_code"],
            "check_code": "baaqmd_notice_window",
            "label": "Confirm BAAQMD Rule 11-2 notice timing before demolition/renovation start.",
        }
    ]
    proposal_note_candidates = [
        {
            "source_code": source["source_code"],
            "note_code": "baaqmd_asbestos_notice_assumption",
            "text": "Schedule and scope assume required BAAQMD asbestos notice and abatement coordination where applicable.",
        }
    ]

    if source.get("status") in {"queued_for_download", "indexed"}:
        errors.append(
            _new_parse_error(
                source_code=source["source_code"],
                error_code="source_not_mirrored_pdf_asset",
                error_message="Regulatory PDF source still queued for direct-file mirror; candidates are extract-based placeholders.",
                run_ts=run_ts,
                payload={"status": source.get("status")},
            )
        )

    run = _finalize_parse_run(
        run=run,
        status="partial" if errors else "succeeded",
        run_ts=run_ts,
        parsed_row_counts={
            "jurisdiction_rule_template_candidates": len(rule_candidates),
            "checklist_template_candidates": len(checklist_candidates),
            "proposal_note_template_candidates": len(proposal_note_candidates),
        },
    )

    return run, errors, {
        "jurisdiction_rule_template_candidates": rule_candidates,
        "checklist_template_candidates": checklist_candidates,
        "proposal_note_template_candidates": proposal_note_candidates,
    }


def _parse_caltrans_equipment(
    source: dict[str, Any],
    caltrans_registry_rows: list[dict[str, str]],
    run_ts: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    run = _new_parse_run(
        source_code=source["source_code"],
        parser_code="caltrans_equipment_csv_parser",
        parse_family="equipment_csv",
        run_ts=run_ts,
    )
    errors: list[dict[str, Any]] = []

    book_code = "caltrans_equipment_2025_04_01_2026_03_31"
    book_rows = [
        {
            "source_code": source["source_code"],
            "rate_book_code": book_code,
            "title": source["title"],
            "source_url": source["source_url"],
            "effective_start": "2025-04-01",
            "effective_end": "2026-03-31",
            "metadata_json": {"parse_confidence": "high"},
        }
    ]

    entry_rows: list[dict[str, Any]] = []
    registry_match = next(
        (row for row in caltrans_registry_rows if row.get("source_id") == "caltrans_equipment_rate_book_2025_04_01_2026_03_31"),
        None,
    )
    if registry_match is None:
        errors.append(
            _new_parse_error(
                source_code=source["source_code"],
                error_code="caltrans_registry_row_missing",
                error_message="Expected Caltrans source registry row was not found.",
                run_ts=run_ts,
            )
        )
    else:
        errors.append(
            _new_parse_error(
                source_code=source["source_code"],
                error_code="equipment_csv_rows_not_mirrored",
                error_message="Caltrans rate-book metadata exists but detailed equipment CSV rows are not mirrored in this pack yet.",
                run_ts=run_ts,
                payload={"source_url": registry_match.get("url")},
            )
        )

    run = _finalize_parse_run(
        run=run,
        status="partial" if errors else "succeeded",
        run_ts=run_ts,
        parsed_row_counts={"equipment_rate_book": len(book_rows), "equipment_rate_entry": len(entry_rows)},
    )

    return run, errors, {"equipment_rate_book": book_rows, "equipment_rate_entry": entry_rows}


def build_source_mirror_bundle(pack_root: str | Path = PACK_ROOT, run_timestamp_utc: str | None = None) -> dict[str, Any]:
    root = Path(pack_root).resolve()
    run_ts = run_timestamp_utc or _utc_now()

    indexed_docs = _read_json(root / "indexes" / "source_registry.json")
    indexed_by_code = {item["source_code"]: item for item in indexed_docs}

    mirror_assets: list[dict[str, Any]] = []
    for mirror_path in sorted((root / "mirrors").glob("*.json")):
        raw_text = mirror_path.read_text(encoding="utf-8")
        payload = json.loads(raw_text)
        source_code = payload.get("source_code")
        if not source_code or source_code not in indexed_by_code:
            continue
        indexed = indexed_by_code[source_code]
        mirror_assets.append(
            {
                "source_code": source_code,
                "asset_kind": _asset_kind_for_source_type(indexed["source_type"]),
                "asset_storage_key": str(mirror_path.relative_to(root)).replace("\\", "/"),
                "asset_mime_type": "application/json",
                "checksum_sha256": sha256_hex(raw_text),
                "byte_size": len(raw_text.encode("utf-8")),
                "mirrored_at": run_ts,
                "parser_status": "not_started",
                "metadata_json": {"mirror_file": mirror_path.name},
            }
        )

    parse_runs: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []

    sf_source = indexed_by_code["sf_public_works_fee_schedule_pdf"]
    sf_run, sf_errors, sf_rows = _parse_sf_public_works_fee_schedule(sf_source, run_ts)
    parse_runs.append(sf_run)
    parse_errors.extend(sf_errors)

    baaqmd_source = indexed_by_code["baaqmd_reg11_rule2"]
    baaqmd_run, baaqmd_errors, baaqmd_rows = _parse_baaqmd_rule(baaqmd_source, run_ts)
    parse_runs.append(baaqmd_run)
    parse_errors.extend(baaqmd_errors)

    caltrans_source = indexed_by_code["caltrans_equipment_rate_book_page"]
    caltrans_registry = _read_csv(root / "seedpacks" / "sources" / "caltrans_source_registry.csv")
    caltrans_run, caltrans_errors, caltrans_rows = _parse_caltrans_equipment(caltrans_source, caltrans_registry, run_ts)
    parse_runs.append(caltrans_run)
    parse_errors.extend(caltrans_errors)

    bundle = {
        "indexed_source_document": sorted(indexed_docs, key=lambda item: item["source_code"]),
        "source_mirror_asset": sorted(mirror_assets, key=lambda item: item["source_code"]),
        "source_parse_run": sorted(parse_runs, key=lambda item: item["source_code"]),
        "source_parse_error": sorted(parse_errors, key=lambda item: (item["source_code"], item["error_code"])),
        "fee_schedule_source": [sf_rows[0]],
        "fee_schedule_entry": sf_rows[1:],
        "jurisdiction_rule_template_candidates": baaqmd_rows["jurisdiction_rule_template_candidates"],
        "checklist_template_candidates": baaqmd_rows["checklist_template_candidates"],
        "proposal_note_template_candidates": baaqmd_rows["proposal_note_template_candidates"],
        "equipment_rate_book": caltrans_rows["equipment_rate_book"],
        "equipment_rate_entry": caltrans_rows["equipment_rate_entry"],
    }
    return canonicalize(bundle)

