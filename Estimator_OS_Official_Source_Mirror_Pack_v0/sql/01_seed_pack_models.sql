-- Estimator.OS seed-pack models v0
-- Purpose: source-evidence ingestion for wages, apprenticeship, equipment books, and materials.
-- These tables feed existing canonical execution tables (rate_books, rate_book_entries, labor_rate_profiles, quotes)
-- through explicit operator-reviewed normalization jobs. They are NOT a parallel pricing engine.

create extension if not exists pgcrypto;

create table if not exists seed_import_run (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    import_family text not null, -- dir, caltrans, materials
    manifest_code text not null,
    source_id text null,
    started_at timestamptz not null default now(),
    completed_at timestamptz null,
    status text not null check (status in ('queued','running','completed','failed','partial')),
    row_count integer not null default 0,
    error_count integer not null default 0,
    notes text null,
    metadata_json jsonb not null default '{}'::jsonb
);

create table if not exists seed_import_error (
    id uuid primary key default gen_random_uuid(),
    seed_import_run_id uuid not null references seed_import_run(id) on delete cascade,
    row_identifier text null,
    error_code text not null,
    error_message text not null,
    payload_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists wage_source (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    source_code text not null unique,
    source_type text not null check (source_type in ('dir_general','dir_apprentice','union_cba','org_tm','benchmark','manual')),
    title text not null,
    source_url text not null,
    cycle text null,
    county_scope text[] not null default '{}',
    craft_scope text[] not null default '{}',
    effective_start date not null,
    effective_end date null,
    retrieved_at timestamptz not null,
    canonical_for_public_works boolean not null default false,
    raw_metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists wage_determination (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    wage_source_id uuid not null references wage_source(id) on delete cascade,
    county_code text not null,
    county_name text not null,
    craft_code text not null,
    craft_name text not null,
    classification_code text not null,
    classification_name text not null,
    shift_code text not null default 'standard',
    rate_type text not null check (rate_type in ('journeyman','apprentice','foreman','other')),
    apprentice_period text null,
    base_hourly numeric(18,4) null,
    fringe_total_hourly numeric(18,4) null,
    total_package_hourly numeric(18,4) generated always as (coalesce(base_hourly,0) + coalesce(fringe_total_hourly,0)) stored,
    overtime_rule_ref text null,
    training_contribution_hourly numeric(18,4) null,
    effective_start date not null,
    effective_end date null,
    raw_line_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (wage_source_id, county_code, craft_code, classification_code, shift_code, rate_type, coalesce(apprentice_period,''))
);

create index if not exists idx_wage_determination_lookup
    on wage_determination (county_code, craft_code, classification_code, rate_type, effective_start);

create table if not exists apprentice_ratio_rule (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    source_code text not null,
    state_code text not null default 'CA',
    craft_code text null,
    applicability_scope text not null default 'public_works',
    contract_amount_threshold numeric(18,2) not null default 30000.00,
    ratio_basis text not null default 'straight_time_journeyman_hours',
    minimum_journeyman_hours integer not null default 5,
    apprentice_hours_required integer not null default 1,
    requires_das_140 boolean not null default true,
    requires_das_142 boolean not null default true,
    requires_training_fund boolean not null default true,
    source_url text not null,
    effective_start date not null,
    effective_end date null,
    notes text null,
    raw_metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists equipment_rate_book (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    source_code text not null unique,
    provider_code text not null check (provider_code in ('caltrans','local_rental_yard','internal','manual')),
    title text not null,
    source_url text not null,
    effective_start date not null,
    effective_end date null,
    public_works_canonical boolean not null default false,
    source_asset_type text not null default 'csv',
    notes text null,
    raw_metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists equipment_rate_entry (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    equipment_rate_book_id uuid not null references equipment_rate_book(id) on delete cascade,
    equipment_code text not null,
    equipment_name text not null,
    category text null,
    ownership_basis text not null default 'ownership_cost',
    rate_hourly numeric(18,4) null,
    rate_daily numeric(18,4) null,
    rate_weekly numeric(18,4) null,
    rate_monthly numeric(18,4) null,
    labor_surcharge_pct numeric(10,4) null,
    fuel_basis text null,
    raw_line_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (equipment_rate_book_id, equipment_code)
);

create index if not exists idx_equipment_rate_entry_lookup
    on equipment_rate_entry (equipment_code, equipment_name);

create table if not exists vendor_source_registry (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    vendor_source_code text not null unique,
    vendor_name text not null,
    source_type text not null check (source_type in ('vendor_catalog','vendor_quote','internal_catalog','manual')),
    source_url text null,
    location_scope text not null default 'regional',
    price_variance_policy text not null default 'location_scoped',
    default_confidence text not null check (default_confidence in ('quote','public_list_price','branch_specific','manual','benchmark')),
    notes text null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists material_catalog_item (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    catalog_item_code text not null unique,
    category_code text not null,
    subcategory_code text not null,
    description text not null,
    typical_uom text not null,
    source_strategy text not null default 'curated_plus_observation',
    preferred_vendor_source_id uuid null references vendor_source_registry(id),
    bay_area_priority boolean not null default true,
    location_scope text not null default 'regional',
    default_price_confidence text not null check (default_price_confidence in ('structure_only','public_list_price','quote_required','branch_specific')),
    notes text null,
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_material_catalog_lookup
    on material_catalog_item (category_code, subcategory_code, description);

create table if not exists material_price_observation (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    material_catalog_item_id uuid not null references material_catalog_item(id) on delete cascade,
    vendor_source_registry_id uuid not null references vendor_source_registry(id),
    branch_name text null,
    branch_city text null,
    branch_region text null,
    location_scope text not null default 'branch/location',
    public_price numeric(18,4) null,
    currency_code text not null default 'USD',
    uom text not null,
    price_confidence text not null check (price_confidence in ('public_list_price','branch_specific','quote','manual','benchmark')),
    source_url text null,
    observed_at timestamptz not null,
    effective_start date null,
    effective_end date null,
    raw_payload_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_material_price_observation_lookup
    on material_price_observation (material_catalog_item_id, vendor_source_registry_id, observed_at desc);

-- Suggested normalization targets:
-- 1) Convert selected wage_determination rows into labor_rate_profiles / labor profile entries by county-craft basis.
-- 2) Convert equipment_rate_entry rows into rate_book_entries for public works equipment books.
-- 3) Convert approved material_price_observation rows into rate_book_entries, preserving vendor/location evidence in metadata_json.
