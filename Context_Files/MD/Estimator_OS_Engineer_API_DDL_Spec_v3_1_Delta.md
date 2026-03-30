---
title: "Estimator OS"
subtitle: "Engineer Spec v3.1 — Rules Contract + Seed Pack Delta"
date: "March 25, 2026"
---

# 0 Purpose

This is a small additive delta to the existing Engineer API + DDL Spec v3. It locks the rule engine contract, extends the schema for wages/materials/equipment seed packs, and adds the search/read-model implementation details required by current project decisions.

# 1 Additional migration sequence

## 1.1 New additive migrations

| ID | Migration | Purpose | Depends on |
|---|---|---|---|
| M017 | rules_engine_contract_tables | add canonical rule version / compile artifacts if not already explicit | prior rule-template migrations |
| M018 | wage_seed_pack_tables | add wage source, determination, component, progression, ratio, and training fund tables | pricing libraries foundation |
| M019 | equipment_seed_pack_tables | add equipment book, class, entry, and delivery policy tables | pricing libraries foundation |
| M020 | materials_source_tables | add vendor source registry, catalog item, source price, and import-run tables | pricing libraries foundation |
| M021 | search_documents_indexes | add FTS + trigram indexes and refresh support | search_documents baseline |

## 1.2 Migration rules

- All migrations are additive.
- No migration may mutate published estimate data.
- Seed imports must be idempotent.
- Evidence tables and canonical execution tables must remain distinct.

# 2 Rules engine implementation contract (exact)

## 2.1 Stored artifacts per rule template version

Every rule template version must persist:

- `canonical_json`
- `compiled_jsonlogic`
- `compile_hash`
- `schema_version`
- `compiler_version`
- `normalization_version`
- `source_yaml` (nullable, internal only)
- `source_manifest_json`

## 2.2 Stored artifacts per evaluation

Every evaluation must persist:

- `template_version_id`
- `compile_hash`
- `evaluation_hash`
- `input_snapshot`
- `output_snapshot`
- `warning_snapshot`
- `blocker_snapshot`
- `confirmed_by`
- `confirmed_at`
- `override_reason`
- `evaluated_at`

## 2.3 JSON Schema requirements

The canonical JSON schema must validate:

- `schemaVersion`
- `driverCode`
- `effectiveStart`
- `effectiveEnd`
- `sourceRefs[]`
- `requiredInputs[]`
- `applicableIf`
- `outputs`
- `warnings[]`
- `blockers[]`

## 2.4 Compiler guarantees

- stable canonicalization before hashing
- compile failure must never create partial active versions
- runtime must only evaluate compiled JSONLogic
- no runtime code generation outside compiler boundary

# 3 Exact DDL additions

## 3.1 Rules contract support tables

```sql
create table if not exists rule_compile_artifacts (
  id uuid primary key,
  organization_id uuid not null,
  rule_template_version_id uuid not null,
  canonical_json jsonb not null,
  compiled_jsonlogic jsonb not null,
  compile_hash text not null,
  schema_version text not null,
  compiler_version text not null,
  normalization_version text not null,
  source_yaml text null,
  source_manifest_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (organization_id, rule_template_version_id)
);
```

## 3.2 Wage source tables

```sql
create table if not exists wage_sources (
  id uuid primary key,
  organization_id uuid not null,
  source_type text not null check (source_type in ('dir_general','dir_apprentice','union_cba','org_tm','benchmark')),
  source_name text not null,
  source_url text not null,
  jurisdiction_scope jsonb not null default '{}'::jsonb,
  effective_start date not null,
  effective_end date null,
  retrieved_at timestamptz not null,
  hash text not null,
  created_at timestamptz not null default now()
);

create table if not exists wage_determinations (
  id uuid primary key,
  organization_id uuid not null,
  wage_source_id uuid not null references wage_sources(id),
  cycle text not null,
  county text not null,
  craft text not null,
  classification text not null,
  shift_code text null,
  rate_type text not null check (rate_type in ('journeyman','apprentice')),
  effective_start date not null,
  effective_end date null,
  raw_ref_code text null,
  created_at timestamptz not null default now()
);

create table if not exists wage_rate_components (
  id uuid primary key,
  organization_id uuid not null,
  wage_determination_id uuid not null references wage_determinations(id),
  component_code text not null,
  component_label text not null,
  hourly_amount numeric(12,4) not null,
  component_group text not null check (component_group in ('base','fringe','employer_cost','taxable_cash','other')),
  created_at timestamptz not null default now()
);

create table if not exists apprentice_progressions (
  id uuid primary key,
  organization_id uuid not null,
  wage_determination_id uuid not null references wage_determinations(id),
  progression_label text not null,
  progression_order int not null,
  percent_of_journeyman numeric(8,4) null,
  base_hourly numeric(12,4) null,
  fringe_hourly numeric(12,4) null,
  hours_required int null,
  created_at timestamptz not null default now()
);

create table if not exists apprentice_ratio_rules (
  id uuid primary key,
  organization_id uuid not null,
  wage_source_id uuid not null references wage_sources(id),
  craft text not null,
  public_works_threshold_amount numeric(14,2) not null default 30000.00,
  min_journeyman_hours_per_apprentice_hour numeric(10,4) not null default 5.0,
  max_ratio_note text null,
  exemption_note text null,
  created_at timestamptz not null default now()
);

create table if not exists training_fund_obligations (
  id uuid primary key,
  organization_id uuid not null,
  wage_source_id uuid not null references wage_sources(id),
  craft text not null,
  contribution_note text not null,
  das_140_required boolean not null default true,
  das_142_required boolean not null default true,
  created_at timestamptz not null default now()
);
```

