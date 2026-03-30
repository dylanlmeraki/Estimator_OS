---
name: Estimator OS Development Agent
description: "Activates Tier 1 tools for Estimator OS: Database validation, JSON schema enforcement, CSV data parsing. Provides context for rule engine, fixture pack, and seed data workflows."
---

# Activator: Tier 1 Tools & Workspace Context

## Active MCP Servers & Tools

This workspace has activated:

1. **Database Tools** (MSSQL/PostgreSQL)
   - Query seed pack schemas in `01_seed_pack_models.sql`
   - Inspect rate_books, rate_book_entries, labor_rate_profiles
   - Use: `activate_mssql_database_management_tools`

2. **JSON Schema Validator**
   - Validate DTOs against `canonical_rule.schema.json`
   - Validate manifests against `rule_evaluation.schema.json`
   - Use: `pip install jsonschema`
   - Command: `python -m jsonschema --help`

3. **CSV Data Parser**
   - Parse source registries: `caltrans_source_registry.csv`, `dir_source_registry.csv`, `materials_catalog_v0.csv`
   - Validate headers, types, completeness
   - Use: `pip install pandas pyyaml`
   - Command: `python -c "import pandas as pd; df = pd.read_csv('file.csv'); print(df.info())"`

## Recommended Next Skills (After Phase 1)

- `rule-engine-tracing-setup` — Add observability to rule evaluation
- `data-quality-testing` — Profile CSV imports with Great Expectations
- `api-documentation-generation` — Auto-doc for FastAPI endpoints

## Phase 1 Success Checklist

- [ ] All 5 source registries load without errors
- [ ] All manifests pass JSON schema validation
- [ ] SQL seed pack models initialize
- [ ] YAML rules parse into canonical JSON

See [DEPLOYMENT_ROADMAP.md](./.DEPLOYMENT_ROADMAP.md) for full 5-phase plan.
