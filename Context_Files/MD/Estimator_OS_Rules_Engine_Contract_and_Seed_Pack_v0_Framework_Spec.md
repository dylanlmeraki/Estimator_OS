---
title: "Estimator OS"
subtitle: "Rules Engine Contract + Seed Pack v0 Framework Spec"
date: "March 25, 2026"
---

# 0 Purpose

This document locks the implementation contract for two linked workstreams:

1. the **rules engine** used for jurisdictional fees, labor mode, public-works obligations, proposal notes, and publish blockers; and
2. the **seed-pack v0 framework** used to ingest wages, apprenticeship obligations, equipment rates, and materials-source evidence into Estimator OS without creating parallel pricing systems.

This spec is intentionally narrower than a full admin platform. It is designed to let Estimator OS ship with a stable, auditable rule and pricing substrate while keeping room for deeper data growth later.

# 1 Decisions locked by this spec

## 1.1 Rules authoring and execution

- **External authoring model:** form-driven admin UI for internal operators, not freeform text authoring for end users.
- **Internal interchange format:** YAML allowed for developer import/export and fixture authoring.
- **Canonical stored rule format:** validated JSON conforming to a strict JSON Schema.
- **Execution IR:** compiled JSONLogic.
- **Compiler output:** canonical JSON, compiled JSONLogic, compile hash, schema version, author metadata, and source snapshot.
- **Evaluation persistence:** every evaluation pins `template_version_id` and stores input/output snapshots.

## 1.2 Search

- **MVP search strategy:** PostgreSQL FTS + `pg_trgm` similarity.
- **Operational search table:** `search_documents` remains the denormalized read model.
- **No external search infra at MVP:** no Elastic/OpenSearch unless operational evidence later proves need.

## 1.3 Pricing evidence strategy

- **Canonical public-works wage source:** DIR prevailing wage determinations and apprentice menus.
- **Supplemental sources:** union rate sheets, internal T+M books, vendor quotes, market benchmarks.
- **Canonical equipment seed source:** Caltrans Labor Surcharge & Equipment Rental Rate Book CSV.
- **Canonical materials strategy:** curated source observations from local/regional vendors with location scope, source confidence, and effective dating.
- **Canonical execution tables:** existing `rate_books`, `rate_book_entries`, `labor_rate_profiles`, `quotes`, and related pricing tables remain the only tables the estimate builder should price from.
- **Seed tables are evidence/staging tables:** they populate or refresh canonical execution tables; they do not bypass them.

# 2 Rules engine contract

## 2.1 Why Estimator OS needs this exact structure

The product needs deterministic, auditable logic for:

- jurisdictional permit and fee placeholders,
- public-works labor mode and apprenticeship obligations,
- proposal-note generation,
- publish blockers and warnings,
- field-evidence routing,
- and future open-bid qualification logic.

Those use cases require version pinning, reproducibility, and effective dating. They do **not** require a general-purpose programming language.

## 2.2 Authoring architecture

```text
Admin UI / Fixture YAML
        -> DSL JSON (schema-validated)
        -> compiler
        -> canonical JSON
        -> compiled JSONLogic
        -> evaluation runtime
        -> persisted evaluation snapshots
```

### Authoring layers

| Layer | Audience | Purpose | Editable by end users? |
|---|---|---|---|
| Form-driven UI | internal admins / ops | safe authoring and revision management | yes |
| YAML fixture | developers / internal migration tooling | seed packs, import/export, test fixtures | no |
| Canonical JSON | application runtime | single persisted rule source | no |
| JSONLogic | runtime evaluator | deterministic execution IR | no |

## 2.3 Core rule capabilities

The DSL must cover exactly these categories in v0:

- `applicable_if`
- `required_inputs`
- `outputs.placeholders`
- `outputs.generated_notes`
- `outputs.generated_tasks`
- `blockers`
- `warnings`
- `proposal_includes`
- `handoff_annotations`

### Explicit non-goals

- loops
- network calls
- dynamic I/O during evaluation
- arbitrary script execution
- mutation side effects during evaluation
- freeform formulas outside the approved expression set

## 2.4 Canonical JSON Schema shape

The following is the recommended canonical JSON shape for a rule template version.

