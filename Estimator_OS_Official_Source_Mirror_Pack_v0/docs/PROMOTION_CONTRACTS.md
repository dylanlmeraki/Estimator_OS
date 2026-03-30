# Promotion Contracts (Parsed -> Canonical)

This document defines deterministic mappings from parsed source-evidence rows into canonical seed tables.

## Guardrails

- Never promote directly from unparsed mirror assets.
- Never bypass `indexed_source_document` provenance fields.
- Never overwrite active canonical rows silently; append effective-dated versions.
- Preserve `source_code` and `indexed_source_document_id` on promoted rows.

## Contract: DIR wage pages -> canonical wage seeds

Parsed source tables:
- `indexed_source_document`
- `source_mirror_asset`
- `source_parse_run`

Promotion targets:
- `wage_source`
- `wage_determination`
- `apprentice_ratio_rule`

Required provenance mapping:
- `wage_source.source_code` <- indexed `source_code`
- `wage_source.indexed_source_document_id` <- indexed `id`
- `apprentice_ratio_rule.source_code` <- indexed `source_code`
- `apprentice_ratio_rule.indexed_source_document_id` <- indexed `id`

## Contract: SF Public Works fee schedule PDF -> fee schedule seeds

Parsed source tables:
- `fee_schedule_source`
- `fee_schedule_entry`

Promotion targets:
- `jurisdiction_rule_template` candidates for fee placeholders
- `proposal_note_template` candidates

Required provenance mapping:
- `fee_schedule_source.source_code` <- indexed `source_code`
- `fee_schedule_entry.source_code` <- indexed `source_code`
- `fee_schedule_entry.indexed_source_document_id` <- indexed `id`

## Contract: BAAQMD Rule 11-2 PDF -> regulatory trigger candidates

Parsed output targets:
- `jurisdiction_rule_template` candidates
- `checklist_template` candidates
- `proposal_note_template` candidates

Rules:
- Emit trigger/checklist/proposal-note candidates only.
- Do not emit direct fee line entries.
- Keep exception text in candidate metadata for manual review.

## Contract: Caltrans equipment CSV -> equipment seeds

Parsed source tables:
- `equipment_rate_book`
- `equipment_rate_entry`

Promotion targets:
- canonical rate-book-driven pricing tables (`rate_book`, `rate_book_entry`) in later pass

Required provenance mapping:
- `equipment_rate_book.source_code` <- indexed `source_code`
- `equipment_rate_book.indexed_source_document_id` <- indexed `id`
- `equipment_rate_entry.raw_line_json` must retain source row snapshot

## Contract: Vendor price observations -> material evidence

Parsed source tables:
- `vendor_source_registry`
- `material_price_observation`

Rules:
- keep confidence/location scoped evidence
- do not auto-promote low-confidence or quote-required observations
- preserve `material_catalog_item_identity` and source metadata on every row

