-- Estimator.OS source-mirror build layer
-- Purpose:
-- 1) Mirror/index authoritative sources before parsing/promotion.
-- 2) Preserve provenance links from canonical rows back to source_code/source documents.
-- 3) Keep parsing/promotion deterministic and auditable.

create extension if not exists pgcrypto;
create extension if not exists pg_trgm;

create table if not exists indexed_source_document (
    id uuid primary key default gen_random_uuid(),
    source_code text not null unique,
    title text not null,
    source_url text not null,
    source_type text not null check (
        source_type in ('html_page','pdf','csv','json','doc','manual_note','catalog_page','search_result_snapshot')
    ),
    authority_type text not null check (
        authority_type in ('federal','state','regional','county','city_county','vendor','internal','industry_reference')
    ),
    jurisdiction_scope jsonb not null default '[]'::jsonb,
    effective_hint text null,
    retrieved_at timestamptz not null,
    status text not null check (
        status in ('indexed','queued_for_download','mirrored','queued_for_parse','parsed','promoted','superseded','error')
    ),
    indexed_extract jsonb not null default '{}'::jsonb,
    normalization_targets jsonb not null default '[]'::jsonb,
    seed_priority text not null check (seed_priority in ('canonical','high','medium','low')),
    notes text null,
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_indexed_source_document_status
    on indexed_source_document (status, seed_priority, retrieved_at desc);

create index if not exists idx_indexed_source_document_jurisdiction
    on indexed_source_document using gin (jurisdiction_scope);

create table if not exists source_mirror_asset (
    id uuid primary key default gen_random_uuid(),
    indexed_source_document_id uuid not null references indexed_source_document(id) on delete cascade,
    asset_kind text not null check (
        asset_kind in ('raw_pdf','raw_csv','raw_html','raw_json','markdown_extract','table_extract','ocr_extract')
    ),
    asset_storage_key text not null,
    asset_mime_type text not null,
    checksum_sha256 text not null,
    byte_size bigint null,
    mirrored_at timestamptz not null,
    parser_status text not null check (parser_status in ('not_started','parsed','partial','failed')) default 'not_started',
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_source_mirror_asset_source
    on source_mirror_asset (indexed_source_document_id, mirrored_at desc);

create table if not exists source_parse_run (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    indexed_source_document_id uuid not null references indexed_source_document(id) on delete cascade,
    source_code text not null,
    parser_code text not null,
    parser_version text not null,
    parse_family text not null check (parse_family in ('fee_schedule_pdf','regulatory_pdf','equipment_csv','generic')),
    status text not null check (status in ('queued','running','succeeded','partial','failed')),
    started_at timestamptz not null default now(),
    completed_at timestamptz null,
    input_asset_ids jsonb not null default '[]'::jsonb,
    parsed_row_counts jsonb not null default '{}'::jsonb,
    promoted_row_counts jsonb not null default '{}'::jsonb,
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_source_parse_run_lookup
    on source_parse_run (source_code, status, started_at desc);

create table if not exists source_parse_error (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    source_parse_run_id uuid not null references source_parse_run(id) on delete cascade,
    source_code text not null,
    row_ref text null,
    field_name text null,
    error_code text not null,
    error_message text not null,
    raw_value text null,
    payload_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_source_parse_error_run
    on source_parse_error (source_parse_run_id, created_at desc);

create table if not exists fee_schedule_source (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    source_code text not null unique,
    indexed_source_document_id uuid not null references indexed_source_document(id),
    jurisdiction_code text not null,
    authority_type text not null,
    title text not null,
    source_url text not null,
    effective_start date null,
    effective_end date null,
    retrieved_at timestamptz not null,
    source_cycle text null,
    parse_run_id uuid null references source_parse_run(id),
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists fee_schedule_entry (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null,
    fee_schedule_source_id uuid not null references fee_schedule_source(id) on delete cascade,
    source_code text not null,
    indexed_source_document_id uuid not null references indexed_source_document(id),
    parse_run_id uuid null references source_parse_run(id),
    jurisdiction_code text not null,
    fee_family text not null,
    fee_code text not null,
    fee_label text not null,
    fee_basis_type text not null check (fee_basis_type in ('flat','per_unit','formula','review','consultation','other')),
    fee_amount numeric(14,4) null,
    currency_code text not null default 'USD',
    uom text null,
    formula_notes text null,
    qualifier_notes text null,
    effective_start date null,
    effective_end date null,
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (source_code, fee_code, coalesce(uom,''))
);

create index if not exists idx_fee_schedule_entry_lookup
    on fee_schedule_entry (jurisdiction_code, fee_family, fee_code, effective_start);

alter table if exists wage_source
    add column if not exists indexed_source_document_id uuid null references indexed_source_document(id);

alter table if exists apprentice_ratio_rule
    add column if not exists indexed_source_document_id uuid null references indexed_source_document(id);

alter table if exists equipment_rate_book
    add column if not exists indexed_source_document_id uuid null references indexed_source_document(id);

alter table if exists vendor_source_registry
    add column if not exists source_code text null;

alter table if exists vendor_source_registry
    add column if not exists indexed_source_document_id uuid null references indexed_source_document(id);

alter table if exists material_price_observation
    add column if not exists source_code text null;

alter table if exists material_price_observation
    add column if not exists indexed_source_document_id uuid null references indexed_source_document(id);

alter table if exists rule_compile_artifact
    add column if not exists source_codes jsonb not null default '[]'::jsonb;

alter table if exists rule_evaluation_snapshot
    add column if not exists source_codes jsonb not null default '[]'::jsonb;

alter table if exists jurisdiction_rule_template
    add column if not exists source_code text null;

alter table if exists jurisdiction_rule_template
    add column if not exists source_url text null;

alter table if exists jurisdiction_rule_template
    add column if not exists source_effective_hint text null;

alter table if exists jurisdiction_rule_template
    add column if not exists source_authority_type text null;

