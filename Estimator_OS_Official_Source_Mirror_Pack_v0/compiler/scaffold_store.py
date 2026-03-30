"""Local persistence scaffold using SQLite table mirrors for pass-2 demos/tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def _to_json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def initialize_scaffold_store(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        create table if not exists rule_compile_artifact (
            id integer primary key autoincrement,
            organization_id text null,
            rule_id text not null,
            rule_code text not null,
            template_version text not null,
            schema_version text not null,
            compiler_version text not null,
            normalization_version text not null,
            canonical_json text not null,
            compiled_jsonlogic text not null,
            canonical_sha256 text not null,
            compile_hash text not null,
            source_codes text not null,
            source_yaml text null,
            source_manifest_json text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists rule_evaluation_snapshot (
            id integer primary key autoincrement,
            organization_id text null,
            evaluation_id text not null,
            rule_id text not null,
            template_version text not null,
            compile_hash text not null,
            evaluation_hash text not null,
            effective_date text not null,
            status text not null,
            source_codes text not null,
            input_snapshot text not null,
            output_snapshot text not null,
            confirmations text not null,
            overrides text not null,
            evaluated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists seed_import_run (
            id text primary key,
            organization_id text null,
            import_family text not null,
            manifest_code text not null,
            source_id text null,
            started_at text not null,
            completed_at text not null,
            status text not null,
            row_count integer not null,
            error_count integer not null,
            notes text null,
            metadata_json text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists seed_import_error (
            id text primary key,
            seed_import_run_id text null,
            import_family text not null,
            manifest_code text not null,
            row_identifier text null,
            error_code text not null,
            error_message text not null,
            payload_json text not null,
            created_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists indexed_source_document (
            id integer primary key autoincrement,
            source_code text not null unique,
            title text not null,
            source_url text not null,
            source_type text not null,
            authority_type text not null,
            jurisdiction_scope text not null,
            effective_hint text null,
            retrieved_at text not null,
            status text not null,
            indexed_extract text not null,
            normalization_targets text not null,
            seed_priority text not null,
            notes text null,
            metadata_json text not null,
            created_at text not null,
            updated_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists source_mirror_asset (
            id integer primary key autoincrement,
            source_code text not null,
            asset_kind text not null,
            asset_storage_key text not null,
            asset_mime_type text not null,
            checksum_sha256 text not null,
            byte_size integer null,
            mirrored_at text not null,
            parser_status text not null,
            metadata_json text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists source_parse_run (
            id integer primary key autoincrement,
            source_code text not null,
            parser_code text not null,
            parser_version text not null,
            parse_family text not null,
            status text not null,
            started_at text not null,
            completed_at text null,
            input_asset_ids text not null,
            parsed_row_counts text not null,
            promoted_row_counts text not null,
            metadata_json text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists source_parse_error (
            id integer primary key autoincrement,
            source_code text not null,
            source_parse_run_source_code text null,
            row_ref text null,
            field_name text null,
            error_code text not null,
            error_message text not null,
            raw_value text null,
            payload_json text not null,
            created_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists fee_schedule_source (
            id integer primary key autoincrement,
            source_code text not null unique,
            jurisdiction_code text not null,
            authority_type text not null,
            title text not null,
            source_url text not null,
            effective_start text null,
            effective_end text null,
            retrieved_at text not null,
            source_cycle text null,
            parse_run_source_code text null,
            metadata_json text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists fee_schedule_entry (
            id integer primary key autoincrement,
            source_code text not null,
            jurisdiction_code text not null,
            fee_family text not null,
            fee_code text not null,
            fee_label text not null,
            fee_basis_type text not null,
            fee_amount real null,
            currency_code text not null,
            uom text null,
            formula_notes text null,
            qualifier_notes text null,
            effective_start text null,
            effective_end text null,
            metadata_json text not null
        )
        """
    )
    conn.execute(
        """
        create unique index if not exists idx_fee_schedule_entry_unique
            on fee_schedule_entry(source_code, fee_code, ifnull(uom, ''))
        """
    )
    conn.execute(
        """
        create table if not exists search_documents (
            id integer primary key autoincrement,
            organization_id text null,
            object_type text not null,
            object_id text not null,
            title text not null,
            subtitle text null,
            body_text text null,
            search_key text not null,
            facets_json text not null,
            payload_json text not null,
            updated_at text not null
        )
        """
    )
    conn.commit()
    return conn