## 3.3 Equipment seed tables

```sql
create table if not exists equipment_rate_books (
  id uuid primary key,
  organization_id uuid not null,
  source_name text not null,
  source_url text not null,
  effective_start date not null,
  effective_end date not null,
  retrieved_at timestamptz not null,
  source_hash text not null,
  created_at timestamptz not null default now()
);

create table if not exists equipment_classes (
  id uuid primary key,
  organization_id uuid not null,
  equipment_code text not null,
  equipment_name text not null,
  category text not null,
  unit_basis text not null,
  created_at timestamptz not null default now(),
  unique (organization_id, equipment_code)
);

create table if not exists equipment_rate_entries (
  id uuid primary key,
  organization_id uuid not null,
  equipment_rate_book_id uuid not null references equipment_rate_books(id),
  equipment_class_id uuid not null references equipment_classes(id),
  rate_code text not null,
  daily_rate numeric(14,4) null,
  weekly_rate numeric(14,4) null,
  monthly_rate numeric(14,4) null,
  labor_surcharge numeric(14,4) null,
  fuel_basis_note text null,
  meter_cap_note text null,
  created_at timestamptz not null default now()
);

create table if not exists equipment_delivery_policies (
  id uuid primary key,
  organization_id uuid not null,
  vendor_name text not null,
  location_scope text not null,
  small_delivery_each_way numeric(12,2) null,
  large_delivery_each_way numeric(12,2) null,
  policy_note text null,
  source_url text not null,
  retrieved_at timestamptz not null,
  created_at timestamptz not null default now()
);
```

## 3.4 Materials source tables

```sql
create table if not exists vendor_source_registry (
  id uuid primary key,
  organization_id uuid not null,
  vendor_code text not null,
  vendor_name text not null,
  branch_name text null,
  branch_city text null,
  location_scope text not null,
  source_type text not null check (source_type in ('public_price','public_catalog','quote_only','account_price','rental_policy')),
  base_url text not null,
  price_confidence text not null check (price_confidence in ('high','medium','low','quote_required')),
  last_verified_at timestamptz not null,
  created_at timestamptz not null default now()
);

create table if not exists material_catalog_items (
  id uuid primary key,
  organization_id uuid not null,
  item_code text not null,
  item_name text not null,
  unit text not null,
  category text not null,
  tags jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique (organization_id, item_code)
);

create table if not exists material_source_prices (
  id uuid primary key,
  organization_id uuid not null,
  vendor_source_registry_id uuid not null references vendor_source_registry(id),
  material_catalog_item_id uuid not null references material_catalog_items(id),
  observed_unit_price numeric(14,4) not null,
  price_type text not null check (price_type in ('list','promo','account','quote_only')),
  effective_start date null,
  effective_end date null,
  retrieved_at timestamptz not null,
  source_sku text null,
  source_note text null,
  created_at timestamptz not null default now()
);

create table if not exists source_import_runs (
  id uuid primary key,
  organization_id uuid not null,
  pack_type text not null,
  source_name text not null,
  source_url text not null,
  retrieved_at timestamptz not null,
  source_hash text not null,
  row_count int not null default 0,
  status text not null check (status in ('queued','running','succeeded','failed','partial')),
  summary_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  completed_at timestamptz null
);

create table if not exists source_import_errors (
  id uuid primary key,
  organization_id uuid not null,
  source_import_run_id uuid not null references source_import_runs(id),
  row_ref text null,
  field_name text null,
  error_code text not null,
  error_message text not null,
  raw_value text null,
  created_at timestamptz not null default now()
);
```

## 3.5 Search table hardening

```sql
create extension if not exists pg_trgm;

alter table search_documents
  add column if not exists search_key text,
  add column if not exists tsv tsvector generated always as (
    to_tsvector('english', coalesce(title,'') || ' ' || coalesce(subtitle,'') || ' ' || coalesce(body_text,''))
  ) stored;

create index if not exists idx_search_documents_tsv
  on search_documents using gin (tsv);

create index if not exists idx_search_documents_trgm
  on search_documents using gin (search_key gin_trgm_ops);
```

# 4 DTO additions

## 4.1 Wage source DTOs

