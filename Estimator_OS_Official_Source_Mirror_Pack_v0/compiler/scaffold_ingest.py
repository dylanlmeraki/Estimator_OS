"""Manifest-driven seed fixture ingestion scaffolding."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .scaffold_common import PACK_ROOT, canonicalize


@dataclass
class IngestionBundle:
    seed_import_runs: list[dict[str, Any]]
    seed_import_errors: list[dict[str, Any]]
    wage_source: list[dict[str, Any]]
    apprentice_ratio_rule: list[dict[str, Any]]
    equipment_rate_book: list[dict[str, Any]]
    vendor_source_registry: list[dict[str, Any]]
    material_catalog_item: list[dict[str, Any]]
    material_price_observation: list[dict[str, Any]]

    def as_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "seed_import_runs": self.seed_import_runs,
            "seed_import_errors": self.seed_import_errors,
            "wage_source": self.wage_source,
            "apprentice_ratio_rule": self.apprentice_ratio_rule,
            "equipment_rate_book": self.equipment_rate_book,
            "vendor_source_registry": self.vendor_source_registry,
            "material_catalog_item": self.material_catalog_item,
            "material_price_observation": self.material_price_observation,
        }


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _new_import_run(import_family: str, manifest_code: str, row_count: int, error_count: int, metadata: dict[str, Any]) -> dict[str, Any]:
    status = "failed" if row_count == 0 and error_count > 0 else "completed"
    if row_count > 0 and error_count > 0:
        status = "partial"
    return {
        "id": f"run_{uuid4().hex}",
        "organization_id": None,
        "import_family": import_family,
        "manifest_code": manifest_code,
        "source_id": None,
        "started_at": _utc_now(),
        "completed_at": _utc_now(),
        "status": status,
        "row_count": row_count,
        "error_count": error_count,
        "notes": None,
        "metadata_json": metadata,
    }


def _vendor_source_type(value: str) -> str:
    mapping = {
        "vendor_catalog": "vendor_catalog",
        "vendor_quote": "vendor_quote",
        "internal": "internal_catalog",
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


def _ingest_dir(dir_manifest: dict[str, Any], dir_sources: list[dict[str, str]], errors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    wage_rows: list[dict[str, Any]] = []
    ratio_rows: list[dict[str, Any]] = []
    for row in dir_sources:
        source_code = row.get("source_id", "").strip()
        source_type = row.get("source_type", "").strip()
        title = row.get("title", "").strip()
        source_url = row.get("url", "").strip()
        if not source_code or not source_type or not title or not source_url:
            errors.append(
                {
                    "id": f"imp_err_{uuid4().hex}",
                    "seed_import_run_id": None,
                    "row_identifier": source_code or "<missing-source-id>",
                    "error_code": "dir_source_missing_required_fields",
                    "error_message": "DIR source registry row is missing required values.",
                    "payload_json": row,
                    "created_at": _utc_now(),
                }
            )
            continue

        canonical_for = row.get("canonical_for", "")
        cycle = row.get("cycle") or None
        effective_start = row.get("effective_start") or "2026-01-01"
        effective_end = row.get("effective_end") or None
        inferred_type = "dir_apprentice" if "apprentice" in canonical_for else "dir_general"
        wage_rows.append(
            {
                "source_code": source_code,
                "source_type": inferred_type,
                "title": title,
                "source_url": source_url,
                "cycle": cycle,
                "county_scope": [],
                "craft_scope": [],
                "effective_start": effective_start,
                "effective_end": effective_end,
                "retrieved_at": _utc_now(),
                "canonical_for_public_works": canonical_for.startswith("public_works"),
                "raw_metadata_json": {
                    "source_type_original": source_type,
                    "canonical_for": canonical_for,
                    "notes": row.get("notes", ""),
                },
            }
        )

    ratio_rows.append(
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
            "notes": "Seeded from manifest normalize step baseline (1 apprentice hour per 5 journeyman hours).",
            "raw_metadata_json": {
                "dataset_code": dir_manifest.get("dataset_code"),
                "manifest_version": dir_manifest.get("manifest_version"),
            },
        }
    )
    return wage_rows, ratio_rows


def _ingest_caltrans(cal_manifest: dict[str, Any], caltrans_sources: list[dict[str, str]], errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    book_rows: list[dict[str, Any]] = []
    for row in caltrans_sources:
        source_code = row.get("source_id", "").strip()
        source_url = row.get("url", "").strip()
        title = row.get("title", "").strip()
        if not source_code or not source_url or not title:
            errors.append(
                {
                    "id": f"imp_err_{uuid4().hex}",
                    "seed_import_run_id": None,
                    "row_identifier": source_code or "<missing-source-id>",
                    "error_code": "caltrans_source_missing_required_fields",
                    "error_message": "Caltrans source registry row is missing required values.",
                    "payload_json": row,
                    "created_at": _utc_now(),
                }
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
                    "dataset_code": cal_manifest.get("dataset_code"),
                    "canonical_for": row.get("canonical_for", ""),
                },
            }
        )
    return book_rows


def _ingest_materials(
    materials_manifest: dict[str, Any],
    vendor_rows: list[dict[str, str]],
    catalog_rows: list[dict[str, str]],
    observation_rows: list[dict[str, str]],
    errors: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    vendor_payloads: list[dict[str, Any]] = []
    catalog_payloads: list[dict[str, Any]] = []
    observation_payloads: list[dict[str, Any]] = []

    subcategory_to_item: dict[str, str] = {}

    for row in vendor_rows:
        source_code = row.get("vendor_source_id", "").strip()
        vendor_name = row.get("vendor_name", "").strip()
        if not source_code or not vendor_name:
            errors.append(
                {
                    "id": f"imp_err_{uuid4().hex}",
                    "seed_import_run_id": None,
                    "row_identifier": source_code or "<missing-vendor-source-id>",
                    "error_code": "materials_vendor_missing_required_fields",
                    "error_message": "Vendor source registry row is missing required values.",
                    "payload_json": row,
                    "created_at": _utc_now(),
                }
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
                {
                    "id": f"imp_err_{uuid4().hex}",
                    "seed_import_run_id": None,
                    "row_identifier": item_code or "<missing-catalog-item-code>",
                    "error_code": "materials_catalog_missing_required_fields",
                    "error_message": "Material catalog row is missing required values.",
                    "payload_json": row,
                    "created_at": _utc_now(),
                }
            )
            continue

        subcategory_to_item[subcategory] = item_code
        catalog_payloads.append(
            {
                "catalog_item_code": item_code,
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
                    "dataset_code": materials_manifest.get("dataset_code"),
                },
            }
        )

    for row in observation_rows:
        subcategory = row.get("catalog_subcategory_code", "").strip()
        vendor_source = row.get("vendor_source_id", "").strip()
        public_price = row.get("public_price_usd", "").strip()
        if not subcategory or not vendor_source:
            errors.append(
                {
                    "id": f"imp_err_{uuid4().hex}",
                    "seed_import_run_id": None,
                    "row_identifier": row.get("sample_id") or "<missing-sample-id>",
                    "error_code": "materials_price_missing_required_fields",
                    "error_message": "Material observation row is missing required values.",
                    "payload_json": row,
                    "created_at": _utc_now(),
                }
            )
            continue
        if subcategory not in subcategory_to_item:
            errors.append(
                {
                    "id": f"imp_err_{uuid4().hex}",
                    "seed_import_run_id": None,
                    "row_identifier": row.get("sample_id") or "<missing-sample-id>",
                    "error_code": "materials_price_unknown_subcategory",
                    "error_message": "Observation subcategory was not found in catalog rows.",
                    "payload_json": row,
                    "created_at": _utc_now(),
                }
            )
            continue
        observation_payloads.append(
            {
                "sample_id": row.get("sample_id"),
                "material_catalog_item_code": subcategory_to_item[subcategory],
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
                "observed_at": row.get("retrieved_at") or _utc_now(),
                "effective_start": None,
                "effective_end": None,
                "raw_payload_json": row,
            }
        )

    return vendor_payloads, catalog_payloads, observation_payloads


def ingest_seed_fixtures(pack_root: str | Path = PACK_ROOT) -> dict[str, list[dict[str, Any]]]:
    root = Path(pack_root).resolve()
    manifests_dir = root / "seedpacks" / "manifests"
    sources_dir = root / "seedpacks" / "sources"

    dir_manifest = _read_json(manifests_dir / "dir_prevailing_wage_import_manifest.json")
    caltrans_manifest = _read_json(manifests_dir / "caltrans_equipment_import_manifest.json")
    materials_manifest = _read_json(manifests_dir / "materials_catalog_import_manifest.json")

    dir_sources = _read_csv(sources_dir / "dir_source_registry.csv")
    caltrans_sources = _read_csv(sources_dir / "caltrans_source_registry.csv")
    vendor_sources = _read_csv(sources_dir / "vendor_source_registry.csv")
    materials_catalog = _read_csv(sources_dir / "materials_catalog_v0.csv")
    materials_prices = _read_csv(sources_dir / "materials_public_price_samples.csv")

    errors: list[dict[str, Any]] = []

    wage_rows, ratio_rows = _ingest_dir(dir_manifest, dir_sources, errors)
    caltrans_books = _ingest_caltrans(caltrans_manifest, caltrans_sources, errors)
    vendor_rows, catalog_rows, price_rows = _ingest_materials(
        materials_manifest,
        vendor_sources,
        materials_catalog,
        materials_prices,
        errors,
    )

    run_records = [
        _new_import_run(
            import_family="dir",
            manifest_code=dir_manifest["dataset_code"],
            row_count=len(wage_rows) + len(ratio_rows),
            error_count=0,
            metadata={"manifest_version": dir_manifest.get("manifest_version"), "sources_seen": len(dir_sources)},
        ),
        _new_import_run(
            import_family="caltrans",
            manifest_code=caltrans_manifest["dataset_code"],
            row_count=len(caltrans_books),
            error_count=0,
            metadata={"manifest_version": caltrans_manifest.get("manifest_version"), "sources_seen": len(caltrans_sources)},
        ),
        _new_import_run(
            import_family="materials",
            manifest_code=materials_manifest["dataset_code"],
            row_count=len(vendor_rows) + len(catalog_rows) + len(price_rows),
            error_count=0,
            metadata={
                "manifest_version": materials_manifest.get("manifest_version"),
                "sources_seen": len(vendor_sources) + len(materials_catalog) + len(materials_prices),
            },
        ),
    ]

    error_records: list[dict[str, Any]] = []
    if errors:
        run_records[-1]["status"] = "partial"
        run_records[-1]["error_count"] = len(errors)
        for error in errors:
            error["seed_import_run_id"] = run_records[-1]["id"]
            error_records.append(error)

    bundle = IngestionBundle(
        seed_import_runs=run_records,
        seed_import_errors=error_records,
        wage_source=wage_rows,
        apprentice_ratio_rule=ratio_rows,
        equipment_rate_book=caltrans_books,
        vendor_source_registry=vendor_rows,
        material_catalog_item=catalog_rows,
        material_price_observation=price_rows,
    )
    return canonicalize(bundle.as_dict())


# Pass-2 shim: keep legacy module path but route callers to corrected implementation.
from .scaffold_ingest_v2 import ingest_seed_fixtures as ingest_seed_fixtures  # noqa: E402,F401