def insert_rule_compile_artifact(conn: sqlite3.Connection, row: dict[str, Any]) -> None:
    conn.execute(
        """
        insert into rule_compile_artifact (
            organization_id, rule_id, rule_code, template_version, schema_version,
            compiler_version, normalization_version, canonical_json, compiled_jsonlogic,
            canonical_sha256, compile_hash, source_codes, source_yaml, source_manifest_json
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row.get("organization_id"),
            row["rule_id"],
            row["rule_code"],
            row["template_version"],
            row["schema_version"],
            row["compiler_version"],
            row["normalization_version"],
            _to_json_text(row["canonical_json"]),
            _to_json_text(row["compiled_jsonlogic"]),
            row["canonical_sha256"],
            row["compile_hash"],
            _to_json_text(row.get("source_codes", [])),
            row.get("source_yaml"),
            _to_json_text(row.get("source_manifest_json", {})),
        ),
    )
    conn.commit()


def insert_rule_evaluation_snapshot(conn: sqlite3.Connection, row: dict[str, Any]) -> None:
    conn.execute(
        """
        insert into rule_evaluation_snapshot (
            organization_id, evaluation_id, rule_id, template_version, compile_hash,
            evaluation_hash, effective_date, status, source_codes, input_snapshot, output_snapshot,
            confirmations, overrides, evaluated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row.get("organization_id"),
            row["evaluation_id"],
            row["rule_id"],
            row["template_version"],
            row["compile_hash"],
            row["evaluation_hash"],
            row["effective_date"],
            row["status"],
            _to_json_text(row.get("source_codes", [])),
            _to_json_text(row["input_snapshot"]),
            _to_json_text(row["output_snapshot"]),
            _to_json_text(row["confirmations"]),
            _to_json_text(row["overrides"]),
            row["evaluated_at"],
        ),
    )
    conn.commit()


def insert_seed_import_bundle(conn: sqlite3.Connection, bundle: dict[str, list[dict[str, Any]]]) -> None:
    for row in bundle["seed_import_runs"]:
        conn.execute(
            """
            insert into seed_import_run (
                id, organization_id, import_family, manifest_code, source_id,
                started_at, completed_at, status, row_count, error_count, notes, metadata_json
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["id"],
                row.get("organization_id"),
                row["import_family"],
                row["manifest_code"],
                row.get("source_id"),
                row["started_at"],
                row["completed_at"],
                row["status"],
                row["row_count"],
                row["error_count"],
                row.get("notes"),
                _to_json_text(row.get("metadata_json", {})),
            ),
        )
    for error in bundle["seed_import_errors"]:
        conn.execute(
            """
            insert into seed_import_error (
                id, seed_import_run_id, import_family, manifest_code, row_identifier,
                error_code, error_message, payload_json, created_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                error["id"],
                error.get("seed_import_run_id"),
                error["import_family"],
                error["manifest_code"],
                error.get("row_identifier"),
                error["error_code"],
                error["error_message"],
                _to_json_text(error.get("payload_json", {})),
                error["created_at"],
            ),
        )
    conn.commit()


