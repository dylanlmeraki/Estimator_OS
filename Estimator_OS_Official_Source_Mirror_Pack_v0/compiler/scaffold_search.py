"""Search document builders and ranked query helpers for pass 2."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .scaffold_common import canonicalize


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_rule_evaluation_search_document(
    *,
    organization_id: str | None,
    evaluation_row: dict[str, Any],
) -> dict[str, Any]:
    output_snapshot = evaluation_row.get("output_snapshot", {})
    blockers = output_snapshot.get("blockers", [])
    flags = output_snapshot.get("flags", [])
    blocker_codes = [item.get("code") for item in blockers if item.get("code")]
    flag_codes = [item.get("flag_code") for item in flags if item.get("flag_code")]
    source_codes = [item for item in evaluation_row.get("source_codes", []) if item]

    title = f"Rule Evaluation {evaluation_row['rule_id']} ({evaluation_row['status']})"
    subtitle = f"Template {evaluation_row['template_version']} - Effective {evaluation_row['effective_date']}"
    body_text = " ".join(
        [
            evaluation_row["rule_id"],
            evaluation_row["status"],
            " ".join(source_codes),
            " ".join(blocker_codes),
            " ".join(flag_codes),
        ]
    ).strip()

    return canonicalize(
        {
            "organization_id": organization_id,
            "object_type": "rule_evaluation_snapshot",
            "object_id": evaluation_row["evaluation_id"],
            "title": title,
            "subtitle": subtitle,
            "body_text": body_text,
            "search_key": f"{evaluation_row['rule_id']} {evaluation_row['status']} {evaluation_row['template_version']}",
            "facets_json": {
                "status": evaluation_row["status"],
                "rule_id": evaluation_row["rule_id"],
                "template_version": evaluation_row["template_version"],
                "source_codes": source_codes,
            },
            "payload_json": {
                "evaluation_hash": evaluation_row["evaluation_hash"],
                "source_codes": source_codes,
                "blocker_codes": blocker_codes,
                "flag_codes": flag_codes,
            },
            "updated_at": _utc_now(),
        }
    )


def build_import_run_search_document(
    *,
    organization_id: str | None,
    import_run_row: dict[str, Any],
    import_errors: list[dict[str, Any]],
) -> dict[str, Any]:
    run_errors = [item for item in import_errors if item.get("seed_import_run_id") == import_run_row["id"]]
    error_codes = sorted({item["error_code"] for item in run_errors})

    title = f"Import Run {import_run_row['import_family']} ({import_run_row['status']})"
    subtitle = f"Manifest {import_run_row['manifest_code']} - Rows {import_run_row['row_count']}"
    body_text = " ".join(
        [
            import_run_row["import_family"],
            import_run_row["manifest_code"],
            import_run_row["status"],
            " ".join(error_codes),
        ]
    ).strip()

    return canonicalize(
        {
            "organization_id": organization_id,
            "object_type": "seed_import_run",
            "object_id": import_run_row["id"],
            "title": title,
            "subtitle": subtitle,
            "body_text": body_text,
            "search_key": f"{import_run_row['import_family']} {import_run_row['manifest_code']} {import_run_row['status']}",
            "facets_json": {
                "import_family": import_run_row["import_family"],
                "manifest_code": import_run_row["manifest_code"],
                "status": import_run_row["status"],
            },
            "payload_json": {
                "error_count": import_run_row["error_count"],
                "error_codes": error_codes,
            },
            "updated_at": _utc_now(),
        }
    )


def build_source_parse_run_search_document(
    *,
    organization_id: str | None,
    parse_run_row: dict[str, Any],
    parse_errors: list[dict[str, Any]],
) -> dict[str, Any]:
    run_errors = [item for item in parse_errors if item.get("source_code") == parse_run_row["source_code"]]
    error_codes = sorted({item["error_code"] for item in run_errors})
    object_id = (
        f"{parse_run_row['source_code']}:{parse_run_row['parser_code']}:"
        f"{parse_run_row.get('started_at', '')}"
    )
    parsed_row_counts = parse_run_row.get("parsed_row_counts", {})

    title = f"Source Parse {parse_run_row['source_code']} ({parse_run_row['status']})"
    subtitle = f"Family {parse_run_row['parse_family']} - Parser {parse_run_row['parser_code']}"
    body_text = " ".join(
        [
            parse_run_row["source_code"],
            parse_run_row["parse_family"],
            parse_run_row["status"],
            " ".join(error_codes),
        ]
    ).strip()

    return canonicalize(
        {
            "organization_id": organization_id,
            "object_type": "source_parse_run",
            "object_id": object_id,
            "title": title,
            "subtitle": subtitle,
            "body_text": body_text,
            "search_key": (
                f"{parse_run_row['source_code']} {parse_run_row['parse_family']} "
                f"{parse_run_row['parser_code']} {parse_run_row['status']}"
            ),
            "facets_json": {
                "source_code": parse_run_row["source_code"],
                "parse_family": parse_run_row["parse_family"],
                "status": parse_run_row["status"],
            },
            "payload_json": {
                "error_count": len(run_errors),
                "error_codes": error_codes,
                "parsed_row_counts": parsed_row_counts,
            },
            "updated_at": _utc_now(),
        }
    )


def build_ranked_search_query(
    *,
    query_text: str,
    organization_id: str | None,
    object_types: list[str] | None = None,
    limit: int = 20,
) -> tuple[str, dict[str, Any]]:
    where_filters = ["organization_id is not distinct from %(organization_id)s"]
    params: dict[str, Any] = {
        "organization_id": organization_id,
        "query_text": query_text,
        "limit": limit,
    }

    if object_types:
        where_filters.append("object_type = any(%(object_types)s)")
        params["object_types"] = object_types

    sql = (
        f"""
select
  object_type,
  object_id,
  title,
  subtitle,
  facets_json,
  payload_json,
  ts_rank_cd(tsv, websearch_to_tsquery('english', %(query_text)s)) as fts_rank,
  similarity(search_key, %(query_text)s) as trigram_score
from search_documents
where {' and '.join(where_filters)}
order by
  ts_rank_cd(tsv, websearch_to_tsquery('english', %(query_text)s)) desc,
  similarity(search_key, %(query_text)s) desc,
  updated_at desc
limit %(limit)s
""".strip()
    )
    return sql, params
