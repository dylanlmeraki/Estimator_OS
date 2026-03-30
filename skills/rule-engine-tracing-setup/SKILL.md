---
name: rule-engine-tracing-setup
description: "Instrument rule compilation and evaluation with trace-friendly events and timing. Use when debugging rule execution paths, blockers/warnings, or performance regressions."
argument-hint: "Rule engine module path (optional)"
---

# Rule Engine Tracing Setup

Add practical tracing for the compile/evaluate lifecycle so rule behavior is observable and reproducible.

## When to use

- You need to debug which rule path produced a blocker/warning.
- Evaluation latency or throughput needs measurement.
- Compile hash or evaluation hash drift is suspected.
- You need evidence-grade execution traces for audits/reviews.

## Trace model

Track these pipeline stages explicitly:

1. load_rule_document
2. normalize_authoring_document
3. build_canonical_rule
4. build_compiled_ir
5. validate_canonical_rule
6. emit_compile_artifact
7. evaluate_rule_snapshot

## Procedure

### 1. Add trace context

- Generate or propagate `trace_id` / `request_id`.
- Include `organization_id`, `rule_id`, `template_version`.
- Attach `compile_hash` and `evaluation_hash` when available.

### 2. Instrument compile phase

- Emit start/end events per stage.
- Capture duration and success/failure state.
- Log validation failures with rule identifiers, not raw secrets.

### 3. Instrument evaluate phase

- Record applicability decision and status output.
- Capture blocker/warning counts and codes.
- Include deterministic snapshots references (not oversized payload dumps).

### 4. Persist minimal trace records

- Keep trace rows/queryable logs for local diagnostics.
- Ensure events are tenant-scoped and correlation-friendly.
- Support replay: same inputs should reproduce same hash path.

## Suggested event fields

- `timestamp`
- `trace_id`
- `stage`
- `organization_id`
- `rule_id`
- `template_version`
- `compile_hash`
- `evaluation_hash`
- `status`
- `duration_ms`
- `error_code` (nullable)

## Guardrails

- Do not mutate business state from tracing code.
- Avoid logging sensitive full payloads unless redacted.
- Keep overhead low; tracing must not materially slow evaluation.
- Preserve deterministic hashing semantics.

## Success criteria

- A single evaluation can be traced stage-by-stage end to end.
- Failed evaluations expose stage and reason quickly.
- Hash drift investigations can be performed without guesswork.

