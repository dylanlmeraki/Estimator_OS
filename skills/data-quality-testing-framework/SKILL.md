---
name: data-quality-testing-framework
description: "Profile and validate CSV/JSON data quality for ingestion pipelines. Use when onboarding new source files, debugging import failures, or enforcing schema and completeness checks."
argument-hint: "Data folder path and scope (optional)"
---

# Data Quality Testing Framework

Run a lightweight, repeatable quality pass on ingestion datasets before they enter normalized tables.

## When to use

- New source CSV or manifest is introduced.
- Import pipeline reports row-level validation errors.
- You need confidence checks before publish/readiness workflows.
- You want deterministic fixture health checks in CI.

## Primary targets

- Source registries (`*.csv`)
- Import manifests (`*.json`)
- Rule fixtures (`*.yaml`, canonical rule JSON)
- SQL seed mappings and normalized table assumptions

## Procedure

### 1. Profile files

- Confirm encoding, delimiter, and header consistency.
- Count rows and detect duplicate natural keys.
- Identify null-heavy columns and outlier values.

### 2. Validate structure

- Validate JSON against JSON Schema where available.
- Validate required CSV columns by registry type.
- Check enum and type compatibility for key fields.

### 3. Run rule-based quality checks

- Required field completeness checks.
- Referential consistency across related files.
- Effective date window sanity checks.
- Confidence/state policy checks (for pricing evidence rows).

### 4. Produce actionable output

- Summary by file: pass/warn/fail.
- Row-level error list with stable identifiers.
- Recommended fixes grouped by severity.
- Optional CI-friendly exit status rules.

## Suggested outputs

- `data-quality-summary.md`
- `data-quality-errors.json`
- `data-quality-metrics.json`

## Guardrails

- Keep evidence tables separate from canonical pricing tables.
- Do not auto-correct silently; report and require explicit transforms.
- Preserve raw row payload references in failures.
- Keep checks deterministic across repeated runs.

## Optional tooling

- Minimal Python checks (`csv`, `json`, `pyyaml`).
- Optional advanced profiling with Great Expectations or Pandera.
- CI step for fixture pack validation.

