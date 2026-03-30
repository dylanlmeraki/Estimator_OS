---
name: api-documentation-generation
description: "Generate and maintain API documentation from implementation and contracts. Use when creating or updating endpoints, request/response DTOs, or acceptance criteria."
argument-hint: "API module path or docs target path (optional)"
---

# API Documentation Generation

Generate concise, implementation-aligned API docs from code and contract files with minimal drift.

## When to use

- New endpoint is added or endpoint behavior changes.
- Request/response schema changes and docs need sync.
- You need quick internal docs for review, QA, or handoff.
- You want a release note style endpoint delta summary.

## Inputs to inspect

- Endpoint/controller/router files.
- DTO/schema files.
- Acceptance criteria and behavior notes.
- Existing docs in `README.md`, `docs/`, and OpenAPI artifacts.

## Procedure

### 1. Discover API surface

- List endpoint files and route definitions.
- Identify method, path, auth requirements, and ownership.
- Capture current request/response contracts from code.

### 2. Extract contract details

- Request body/query/path fields and validation rules.
- Response status codes and payload shapes.
- Error contracts and idempotency behavior where present.
- Versioning or compatibility notes.

### 3. Generate doc artifacts

- Create or update endpoint reference markdown.
- Include example request/response payloads.
- Add a change summary section for net-new and modified endpoints.
- Link docs back to source files.

### 4. Validate alignment

- Ensure examples match implementation field names and enums.
- Flag any behavior that is undocumented or ambiguous.
- Keep docs additive; do not remove historical notes without reason.

## Recommended output structure

- Overview
- Auth and tenancy scope
- Endpoint reference table
- Detailed endpoint sections
- Error handling
- Idempotency and immutability notes
- Changelog delta

## Guardrails

- Prefer implementation truth over stale docs.
- Do not invent undocumented response fields.
- Call out uncertain behavior as a TODO, not a fact.
- Keep examples deterministic and copy-paste runnable.

## Suggested follow-up checks

- Add/update contract tests for changed endpoints.
- Regenerate OpenAPI when applicable.
- Add docs link in PR description for reviewer context.

