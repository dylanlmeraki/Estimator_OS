"""Manifest-driven seed fixture ingestion scaffolding (pass 2)."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .scaffold_common import PACK_ROOT, canonicalize


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _now_or(now_utc: str | None) -> str:
    return now_utc or _utc_now()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _new_import_error(
    *,
    import_family: str,
    manifest_code: str,
    row_identifier: str,
    error_code: str,
    error_message: str,
    payload_json: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    return {
        "id": f"imp_err_{uuid4().hex}",
        "seed_import_run_id": None,
        "import_family": import_family,
        "manifest_code": manifest_code,
        "row_identifier": row_identifier,
        "error_code": error_code,
        "error_message": error_message,
        "payload_json": payload_json,
        "created_at": created_at,
    }


def _new_import_run(
    *,
    import_family: str,
    manifest_code: str,
    row_count: int,
    errors: list[dict[str, Any]],
    now_utc: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    status = "completed"
    if row_count == 0 and errors:
        status = "failed"
    elif errors:
        status = "partial"

    return {
        "id": f"run_{uuid4().hex}",
        "organization_id": None,
        "import_family": import_family,
        "manifest_code": manifest_code,
        "source_id": None,
        "started_at": now_utc,
        "completed_at": now_utc,
        "status": status,
        "row_count": row_count,
        "error_count": len(errors),
        "notes": None,
        "metadata_json": metadata,
    }


def _vendor_source_type(value: str) -> str:
    mapping = {
        "vendor_catalog": "vendor_catalog",
        "vendor_quote": "vendor_quote",
        "internal": "internal_catalog",
        "internal_catalog": "internal_catalog",
    }
    return mapping.get(value, "manual")


def _default_material_confidence(value: str) -> str:
    mapping = {
        "public_list_price": "public_list_price",
        "quote": "quote",
        "branch_specific": "branch_specific",
        "manual": "manual",
        "benchmark": "benchmark",
    }
    return mapping.get(value, "manual")


def _material_observation_confidence(value: str) -> str:
    mapping = {
        "public_list_price": "public_list_price",
        "branch_specific": "branch_specific",
        "quote": "quote",
        "manual": "manual",
        "benchmark": "benchmark",
    }
    return mapping.get(value, "manual")


def _ingest_dir(
    *,
    dir_manifest: dict[str, Any],
    dir_sources: list[dict[str, str]],
    now_utc: str,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    dataset_code = str(dir_manifest["dataset_code"])
    errors: list[dict[str, Any]] = []
    wage_rows: list[dict[str, Any]] = []

    for row in dir_sources:
        source_code = row.get("source_id", "").strip()
        source_type = row.get("source_type", "").strip()
        title = row.get("title", "").strip()
        source_url = row.get("url", "").strip()
        if not source_code or not source_type or not title or not source_url:
            errors.append(
                _new_import_error(
                    import_family="dir",
                    manifest_code=dataset_code,
                    row_identifier=source_code or "<missing-source-id>",
                    error_code="dir_source_missing_required_fields",
                    error_message="DIR source registry row is missing required values.",
                    payload_json=row,
                    created_at=now_utc,
                )
            )
            continue

        canonical_for = row.get("canonical_for", "")
        inferred_type = "dir_apprentice" if "apprentice" in canonical_for else "dir_general"
        wage_rows.append(
            {
                "source_code": source_code,
                "source_type": inferred_type,
                "title": title,
                "source_url": source_url,
                "cycle": row.get("cycle") or None,
                "county_scope": [],
                "craft_scope": [],
                "effective_start": row.get("effective_start") or "2026-01-01",
                "effective_end": row.get("effective_end") or None,
                "retrieved_at": now_utc,
                "canonical_for_public_works": canonical_for.startswith("public_works"),
                "raw_metadata_json": {
                    "source_type_original": source_type,
                    "canonical_for": canonical_for,
                    "notes": row.get("notes", ""),
                },
            }
        )

    ratio_rows = [
        {
            "source_code": "dir_apprentice_ratio_default_1_to_5",
            "state_code": "CA",
            "craft_code": None,
            "applicability_scope": "public_works",
            "contract_amount_threshold": 30000.00,
            "ratio_basis": "straight_time_journeyman_hours",
            "minimum_journeyman_hours": 5,
            "apprentice_hours_required": 1,
            "requires_das_140": True,
            "requires_das_142": True,
            "requires_training_fund": True,
            "source_url": "https://www.dir.ca.gov/das/publicworks.html",
            "effective_start": "2026-01-01",
            "effective_end": None,
            "notes": "Seed baseline from DIR manifest normalize steps.",
            "raw_metadata_json": {
                "dataset_code": dataset_code,
                "manifest_version": dir_manifest.get("manifest_version"),
            },
        }
    ]

    rows = {
        "wage_source": sorted(wage_rows, key=lambda item: item["source_code"]),
        "apprentice_ratio_rule": ratio_rows,
        "equipment_rate_book": [],
        "vendor_source_registry": [],
        "material_catalog_item": [],
        "material_price_observation": [],
    }
    return rows, errors


def _ingest_caltrans(
    *,
    caltrans_manifest: dict[str, Any],
    caltrans_sources: list[dict[str, str]],
    now_utc: str,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    dataset_code = str(caltrans_manifest["dataset_code"])
    errors: list[dict[str, Any]] = []
    book_rows: list[dict[str, Any]] = []

    for row in caltrans_sources:
        source_code = row.get("source_id", "").strip()
        source_url = row.get("url", "").strip()
        title = row.get("title", "").strip()
        if not source_code or not source_url or not title:
            errors.append(
                _new_import_error(
                    import_family="caltrans",
                    manifest_code=dataset_code,
                    row_identifier=source_code or "<missing-source-id>",
                    error_code="caltrans_source_missing_required_fields",
                    error_message="Caltrans source registry row is missing required values.",
                    payload_json=row,
                    created_at=now_utc,
                )
            )
            continue

        book_rows.append(
            {
                "source_code": source_code,
                "provider_code": "caltrans",
                "title": title,
                "source_url": source_url,
                "effective_start": row.get("effective_start") or "2025-04-01",
                "effective_end": row.get("effective_end") or None,
                "public_works_canonical": row.get("canonical_for", "").startswith("public_works"),
                "source_asset_type": "csv",
                "notes": row.get("notes", ""),
                "raw_metadata_json": {
                    "dataset_code": dataset_code,
                    "canonical_for": row.get("canonical_for", ""),
                },
            }
        )

    rows = {
        "wage_source": [],
        "apprentice_ratio_rule": [],
        "equipment_rate_book": sorted(book_rows, key=lambda item: item["source_code"]),
        "vendor_source_registry": [],
        "material_catalog_item": [],
        "material_price_observation": [],
    }
    return rows, errors


def _ingest_materials(
    *,
    materials_manifest: dict[str, Any],
    vendor_rows: list[dict[str, str]],
    catalog_rows: list[dict[str, str]],
    observation_rows: list[dict[str, str]],
    now_utc: str,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    dataset_code = str(materials_manifest["dataset_code"])
    errors: list[dict[str, Any]] = []

    vendor_payloads: list[dict[str, Any]] = []
    catalog_payloads: list[dict[str, Any]] = []
    observation_payloads: list[dict[str, Any]] = []

    subcategory_to_identity: dict[str, tuple[str, str]] = {}

    for row in vendor_rows:
        source_code = row.get("vendor_source_id", "").strip()
        vendor_name = row.get("vendor_name", "").strip()
        if not source_code or not vendor_name:
            errors.append(
                _new_import_error(
                    import_family="materials",
                    manifest_code=dataset_code,
                    row_identifier=source_code or "<missing-vendor-source-id>",
                    error_code="materials_vendor_missing_required_fields",
                    error_message="Vendor source registry row is missing required values.",
                    payload_json=row,
                    created_at=now_utc,
                )
            )
            continue

        vendor_payloads.append(
            {
                "vendor_source_code": source_code,
                "vendor_name": vendor_name,
                "source_type": _vendor_source_type(row.get("source_type", "")),
                "source_url": row.get("source_url") or None,
                "location_scope": row.get("location_scope") or "regional",
                "price_variance_policy": row.get("price_variance_policy") or "location_scoped",
                "default_confidence": _default_material_confidence(row.get("default_confidence", "")),
                "notes": row.get("notes", ""),
                "active": True,
            }
        )

    for row in catalog_rows:
        item_code = row.get("catalog_item_code", "").strip()
        subcategory = row.get("subcategory_code", "").strip()
        description = row.get("description", "").strip()
        uom = row.get("uom", "").strip()
        if not item_code or not subcategory or not description or not uom:
            errors.append(
                _new_import_error(
                    import_family="materials",
                    manifest_code=dataset_code,
                    row_identifier=item_code or "<missing-catalog-item-code>",
                    error_code="materials_catalog_missing_required_fields",
                    error_message="Material catalog row is missing required values.",
                    payload_json=row,
                    created_at=now_utc,
                )
            )
            continue

        identity = f"catalog_item::{item_code}"
        if subcategory in subcategory_to_identity and subcategory_to_identity[subcategory][0] != item_code:
            errors.append(
                _new_import_error(
                    import_family="materials",
                    manifest_code=dataset_code,
                    row_identifier=item_code,
                    error_code="materials_catalog_duplicate_subcategory",
                    error_message="Subcategory maps to multiple catalog item codes.",
                    payload_json=row,
                    created_at=now_utc,
                )
            )
            continue

        subcategory_to_identity[subcategory] = (item_code, identity)
        catalog_payloads.append(
            {
                "catalog_item_code": item_code,
                "catalog_item_identity": identity,
                "category_code": row.get("category", "uncategorized"),
                "subcategory_code": subcategory,
                "description": description,
                "typical_uom": uom,
                "source_strategy": row.get("source_strategy") or "curated_plus_observation",
                "preferred_vendor_source_code": row.get("default_vendor_source_id") or None,
                "bay_area_priority": str(row.get("bay_area_priority", "true")).lower() == "true",
                "location_scope": row.get("location_scope") or "regional",
                "default_price_confidence": row.get("price_confidence") or "structure_only",
                "notes": row.get("notes") or "",
                "metadata_json": {
                    "seed_price_usd": row.get("seed_price_usd") or None,
                    "currency": row.get("currency") or "USD",
                    "dataset_code": dataset_code,
                },
            }
        )

    for row in observation_rows:
        subcategory = row.get("catalog_subcategory_code", "").strip()
        vendor_source = row.get("vendor_source_id", "").strip()
        public_price = row.get("public_price_usd", "").strip()
        if not subcategory or not vendor_source:
            errors.append(
                _new_import_error(
                    import_family="materials",
                    manifest_code=dataset_code,
                    row_identifier=row.get("sample_id") or "<missing-sample-id>",
                    error_code="materials_price_missing_required_fields",
                    error_message="Material observation row is missing required values.",
                    payload_json=row,
                    created_at=now_utc,
                )
            )
            continue

        if subcategory not in subcategory_to_identity:
            errors.append(
                _new_import_error(
                    import_family="materials",
                    manifest_code=dataset_code,
                    row_identifier=row.get("sample_id") or "<missing-sample-id>",
                    error_code="materials_price_unknown_subcategory",
                    error_message="Observation subcategory was not found in catalog rows.",
                    payload_json=row,
                    created_at=now_utc,
                )
            )
            continue

        item_code, identity = subcategory_to_identity[subcategory]
        observation_payloads.append(
            {
                "sample_id": row.get("sample_id"),
                "material_catalog_item_code": item_code,
                "material_catalog_item_identity": identity,
                "vendor_source_code": vendor_source,
                "branch_name": None,
                "branch_city": None,
                "branch_region": "Bay Area",
                "location_scope": row.get("location_scope") or "branch/location",
                "public_price": float(public_price) if public_price else None,
                "currency_code": "USD",
                "uom": row.get("unit") or "ea",
                "price_confidence": _material_observation_confidence(row.get("price_confidence", "")),
                "source_url": row.get("source_url") or None,
                "observed_at": row.get("retrieved_at") or now_utc,
                "effective_start": None,
                "effective_end": None,
                "raw_payload_json": row,
            }
        )

    rows = {
        "wage_source": [],
        "apprentice_ratio_rule": [],
        "equipment_rate_book": [],
        "vendor_source_registry": sorted(vendor_payloads, key=lambda item: item["vendor_source_code"]),
        "material_catalog_item": sorted(catalog_payloads, key=lambda item: item["catalog_item_code"]),
        "material_price_observation": sorted(observation_payloads, key=lambda item: item["sample_id"] or ""),
    }
    return rows, errors


def _collect_row_count(rows: dict[str, list[dict[str, Any]]]) -> int:
    return sum(len(items) for items in rows.values())


def ingest_seed_fixtures(pack_root: str | Path = PACK_ROOT, run_timestamp_utc: str | None = None) -> dict[str, list[dict[str, Any]]]:
    root = Path(pack_root).resolve()
    manifests_dir = root / "seedpacks" / "manifests"
    sources_dir = root / "seedpacks" / "sources"
    now_utc = _now_or(run_timestamp_utc)

    dir_manifest = _read_json(manifests_dir / "dir_prevailing_wage_import_manifest.json")
    caltrans_manifest = _read_json(manifests_dir / "caltrans_equipment_import_manifest.json")
    materials_manifest = _read_json(manifests_dir / "materials_catalog_import_manifest.json")

    dir_rows, dir_errors = _ingest_dir(
        dir_manifest=dir_manifest,
        dir_sources=_read_csv(sources_dir / "dir_source_registry.csv"),
        now_utc=now_utc,
    )
    caltrans_rows, caltrans_errors = _ingest_caltrans(
        caltrans_manifest=caltrans_manifest,
        caltrans_sources=_read_csv(sources_dir / "caltrans_source_registry.csv"),
        now_utc=now_utc,
    )
    materials_rows, materials_errors = _ingest_materials(
        materials_manifest=materials_manifest,
        vendor_rows=_read_csv(sources_dir / "vendor_source_registry.csv"),
        catalog_rows=_read_csv(sources_dir / "materials_catalog_v0.csv"),
        observation_rows=_read_csv(sources_dir / "materials_public_price_samples.csv"),
        now_utc=now_utc,
    )

    run_dir = _new_import_run(
        import_family="dir",
        manifest_code=dir_manifest["dataset_code"],
        row_count=_collect_row_count(dir_rows),
        errors=dir_errors,
        now_utc=now_utc,
        metadata={"manifest_version": dir_manifest.get("manifest_version")},
    )
    run_caltrans = _new_import_run(
        import_family="caltrans",
        manifest_code=caltrans_manifest["dataset_code"],
        row_count=_collect_row_count(caltrans_rows),
        errors=caltrans_errors,
        now_utc=now_utc,
        metadata={"manifest_version": caltrans_manifest.get("manifest_version")},
    )
    run_materials = _new_import_run(
        import_family="materials",
        manifest_code=materials_manifest["dataset_code"],
        row_count=_collect_row_count(materials_rows),
        errors=materials_errors,
        now_utc=now_utc,
        metadata={"manifest_version": materials_manifest.get("manifest_version")},
    )

    for error in dir_errors:
        error["seed_import_run_id"] = run_dir["id"]
    for error in caltrans_errors:
        error["seed_import_run_id"] = run_caltrans["id"]
    for error in materials_errors:
        error["seed_import_run_id"] = run_materials["id"]

    result = {
        "seed_import_runs": [run_dir, run_caltrans, run_materials],
        "seed_import_errors": sorted(
            [*dir_errors, *caltrans_errors, *materials_errors],
            key=lambda item: (item["import_family"], item["row_identifier"], item["error_code"]),
        ),
        "wage_source": dir_rows["wage_source"],
        "apprentice_ratio_rule": dir_rows["apprentice_ratio_rule"],
        "equipment_rate_book": caltrans_rows["equipment_rate_book"],
        "vendor_source_registry": materials_rows["vendor_source_registry"],
        "material_catalog_item": materials_rows["material_catalog_item"],
        "material_price_observation": materials_rows["material_price_observation"],
    }
    return canonicalize(result)