### `WageSource`
```json
{
  "id": "uuid",
  "sourceType": "dir_general",
  "sourceName": "DIR 2025-2 Journeyman Determinations",
  "sourceUrl": "https://www.dir.ca.gov/OPRL/2025-2/PWD/index.htm",
  "jurisdictionScope": {"state": "CA", "region": "Northern California"},
  "effectiveStart": "2026-09-01",
  "effectiveEnd": null,
  "retrievedAt": "2026-03-25T00:00:00Z"
}
```

### `WageDetermination`
```json
{
  "id": "uuid",
  "wageSourceId": "uuid",
  "cycle": "2025-2",
  "county": "San Francisco",
  "craft": "Laborer",
  "classification": "Group 1",
  "shiftCode": null,
  "rateType": "journeyman"
}
```

### `ApprenticeRatioRule`
```json
{
  "id": "uuid",
  "craft": "Carpenter",
  "publicWorksThresholdAmount": 30000.0,
  "minJourneymanHoursPerApprenticeHour": 5.0,
  "maxRatioNote": "Per applicable program standards",
  "das140Required": true,
  "das142Required": true
}
```

## 4.2 Equipment DTOs

### `EquipmentRateBook`
```json
{
  "id": "uuid",
  "sourceName": "Caltrans Equipment Rental Rate Book",
  "effectiveStart": "2025-04-01",
  "effectiveEnd": "2026-03-31",
  "retrievedAt": "2026-03-25T00:00:00Z"
}
```

### `EquipmentRateEntry`
```json
{
  "id": "uuid",
  "equipmentClassId": "uuid",
  "rateCode": "CAT_D6_DOZER",
  "dailyRate": 1250.0,
  "weeklyRate": 5000.0,
  "monthlyRate": 15000.0,
  "laborSurcharge": 0.0,
  "fuelBasisNote": "$4.931/gal one-year average diesel basis"
}
```

## 4.3 Materials DTOs

### `VendorSourceRegistry`
```json
{
  "id": "uuid",
  "vendorCode": "white_cap",
  "vendorName": "White Cap",
  "branchName": "San Francisco Branch",
  "branchCity": "San Francisco",
  "locationScope": "branch_pricing",
  "sourceType": "public_price",
  "priceConfidence": "medium",
  "lastVerifiedAt": "2026-03-25T00:00:00Z"
}
```

### `MaterialSourcePrice`
```json
{
  "id": "uuid",
  "vendorSourceRegistryId": "uuid",
  "materialCatalogItemId": "uuid",
  "observedUnitPrice": 39.99,
  "priceType": "list",
  "effectiveStart": "2026-03-25",
  "effectiveEnd": null,
  "sourceSku": "104626001",
  "sourceNote": "Location variance warning applies"
}
```

# 5 API additions

## 5.1 Admin / ingest endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/v1/rules/import` | import YAML/JSON rule packs |
| GET | `/v1/rules/templates/{id}/compiled` | inspect canonical JSON + JSONLogic + compile hash |
| POST | `/v1/source-import-runs` | queue seed-pack import |
| GET | `/v1/source-import-runs/{id}` | read import status and errors |
| GET | `/v1/wage-sources` | list wage sources |
| GET | `/v1/wage-determinations` | filter by county/craft/cycle |
| GET | `/v1/apprentice-ratio-rules` | read obligation rules |
| GET | `/v1/equipment-rate-books` | list rate books |
| GET | `/v1/equipment-rate-entries` | filter by book/class |
| GET | `/v1/vendor-source-registry` | list vendor source rows |
| GET | `/v1/material-source-prices` | filter by vendor/item/confidence |
|

## 5.2 Transformation endpoints (internal/admin)

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/v1/price-evidence/transforms/wages` | project selected wage evidence into labor profiles |
| POST | `/v1/price-evidence/transforms/equipment` | project selected equipment evidence into rate book entries |
| POST | `/v1/price-evidence/transforms/materials` | project selected material evidence into rate book entries |

# 6 Background jobs

Required new jobs:

- `rule_compile_job`
- `seed_pack_import_job`
- `dir_wage_normalize_job`
- `caltrans_equipment_normalize_job`
- `vendor_source_normalize_job`
- `price_evidence_transform_job`
- `search_documents_refresh_job`

# 7 Acceptance additions

1. Importing the same DIR or Caltrans pack twice must be idempotent.
2. A rule template version must compile identically from identical canonical JSON.
3. Evaluation hash must change when and only when template version, compile hash, or input/output snapshot changes.
4. Public-works opportunities with apprenticeable crafts and threshold amount must surface ratio and DAS obligations.
5. Material source prices with `quote_required` must not auto-populate pricing defaults without explicit confirmation or transform policy.
6. Search must rank tenant-scoped results using both FTS and trigram similarity.

# 8 Immediate integration rule

The engineer spec should now treat these source-evidence tables as the feeder system for:

- `labor_rate_profiles`
- `rate_books`
- `rate_book_entries`
- `compliance_driver_templates`
- `compliance_evaluations`

No direct estimate-builder reads from raw evidence tables are allowed.
