# Rules Engine Contract (v0)

## Intent
Estimator.OS rules are **UI-authored**, stored as **canonical JSON**, optionally round-tripped through **internal YAML**, and executed via **compiled JSONLogic**.

## Authoring contract
- External user interaction happens in UI forms / condition builders / checklist editors.
- YAML is **internal/developer-only** import-export and fixture format.
- Canonical persistence format is **JSON** validated by `schemas/canonical_rule.schema.json`.
- Execution IR is **JSONLogic** embedded under `compiled.jsonlogic`.

## Compile pipeline
1. Parse UI-authored JSON or YAML seed input.
2. Validate against constrained authoring spec.
3. Canonicalize:
   - sort object keys
   - normalize booleans/numbers/enums
   - drop empty/null optional fields
4. Emit canonical rule JSON.
5. Compile to JSONLogic IR.
6. Compute `compile_hash = sha256(canonical_jsonlogic_payload)`.
7. Persist:
   - authoring artifact reference
   - canonical rule JSON
   - compiled JSONLogic
   - compiler version
   - compile hash
   - canonical sha256
8. At runtime, pin:
   - `template_version`
   - `compile_hash`
   - `effective_date`
   - `input_snapshot`
   - `output_snapshot`
   - `evaluation_hash`

## Non-goals
- No loops
- No network calls
- No writes/side effects in rule execution
- No dynamic clock access except injected `effective_date`
- No arbitrary scripting

## Runtime expectations
- Deterministic execution only
- Rule results may generate:
  - line-item placeholders
  - proposal notes
  - derived fields
  - publish blockers/warnings
  - operational flags
- Rules do **not** directly mutate published versions.

## Hashing
- Use UTF-8 JSON serialization with sorted keys and compact separators.
- `compile_hash` hashes the compiled execution payload.
- `evaluation_hash` hashes `{rule_id, template_version, compile_hash, effective_date, input_snapshot, output_snapshot}`.

## Evaluation statuses
- `generated`
- `warning`
- `blocked`
- `confirmed`
- `overridden`
- `not_applicable`

## Override contract
Overrides must always capture:
- actor id
- timestamp
- reason code
- freeform note
- superseded output fragment reference

## Search integration
Rules and evaluation objects should be denormalized into `search_documents` so users can find:
- blocked versions
- rules affecting a pursuit
- warning codes
- quote/compliance intersections
