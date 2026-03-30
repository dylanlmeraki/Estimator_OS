"""Pass-2 invariant tests for scaffold pipeline."""

from __future__ import annotations

import unittest
from pathlib import Path

from compiler.scaffold_common import PACK_ROOT, canonicalize
from compiler.scaffold_compile import (
    build_canonical_rule,
    build_compiled_ir,
    compile_rule_file,
    load_rule_document,
    normalize_authoring_document,
)
from compiler.scaffold_evaluate import evaluate_rule_snapshot
from compiler.scaffold_ingest_v2 import _ingest_caltrans, ingest_seed_fixtures
from compiler.scaffold_search import (
    build_import_run_search_document,
    build_ranked_search_query,
    build_rule_evaluation_search_document,
    build_source_parse_run_search_document,
)
from compiler.scaffold_source_mirror_pipeline import build_source_mirror_bundle
from compiler.pass2_demo_runner import run_demo


class Pass2InvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rule_path = PACK_ROOT / "seedpacks" / "rules" / "dir_public_works_apprenticeship.yaml"
        self.compile_result = compile_rule_file(self.rule_path, organization_id="org_test")
        self.source_bundle = build_source_mirror_bundle(
            pack_root=PACK_ROOT,
            run_timestamp_utc="2026-03-30T00:00:00Z",
        )

    def test_canonical_rule_hash_stability(self) -> None:
        second = compile_rule_file(self.rule_path, organization_id="org_test")
        self.assertEqual(
            self.compile_result["compile_artifact_row"]["compile_hash"],
            second["compile_artifact_row"]["compile_hash"],
        )
        self.assertEqual(
            self.compile_result["compile_artifact_row"]["canonical_sha256"],
            second["compile_artifact_row"]["canonical_sha256"],
        )

    def test_evaluation_hash_stability(self) -> None:
        input_snapshot = {
            "opportunity": {"public_works_flag": True},
            "inputs": {
                "contract_amount": 50000,
                "craft_code": "laborer",
                "estimated_journeyman_st_hours": 25,
                "is_apprenticeable_craft": True,
            },
        }
        first = evaluate_rule_snapshot(
            canonical_rule=self.compile_result["canonical_rule"],
            input_snapshot=input_snapshot,
            effective_date="2026-03-30",
            organization_id="org_test",
        )
        second = evaluate_rule_snapshot(
            canonical_rule=self.compile_result["canonical_rule"],
            input_snapshot=input_snapshot,
            effective_date="2026-03-30",
            organization_id="org_test",
        )
        self.assertEqual(first["evaluation_row"]["evaluation_hash"], second["evaluation_row"]["evaluation_hash"])

    def test_null_preservation_in_canonicalization(self) -> None:
        payload = {"a": None, "z": {"x": 1, "y": None}}
        canonical = canonicalize(payload)
        self.assertIn("a", canonical)
        self.assertIsNone(canonical["a"])
        self.assertIn("y", canonical["z"])
        self.assertIsNone(canonical["z"]["y"])

    def test_compiler_output_reproducibility(self) -> None:
        source_doc, authoring_format = load_rule_document(self.rule_path)
        normalized = normalize_authoring_document(source_doc)
        canonical = build_canonical_rule(normalized, authoring_format)
        compiled_one = build_compiled_ir(canonical, compiled_at="2026-03-30T00:00:00Z")
        compiled_two = build_compiled_ir(canonical, compiled_at="2026-03-30T00:00:00Z")
        self.assertEqual(compiled_one["compile_hash"], compiled_two["compile_hash"])
        self.assertEqual(compiled_one["compiled_jsonlogic"], compiled_two["compiled_jsonlogic"])

    def test_ingest_error_attribution_by_family(self) -> None:
        manifest = {"dataset_code": "caltrans_equipment_seed_v0"}
        _, errors = _ingest_caltrans(
            caltrans_manifest=manifest,
            caltrans_sources=[{"source_id": "", "url": "", "title": ""}],
            now_utc="2026-03-30T00:00:00Z",
        )
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["import_family"], "caltrans")
        self.assertEqual(errors[0]["manifest_code"], "caltrans_equipment_seed_v0")

    def test_source_parse_error_attribution_by_family(self) -> None:
        runs_by_source = {row["source_code"]: row for row in self.source_bundle["source_parse_run"]}
        errors_by_source = {row["source_code"]: row for row in self.source_bundle["source_parse_error"]}

        self.assertIn("sf_public_works_fee_schedule_pdf", runs_by_source)
        self.assertIn("baaqmd_reg11_rule2", runs_by_source)
        self.assertIn("caltrans_equipment_rate_book_page", runs_by_source)

        self.assertEqual(runs_by_source["sf_public_works_fee_schedule_pdf"]["parse_family"], "fee_schedule_pdf")
        self.assertEqual(runs_by_source["baaqmd_reg11_rule2"]["parse_family"], "regulatory_pdf")
        self.assertEqual(runs_by_source["caltrans_equipment_rate_book_page"]["parse_family"], "equipment_csv")

        self.assertEqual(
            errors_by_source["sf_public_works_fee_schedule_pdf"]["error_code"],
            "source_not_mirrored_pdf_asset",
        )
        self.assertEqual(
            errors_by_source["baaqmd_reg11_rule2"]["error_code"],
            "source_not_mirrored_pdf_asset",
        )
        self.assertEqual(
            errors_by_source["caltrans_equipment_rate_book_page"]["error_code"],
            "equipment_csv_rows_not_mirrored",
        )

    def test_materials_observation_identity_mapping(self) -> None:
        bundle = ingest_seed_fixtures(pack_root=PACK_ROOT, run_timestamp_utc="2026-03-30T00:00:00Z")
        observations = bundle["material_price_observation"]
        self.assertGreater(len(observations), 0)
        for row in observations:
            self.assertTrue(row["material_catalog_item_identity"].startswith("catalog_item::"))
            self.assertIn(row["material_catalog_item_code"], row["material_catalog_item_identity"])

    def test_source_mirror_bundle_determinism(self) -> None:
        second = build_source_mirror_bundle(
            pack_root=PACK_ROOT,
            run_timestamp_utc="2026-03-30T00:00:00Z",
        )
        self.assertEqual(self.source_bundle, second)

    def test_search_document_generation_and_query_smoke(self) -> None:
        evaluation = evaluate_rule_snapshot(
            canonical_rule=self.compile_result["canonical_rule"],
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
            organization_id="org_test",
        )
        eval_doc = build_rule_evaluation_search_document(
            organization_id="org_test",
            evaluation_row=evaluation["evaluation_row"],
        )
        self.assertEqual(eval_doc["object_type"], "rule_evaluation_snapshot")

        bundle = ingest_seed_fixtures(pack_root=PACK_ROOT, run_timestamp_utc="2026-03-30T00:00:00Z")
        run_doc = build_import_run_search_document(
            organization_id="org_test",
            import_run_row=bundle["seed_import_runs"][0],
            import_errors=bundle["seed_import_errors"],
        )
        self.assertEqual(run_doc["object_type"], "seed_import_run")

        parse_doc = build_source_parse_run_search_document(
            organization_id="org_test",
            parse_run_row=self.source_bundle["source_parse_run"][0],
            parse_errors=self.source_bundle["source_parse_error"],
        )
        self.assertEqual(parse_doc["object_type"], "source_parse_run")

        sql, params = build_ranked_search_query(
            query_text="labor blocked",
            organization_id="org_test",
            object_types=["rule_evaluation_snapshot", "seed_import_run", "source_parse_run"],
            limit=10,
        )
        self.assertIn("ts_rank_cd", sql)
        self.assertIn("similarity", sql)
        self.assertIn("object_type = any", sql)
        self.assertEqual(params["organization_id"], "org_test")

    def test_demo_runner_end_to_end_pipeline(self) -> None:
        summary = run_demo(pack_root=PACK_ROOT, db_path=":memory:")
        self.assertTrue(summary["compile_hash"])
        self.assertTrue(summary["evaluation_hash"])
        self.assertEqual(summary["evaluation_status"], "blocked")
        self.assertGreater(summary["import_run_count"], 0)
        self.assertGreater(summary["source_indexed_count"], 0)
        self.assertGreater(summary["source_parse_run_count"], 0)
        self.assertGreater(summary["search_document_count"], 0)


if __name__ == "__main__":
    unittest.main()