def insert_source_mirror_bundle(conn: sqlite3.Connection, bundle: dict[str, list[dict[str, Any]]]) -> None:
    run_by_source: dict[str, dict[str, Any]] = {}

    for row in bundle["indexed_source_document"]:
        retrieved_at = row["retrieved_at"]
        conn.execute(
            """
            insert into indexed_source_document (
                source_code, title, source_url, source_type, authority_type,
                jurisdiction_scope, effective_hint, retrieved_at, status,
                indexed_extract, normalization_targets, seed_priority, notes,
                metadata_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["source_code"],
                row["title"],
                row["source_url"],
                row["source_type"],
                row["authority_type"],
                _to_json_text(row.get("jurisdiction_scope", [])),
                row.get("effective_hint"),
                retrieved_at,
                row["status"],
                _to_json_text(row.get("indexed_extract", {})),
                _to_json_text(row.get("normalization_targets", [])),
                row["seed_priority"],
                row.get("notes"),
                _to_json_text(row.get("metadata_json", {})),
                row.get("created_at", retrieved_at),
                row.get("updated_at", retrieved_at),
            ),
        )

    for row in bundle["source_mirror_asset"]:
        conn.execute(
            """
            insert into source_mirror_asset (
                source_code, asset_kind, asset_storage_key, asset_mime_type, checksum_sha256,
                byte_size, mirrored_at, parser_status, metadata_json
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["source_code"],
                row["asset_kind"],
                row["asset_storage_key"],
                row["asset_mime_type"],
                row["checksum_sha256"],
                row.get("byte_size"),
                row["mirrored_at"],
                row["parser_status"],
                _to_json_text(row.get("metadata_json", {})),
            ),
        )

    for row in bundle["source_parse_run"]:
        run_by_source[row["source_code"]] = row
        conn.execute(
            """
            insert into source_parse_run (
                source_code, parser_code, parser_version, parse_family, status,
                started_at, completed_at, input_asset_ids, parsed_row_counts,
                promoted_row_counts, metadata_json
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["source_code"],
                row["parser_code"],
                row["parser_version"],
                row["parse_family"],
                row["status"],
                row["started_at"],
                row.get("completed_at"),
                _to_json_text(row.get("input_asset_ids", [])),
                _to_json_text(row.get("parsed_row_counts", {})),
                _to_json_text(row.get("promoted_row_counts", {})),
                _to_json_text(row.get("metadata_json", {})),
            ),
        )

    for row in bundle["source_parse_error"]:
        run = run_by_source.get(row["source_code"])
        conn.execute(
            """
            insert into source_parse_error (
                source_code, source_parse_run_source_code, row_ref, field_name, error_code,
                error_message, raw_value, payload_json, created_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["source_code"],
                run["source_code"] if run else None,
                row.get("row_ref"),
                row.get("field_name"),
                row["error_code"],
                row["error_message"],
                row.get("raw_value"),
                _to_json_text(row.get("payload_json", {})),
                row["created_at"],
            ),
        )

    for row in bundle["fee_schedule_source"]:
        run = run_by_source.get(row["source_code"])
        conn.execute(
            """
            insert into fee_schedule_source (
                source_code, jurisdiction_code, authority_type, title, source_url,
                effective_start, effective_end, retrieved_at, source_cycle,
                parse_run_source_code, metadata_json
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["source_code"],
                row["jurisdiction_code"],
                row["authority_type"],
                row["title"],
                row["source_url"],
                row.get("effective_start"),
                row.get("effective_end"),
                row["retrieved_at"],
                row.get("source_cycle"),
                run["source_code"] if run else None,
                _to_json_text(row.get("metadata_json", {})),
            ),
        )

    for row in bundle["fee_schedule_entry"]:
        conn.execute(
            """
            insert into fee_schedule_entry (
                source_code, jurisdiction_code, fee_family, fee_code, fee_label, fee_basis_type,
                fee_amount, currency_code, uom, formula_notes, qualifier_notes,
                effective_start, effective_end, metadata_json
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["source_code"],
                row["jurisdiction_code"],
                row["fee_family"],
                row["fee_code"],
                row["fee_label"],
                row["fee_basis_type"],
                row.get("fee_amount"),
                row.get("currency_code", "USD"),
                row.get("uom"),
                row.get("formula_notes"),
                row.get("qualifier_notes"),
                row.get("effective_start"),
                row.get("effective_end"),
                _to_json_text(row.get("metadata_json", {})),
            ),
        )

    conn.commit()


def insert_search_documents(conn: sqlite3.Connection, documents: list[dict[str, Any]]) -> None:
    for row in documents:
        conn.execute(
            """
            insert into search_documents (
                organization_id, object_type, object_id, title, subtitle, body_text,
                search_key, facets_json, payload_json, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("organization_id"),
                row["object_type"],
                row["object_id"],
                row["title"],
                row.get("subtitle"),
                row.get("body_text"),
                row["search_key"],
                _to_json_text(row.get("facets_json", {})),
                _to_json_text(row.get("payload_json", {})),
                row["updated_at"],
            ),
        )
    conn.commit()
