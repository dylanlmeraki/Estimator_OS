# Seed-pack DTO notes

Use these DTOs as first-pass API payload shapes for the Codex build pass.

## Primary endpoints to add
- `POST /v1/rules:compile`
- `POST /v1/rules:evaluate`
- `POST /v1/seed-import-runs`
- `POST /v1/seed-import-runs/{id}:complete`
- `POST /v1/material-catalog:bulkUpsert`
- `GET /v1/search?q=...&types=...`

## Key payload files
- `seed_pack_dto_examples.json`
- `schemas/canonical_rule.schema.json`
- `schemas/rule_evaluation.schema.json`

## Notes
- Keep compile and evaluation requests idempotent by hash when possible.
- Store source evidence separately from canonical rate books and labor profiles.
- Allow `organization_id` to be null on official seed rows so a shared catalog can exist before tenant-specific copies are materialized.
