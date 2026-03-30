"""Pass-2 demo runner: compile -> evaluate -> ingest -> search -> persist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parent.parent))

from compiler.scaffold_compile import compile_rule_file
from compiler.scaffold_evaluate import evaluate_rule_snapshot
from compiler.scaffold_ingest_v2 import ingest_seed_fixtures
from compiler.scaffold_search import (
    build_import_run_search_document,
    build_rule_evaluation_search_document,
    build_source_parse_run_search_document,
)
from compiler.scaffold_source_mirror_pipeline import build_source_mirror_bundle
from compiler.scaffold_store import (
    initialize_scaffold_store,
    insert_rule_compile_artifact,
    insert_rule_evaluation_snapshot,
    insert_search_documents,
    insert_seed_import_bundle,
    insert_source_mirror_bundle,
)


def run_demo(pack_root: Path, db_path: str | Path) -> dict[str, Any]:
    organization_id = "org_pass2_demo"
    rule_path = pack_root / "seedpacks" / "rules" / "dir_public_works_apprenticeship.yaml"

    compile_result = compile_rule_file(
        path=rule_path,
        organization_id=organization_id,
        source_manifest_json={"demo": "pass2", "source": str(rule_path.relative_to(pack_root))},
    )
    canonical_rule = compile_result["canonical_rule"]
    compile_row = compile_result["compile_artifact_row"]

    evaluation_result = evaluate_rule_snapshot(
        canonical_rule=canonical_rule,
        input_snapshot={
            "opportunity": {"public_works_flag": True},
            "inputs": {
                "contract_amount": 85000,
                "craft_code": "laborer",
                "estimated_journeyman_st_hours": 0,
                "is_apprenticeable_craft": True,
            },
        },
        effective_date="2026-03-30",
        organization_id=organization_id,
    )
    evaluation_row = evaluation_result["evaluation_row"]

    ingestion_bundle = ingest_seed_fixtures(pack_root=pack_root, run_timestamp_utc="2026-03-30T00:00:00Z")
    source_mirror_bundle = build_source_mirror_bundle(pack_root=pack_root, run_timestamp_utc="2026-03-30T00:00:00Z")

    search_documents = [
        build_rule_evaluation_search_document(
            organization_id=organization_id,
            evaluation_row=evaluation_row,
        )
    ]
    search_documents.extend(
        build_import_run_search_document(
            organization_id=organization_id,
            import_run_row=run_row,
            import_errors=ingestion_bundle["seed_import_errors"],
        )
        for run_row in ingestion_bundle["seed_import_runs"]
    )
    search_documents.extend(
        build_source_parse_run_search_document(
            organization_id=organization_id,
            parse_run_row=run_row,
            parse_errors=source_mirror_bundle["source_parse_error"],
        )
        for run_row in source_mirror_bundle["source_parse_run"]
    )

    conn = initialize_scaffold_store(db_path)
    try:
        insert_rule_compile_artifact(conn, compile_row)
        insert_rule_evaluation_snapshot(conn, evaluation_row)
        insert_seed_import_bundle(conn, ingestion_bundle)
        insert_source_mirror_bundle(conn, source_mirror_bundle)
        insert_search_documents(conn, search_documents)
    finally:
        conn.close()

    return {
        "db_path": str(db_path),
        "compile_hash": compile_row["compile_hash"],
        "evaluation_hash": evaluation_row["evaluation_hash"],
        "evaluation_status": evaluation_row["status"],
        "import_run_count": len(ingestion_bundle["seed_import_runs"]),
        "import_error_count": len(ingestion_bundle["seed_import_errors"]),
        "source_indexed_count": len(source_mirror_bundle["indexed_source_document"]),
        "source_parse_run_count": len(source_mirror_bundle["source_parse_run"]),
        "source_parse_error_count": len(source_mirror_bundle["source_parse_error"]),
        "fee_schedule_entry_count": len(source_mirror_bundle["fee_schedule_entry"]),
        "search_document_count": len(search_documents),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pass-2 scaffold pipeline demo.")
    parser.add_argument(
        "--pack-root",
        default=str(Path(__file__).resolve().parent.parent),
        help="Path to Estimator_OS source pack root.",
    )
    parser.add_argument(
        "--db-path",
        default=":memory:",
        help="SQLite persistence path for the scaffold run. Use :memory: for no filesystem writes.",
    )
    args = parser.parse_args()

    db_path = args.db_path if args.db_path == ":memory:" else str(Path(args.db_path).resolve())
    summary = run_demo(pack_root=Path(args.pack_root).resolve(), db_path=db_path)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