```json
{
  "schemaVersion": "1.0.0",
  "driverCode": "sf_dbi_fee",
  "displayName": "San Francisco DBI fee placeholder",
  "jurisdictionScope": {
    "state": "CA",
    "county": ["San Francisco"],
    "city": ["San Francisco"]
  },
  "effectiveStart": "2026-01-01",
  "effectiveEnd": null,
  "sourceRefs": [
    {
      "title": "SF DBI Fee Schedule",
      "url": "https://www.sf.gov/resource--2022--fees-department-building-inspection/",
      "retrievedAt": "2026-03-25T00:00:00Z"
    }
  ],
  "requiredInputs": [
    {"key": "valuation", "type": "number", "required": true},
    {"key": "permitCategory", "type": "enum", "required": true}
  ],
  "applicableIf": {
    "all": [
      {"eq": [{"var": "opportunity.jurisdictionPreset"}, "sf"]},
      {"gt": [{"var": "inputs.valuation"}, 0]}
    ]
  },
  "outputs": {
    "placeholders": [],
    "generatedNotes": [],
    "generatedTasks": []
  },
  "warnings": [],
  "blockers": []
}
```

## 2.5 YAML fixture form (developer/internal only)

```yaml
schemaVersion: 1.0.0
driverCode: sf_dbi_fee
displayName: San Francisco DBI fee placeholder
jurisdictionScope:
  state: CA
  county: [San Francisco]
  city: [San Francisco]
effectiveStart: 2026-01-01
sourceRefs:
  - title: SF DBI Fee Schedule
    url: https://www.sf.gov/resource--2022--fees-department-building-inspection/
    retrievedAt: 2026-03-25T00:00:00Z
requiredInputs:
  - key: valuation
    type: number
    required: true
applicableIf:
  all:
    - eq: [{var: opportunity.jurisdictionPreset}, sf]
    - gt: [{var: inputs.valuation}, 0]
outputs:
  placeholders:
    - when:
        eq: [{var: opportunity.projectType}, building]
      addLineItem:
        sectionKey: permits
        description: SF DBI permit fee placeholder
        pricingMode: formula
        formulaRef: sf_dbi_fee_table_v2026
warnings: []
blockers:
  - when:
      not: {var: inputs.valuation}
    code: missing_valuation
    message: Valuation is required to compute the placeholder.
```

## 2.6 Compiler contract

### Inputs

- YAML fixture **or** admin UI payload
- target schema version
- rule metadata (author, organization, note)

### Outputs

- validated canonical JSON
- compiled JSONLogic
- normalized source JSON string
- `compile_hash`
- validation warnings list
- compile error list (empty on success)

### Determinism requirements

- identical canonical JSON must produce identical JSONLogic and identical `compile_hash`
- compiler must sort unordered collections before hashing
- all date-based behavior must use injected `effective_date`, never runtime `now()`

### Suggested hash inputs

```text
hash = SHA256(
  schemaVersion +
  canonicalJson +
  compilerVersion +
  normalizationVersion
)
```

## 2.7 Evaluation lifecycle

### Evaluation states

- `not_applicable`
- `applicable`
- `generated`
- `warning`
- `blocked`
- `overridden`
- `superseded`

### Persist per evaluation

- `template_version_id`
- `compile_hash`
- `evaluation_hash`
- `input_snapshot`
- `output_snapshot`
- `warning_snapshot`
- `blocker_snapshot`
- `confirmed_by`
- `override_reason`
- `evaluated_at`

### Evaluation hash

```text
evaluation_hash = SHA256(
  template_version_id +
  compile_hash +
  input_snapshot +
  output_snapshot
)
```

## 2.8 Safety guardrails

- no loops
- no file/network access
- no mutation side effects in evaluator
- all evaluation inputs must be passed explicitly
- all output actions must write to typed output payloads, not execute code
- any override requires actor + reason + timestamp

# 3 Seed pack v0 framework

## 3.1 Objective

Seed pack v0 provides enough structured data to support:

- public-works wage mode,
- apprenticeship obligation checks,
- basic T+M labor profiles,
- equipment rental placeholders,
- materials-source evidence,
- and permit/fee placeholders

without pretending to be a fully exhaustive Bay Area cost database.

## 3.2 Seed pack principles

1. **Official source first where official sources exist.**
2. **Local vendor observations supplement, not replace, official/public-works references.**
3. **Every seed row carries source provenance and retrieval timing.**
4. **Execution tables stay normalized and small; source evidence tables may be broader.**
5. **Seed packs are fixtures, not manual database edits.**

## 3.3 Source hierarchy by domain

| Domain | Canonical source | Supplemental source | Execution target |
|---|---|---|---|
| Public-works wages | DIR determinations and apprentice menus | union sheets, org overrides | `wage_determinations`, `labor_rate_profiles` |
| Apprenticeship obligations | DIR DAS apprenticeship requirements + ratio rules | program standards references | `apprentice_ratio_rules`, checklist note templates |
| Equipment rates | Caltrans rental rate CSV | local rental yard policies for delivery or retail rental context | `equipment_rate_entries`, selected `rate_book_entries` |
| Materials pricing | local vendor observations and quotes | internal org books, promotions, benchmarks | `material_source_prices`, selected `rate_book_entries` |
| Regulatory fees | jurisdiction rule templates + source refs | internal estimating defaults | compliance evaluations + fee placeholder outputs |

