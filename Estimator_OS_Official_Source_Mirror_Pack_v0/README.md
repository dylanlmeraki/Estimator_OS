# Estimator.OS Fixture Pack v0

This package is the project-starter bundle for Codex and first-pass engineering work.

## Included
- `schemas/` — canonical JSON Schemas for rules and rule evaluations
- `examples/` — example canonical rule JSON files
- `seedpacks/rules/` — starter YAML rule seed packs (developer/internal format)
- `seedpacks/manifests/` — ingestion manifests for DIR, Caltrans, and curated materials
- `seedpacks/sources/` — starter CSV fixtures and source registries
- `sql/` — additive PostgreSQL DDL for seed/source evidence models
- `dto/` — DTO examples and API notes
- `compiler/` — compiler contract
- `docs/` — build-scope and handoff notes

## Source-of-truth flow
official/public source -> source evidence tables -> operator review / normalization -> canonical execution tables (rate_books, rate_book_entries, labor_rate_profiles) -> evaluations / proposals / handoff

## Why this structure
It preserves:
- deterministic rule execution via JSONLogic
- effective-dated source evidence
- quote/vendor/location-aware pricing
- reproducible evaluation snapshots
- no parallel pricing engine

## Minimum first-pass build goal
Implement the compiler/evaluation contract, seed-source DDL, import-run scaffolding, and one end-to-end seed flow:
1. compile `dir_public_works_apprenticeship.yaml`
2. ingest sample source registries
3. create one `wage_source` / `apprentice_ratio_rule`
4. run a rule evaluation and persist the snapshot
5. expose it in search documents
