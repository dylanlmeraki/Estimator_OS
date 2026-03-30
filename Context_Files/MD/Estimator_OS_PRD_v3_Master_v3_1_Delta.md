---
title: "Estimator OS"
subtitle: "PRD v3.1 Master — Rules/Search/Pricing Seed Delta"
date: "March 25, 2026"
---

# 0 Purpose

This is a focused additive delta to the existing Master PRD v3. It does not alter the thesis or scope boundary. It locks three implementation decisions and adds the minimum new product requirements required to operationalize them:

1. rules engine contract,
2. search contract,
3. pricing evidence seed-pack model for wages, equipment, and materials.

# 1 Decisions now locked in the master PRD

## 1.1 Rule engine decision

The master PRD should now explicitly state:

- end users do **not** author raw rules;
- internal admins author rule templates through a UI;
- YAML is allowed as developer/internal import-export only;
- canonical stored rules are JSON validated by JSON Schema;
- runtime execution uses compiled JSONLogic;
- all evaluations pin `template_version_id` and persist snapshots.

## 1.2 Search decision

The master PRD should now explicitly state:

- search is implemented using PostgreSQL full-text search plus `pg_trgm` similarity;
- search runs on a tenant-scoped `search_documents` read model;
- search covers opportunities, sheets, takeoff groups, estimate versions, quotes, evaluations, and handoff records;
- no external search infrastructure is required for MVP or immediate post-MVP hardening.

## 1.3 Pricing seed strategy decision

The master PRD should now explicitly state:

- public-works wage logic uses DIR as canonical source;
- union sheets are supplemental evidence, not the canonical legal basis;
- equipment seed rates use Caltrans CSV ingestion;
- materials seed packs use curated vendor-source evidence with price confidence and location scope;
- execution pricing still flows through canonical `rate_book_entries`, `labor_rate_profiles`, and quote objects.

# 2 Requirements text to add to the master PRD

## 2.1 Rules engine requirements

The system shall:

- support a typed rule template schema with effective dating and source references;
- store a canonical JSON form of each rule template version;
- compile canonical rule JSON to JSONLogic before evaluation;
- persist compile hash and evaluation hash for every evaluation run;
- persist input, output, warning, blocker, and override snapshots for each evaluation;
- support admin-UI authoring for rule templates;
- allow YAML import/export for internal developer and data-ops workflows only;
- prohibit side effects, loops, external fetches, and non-deterministic runtime constructs in rule evaluation.

## 2.2 Search requirements

The system shall:

- maintain a denormalized `search_documents` read model;
- index search documents using both FTS and trigram similarity;
- support tenant-scoped search across opportunities, plan artifacts, takeoff groups, estimate versions, quotes, compliance evaluations, and handoff jobs;
- expose structured filters by object type, status, jurisdiction, and updated window;
- emit refresh jobs or outbox events whenever searched entities materially change.

## 2.3 Pricing evidence source requirements

The system shall:

- distinguish between **source evidence tables** and **canonical execution pricing tables**;
- support wage-source records and determination records;
- support apprenticeship ratio and obligation references;
- support equipment rate book ingestion with effective dates;
- support vendor source registry entries for materials and rental vendors;
- support price confidence and location scope for source-observed material prices;
- support curated transforms from evidence tables into `rate_book_entries` and `labor_rate_profiles`;
- preserve source provenance on any derived canonical price entry.

# 3 New stable-before-stable requirement group

The following requirements now move into the “mandatory before PRD considered stable” list:

1. canonical rule contract and evaluation audit model;
2. public-works wage seed path using DIR determinations;
3. apprenticeship ratio/obligation logic;
4. Caltrans equipment book ingestion path;
5. vendor source registry and material-source evidence model;
6. `search_documents` implementation and object-type search coverage.

# 4 Domain-model additions to incorporate into the master PRD

## 4.1 New pricing-source entities

Add the following entities to the master domain model:

- wage source
- wage determination
- wage rate component
- apprentice progression
- apprentice ratio rule
- training fund obligation
- equipment rate book
- equipment class
- equipment rate entry
- equipment delivery policy
- vendor source registry
- material catalog item
- material source price
- source import run
- source import error

## 4.2 Governing flow rule

The master PRD should add this rule explicitly:

> Raw or imported evidence tables never price the estimate builder directly. Evidence must be normalized, reviewed, and transformed into canonical execution pricing tables before it is used for calculation defaults.

# 5 Workflow deltas

## 5.1 Opportunity intake

Add the following operational fields or derived panels:

- labor mode recommendation / current mode
- public works wage source status
- apprenticeship obligation status
- jurisdiction pack coverage status
- pricing evidence freshness warnings

## 5.2 Estimate builder

Add the following provenance surfaces:

- rate source badge
- labor mode badge
- determination / rate-book reference link
- quote evidence state
- `quote_required` or `source_warning` state

## 5.3 Publish readiness

The readiness contract must now be able to block publish if:

- required rule evaluations are stale or absent,
- required public-works labor mode data is incomplete,
- required apprenticeship obligation notes or checklist states are incomplete,
- a fee/permit placeholder is required but lacks required input data,
- source evidence is below the minimum confidence threshold where policy requires confirmation.

# 6 Search design delta

The master PRD should add a short search architecture note:

- `search_documents` is the operational search read model.
- It is refreshed asynchronously by outbox-driven rebuilds or targeted update jobs.
- Result ranking combines FTS relevance and trigram similarity.
- Search is tenant-bound and permission-aware.

# 7 Pricing/compliance framework additions

The pricing/compliance framework section should now add:

## 7.1 Wage-source hierarchy

1. DIR public-works determinations (canonical for public works)
2. apprentice determinations and ratio rules
3. org labor profiles for private/T+M
4. union/CBA uploads as evidence
5. benchmark references as non-canonical support

## 7.2 Equipment-source hierarchy

1. Caltrans CSV book for public-works-aligned seed rates
2. local rental delivery policies as supplemental context
3. vendor/rental quotes where project-specific

## 7.3 Materials-source hierarchy

1. direct vendor public price observations with explicit location variance handling
2. organization cost books and historical price books
3. vendor quotes
4. benchmark and index references as trend/support only

## 7.4 Price confidence levels

Add a required confidence taxonomy:

- high
- medium
- low
- quote_required

This taxonomy must influence builder warnings, evaluation outputs, and publish readiness where configured.

# 8 Immediate implementation note

The master PRD should now recommend that the next implementation pass produce:

- rules compiler contract,
- seed pack v0 fixtures,
- DDL/DTO additions for wages/materials/equipment evidence,
- search read-model implementation,
- and refresh/backfill jobs.