# 4 Wage seed pack v0

## 4.1 Scope

Seed public-works wage mode for the first Northern California/Bay Area implementation using DIR as canonical legal reference.

### Required components

- journeyman determinations by county/craft/classification
- apprentice determinations where applicable
- determination cycle metadata
- base wage and fringe breakdown fields where available
- public-works wage-mode applicability references
- optional org-level private T+M multipliers / labor profiles stored separately

## 4.2 Source strategy

### Canonical

- DIR prevailing wage determination menus and craft detail pages
- DIR apprentice determination menus

### Supplemental

- union wage sheets / CBA summaries as attachments or notes
- org-specific T+M labor books
- benchmark / estimation-only market profiles

## 4.3 Recommended wage tables

### `wage_sources`
Stores the provenance of imported wage data.

### `wage_determinations`
Stores determination header rows: county, craft, classification, cycle, effective dates.

### `wage_rate_components`
Stores base and fringe components.

### `apprentice_progressions`
Stores apprentice period/step and corresponding rates or percentages.

### `apprentice_ratio_rules`
Stores minimum/maximum ratios and obligation notes.

### `training_fund_obligations`
Stores whether CAC or committee contribution notes should be emitted.

## 4.4 Construction-logic translation

The product should support these interpretations:

- Public works at or above threshold triggers apprenticeship obligation logic.
- Requirement applies by craft and is tied to straight-time journeyman hours.
- The minimum ratio is 1 apprentice hour for every 5 straight-time journeyman hours.
- DAS 140 and DAS 142 requirements should appear as checklist/task/proposal-note outputs where configured.
- Private T+M mode should not reuse DIR wages as “truth”; it should use `labor_rate_profiles` tied to an org or market profile.

# 5 Equipment seed pack v0

## 5.1 Scope

Seed one public-works-credible equipment rate source and one local retail/rental-context supplement.

### Canonical

- Caltrans Labor Surcharge & Equipment Rental Rate Book CSV

### Supplemental

- local rental yard delivery policies and non-Caltrans rental context references

## 5.2 Recommended tables

### `equipment_rate_books`
Header for a source book by effective window.

### `equipment_classes`
Normalized equipment taxonomy.

### `equipment_rate_entries`
Detailed rate rows by book, code, unit, and period.

### `equipment_delivery_policies`
Optional local rental delivery/pickup policies.

## 5.3 Execution alignment

- Public-works equipment placeholders may derive directly from `equipment_rate_entries`.
- Non-public-works execution can optionally map selected rows into `rate_book_entries` or create vendor/rental quote placeholders instead.
- Caltrans-origin rates must preserve effective date and source attribution.

# 6 Materials seed pack v0

## 6.1 Scope

Materials seed pack v0 should be intentionally curated. Do not attempt a complete Bay Area cost book.

### Seed categories recommended

- concrete and masonry accessories
- rebar accessories and reinforcement consumables
- ADA / safety / traffic-control consumables
- erosion-control / SWPPP consumables
- demolition consumables and disposal-related placeholders
- site concrete / curb-ramp / utility restoration materials
- common rental- and construction-adjacent tools or consumables where public prices exist

## 6.2 Vendor-source registry model

### `vendor_source_registry`
Stores branch-aware vendor source records.

Recommended fields:

- `vendor_code`
- `vendor_name`
- `branch_name`
- `branch_city`
- `location_scope`
- `source_type` (`public_price`, `public_catalog`, `quote_only`, `account_price`, `rental_policy`)
- `base_url`
- `price_confidence` (`high`, `medium`, `low`, `quote_required`)
- `last_verified_at`

### `material_catalog_items`
Normalized internal item taxonomy.

### `material_source_prices`
Observed source prices by vendor/location/effective date.

## 6.3 Price confidence rules

| Confidence | Meaning | Use in execution |
|---|---|---|
| high | explicit public price on source page, directly observed | can seed `rate_book_entries` |
| medium | explicit public price but location variance or unclear branch scope | seed with warning / confirmation needed |
| low | indirect or stale source | evidence only, do not auto-price |
| quote_required | public source indicates variance or no stable public price | create placeholder / quote task, do not auto-price |

## 6.4 Execution alignment

