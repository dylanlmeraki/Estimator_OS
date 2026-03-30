# Build scope for real-source mirror integration

## Goal
Use real public/official source mirrors as fixture inputs for:
- wage source seeding
- apprenticeship obligation rules
- equipment rate books
- fee schedule placeholders
- permit-path checklists
- materials price observations

## Proposed new tables
- indexed_source_document
- source_mirror_asset
- source_parse_run
- source_parse_error
- fee_schedule_source
- fee_schedule_entry

## Proposed pipeline
1. mirror source metadata
2. download mirror assets when direct file URLs exist
3. parse into normalized source-evidence rows
4. promote reviewed rows into canonical pricing/rule tables
5. link proposal/estimate outputs back to source provenance