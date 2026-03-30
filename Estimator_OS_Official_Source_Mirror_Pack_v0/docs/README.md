# Estimator.OS official source mirror pack v0

This pack was generated from live official/public sources to support the next fixture and ingestion pass.

## What it contains
- indexed source registry
- normalized per-source mirror JSON
- schema for indexed source documents
- source mirror manifest

## Recommended immediate next pass
1. Download and mirror the queued PDF/CSV sources:
   - sf_public_works_fee_schedule_pdf
   - baaqmd_reg11_rule2
   - caltrans equipment CSV
2. Build parsers that convert:
   - DIR determination pages into wage source + craft/county records
   - SF fee schedules into fee_schedule_entry rows
   - vendor catalog snapshots into material_price_observation rows
3. Add `indexed_source_document` and `source_mirror_asset` tables to the seed-pack schema.
4. Link `jurisdiction_rule_template` rows back to `source_code` and `source_url`.
5. Add provenance UI hooks so generated proposal notes and blockers cite their mirror source.

## Notes
- DIR is the canonical public-works wage root.
- Caltrans is the canonical public-works equipment seed root.
- SF DBI and SF Public Works are canonical San Francisco fee/permit-path roots.
- Water Boards and BAAQMD are trigger-rule roots, not broad rate-book roots.
- White Cap is vendor evidence only; prices remain location-scoped and confidence-rated.