- `material_source_prices` are evidence rows.
- approved seed transformations may create curated `rate_book_entries`.
- the estimate builder prices from `rate_book_entries` or quotes, not from raw scrape rows.
- vendor/location metadata must remain visible in provenance.

# 7 Fixture pack layout

## 7.1 File layout recommendation

```text
seed-packs/
  rules/
    sf_core/
      rule_templates.yaml
      source_manifest.json
    san_mateo_publicworks/
      rule_templates.yaml
    caltrans_lpa/
      rule_templates.yaml
  wages/
    dir/
      2025-1_journeyman/
        manifest.json
        raw/
        normalized/
      2025-2_journeyman/
        manifest.json
      apprentice/
        manifest.json
    supplemental_union/
      incoming/
  equipment/
    caltrans/
      2025-04-01_to_2026-03-31/
        rental_rates.csv
        manifest.json
  materials/
    vendor_sources/
      white_cap/
        catalog_snapshot.json
        manifest.json
      action_rentals/
        policy_snapshot.json
        manifest.json
  transform/
    maps/
    tests/
```

## 7.2 Manifest fields

Every imported pack should include:

- `pack_id`
- `pack_type`
- `source_name`
- `source_url`
- `retrieved_at`
- `effective_start`
- `effective_end`
- `normalizer_version`
- `row_count`
- `hash`
- `review_status`

# 8 Exact data-model additions (logical)

## 8.1 New logical entities required

- `wage_sources`
- `wage_determinations`
- `wage_rate_components`
- `apprentice_progressions`
- `apprentice_ratio_rules`
- `training_fund_obligations`
- `equipment_rate_books`
- `equipment_classes`
- `equipment_rate_entries`
- `equipment_delivery_policies`
- `vendor_source_registry`
- `material_catalog_items`
- `material_source_prices`
- `source_import_runs`
- `source_import_errors`

## 8.2 Alignment with existing canonical execution tables

### Existing execution tables that remain authoritative

- `rate_books`
- `rate_book_entries`
- `labor_rate_profiles`
- `quotes`
- `compliance_driver_templates`
- `compliance_evaluations`

### Source-to-execution pipeline

```text
raw source pack
 -> source import tables
 -> normalized evidence tables
 -> curated transforms / approvals
 -> canonical execution tables
 -> estimate builder / proposal / handoff
```

This is the key anti-sprawl rule. Source evidence tables do not replace pricing execution tables.

# 9 Implementation sequencing

## 9.1 First implementation slice

1. lock rules engine contract and compiler outputs
2. add wage source + determination + ratio tables
3. add equipment rate book ingestion path
4. add vendor source registry + material source price tables
5. add seed transforms into `rate_book_entries` and `labor_rate_profiles`
6. add proposal-note generation and checklist hooks for apprenticeship and jurisdiction packs

## 9.2 What to defer

- large-scale vendor scraping
- dynamic pricing refresh automation
- advanced market benchmark logic
- full union-sheet normalization across all trades
- highly granular foreman/superintendent composition rules beyond baseline labor profiles
- predictive pricing models

# 10 Source maintenance policy

## 10.1 Refresh cadence

| Source class | Cadence | Owner |
|---|---|---|
| DIR determinations | at each determination cycle and when important notices change | compliance/data owner |
| apprenticeship rules | quarterly or upon DIR updates | compliance owner |
| Caltrans equipment CSV | each new effective book period and when misc rates are relevant | pricing/data owner |
| vendor public prices | monthly or when pilot categories materially move | pricing ops |
| local delivery/rental policies | quarterly or when vendor pages change | ops |

## 10.2 Required operational controls

- all imports create `source_import_runs`
- all normalization creates warnings for malformed rows
- all execution transforms are reviewed before becoming active defaults
- public-source-derived entries with location variance should default to warning or `quote_required`

# 11 Immediate build actions

1. approve the canonical rule contract in Sections 2–3.
2. add the source evidence tables listed in Section 8.
3. ingest DIR + apprenticeship + Caltrans seed packs first.
4. curate a top 100–300 materials list and populate `vendor_source_registry` + `material_source_prices`.
5. map approved evidence rows into `rate_book_entries` and `labor_rate_profiles`.
6. wire publish-readiness and proposal generation to rule evaluation outputs.

# Appendix A — Source references used to shape v0

- California DIR prevailing wage determinations and apprentice menus
- California DIR apprenticeship/public works guidance and minimum ratio references
- Caltrans Labor Surcharge & Equipment Rental Rate Book page and CSV references
- White Cap public product pricing pages noting location-based pricing variance
- Action Rentals delivery policy page for local delivery-cost logic
