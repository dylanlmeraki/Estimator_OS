# Estimator OS: Complete Development & Deployment Roadmap

**Generated:** 2026-03-29  
**Current Stage:** Data Validation + Rule Engine Core + Azure Deployment Prep

---

## 🎯 Phase 1: Local Development (NOW) — Data Validation Layer

### Selected Tools (Tier 1)
- ✅ **Database Tools** — Schema inspection, SQL validation
- ✅ **JSON Validator** — Manifest/DTO schema enforcement
- ✅ **CSV Parser** — Source registry ingestion

### Secondary Recommendations (Tier 2a)
Choose **one** to layer in:
- **Great Expectations** — Data quality profiling (detect missing fields, type mismatches in CSV imports)
- **dbt** — Seed pack model transformations with built-in tests
- **Pandera** — Lightweight schema assertions for DataFrames

### Success Criteria
- [ ] All source CSVs pass validation (5 registries + 2 catalogs)
- [ ] All JSON manifests conform to schema
- [ ] SQL seed pack models import without errors
- [ ] YAML rules parse correctly into canonical JSON

**Tools to activate:** See [Tier 1 Activation](#tier-1-activation) below

---

## 🔧 Phase 2: Rule Engine Observability (Week 2) — Tracing & Debugging

### Selected Tools (Tier 2b)
Choose **one** primary:
- **OpenTelemetry + Jaeger** — Self-hosted, lightweight (recommended for local dev)
- **Azure App Insights** — If deploying to Azure (pairs with Phase 4 deployment)

### Deliverable
- Rule execution traces show which rules fire for a given input
- Performance metrics (latency per rule, rule composition depth)
- Debug panel in UI showing rule evaluation path

### Skill to Create Next
**"rule-engine-tracing-setup"** — Template for instrumenting rule evaluation with spans/events

---

## 🏗️ Phase 3: Backend API & Data Exposure (Week 3) — API Generation

### Selected Tools (Tier 2c)
- **FastAPI** — Wrap rule engine in HTTP endpoints
- **PostgREST** — Auto-expose seed pack schema as REST API

### API Endpoints Generated
```
POST /api/evaluate-rule       → Execute rule with input
GET  /api/rules               → List all rules (with metadata)
GET  /api/rate-books          → Query rate_books table
POST /api/import-source       → Ingest source registry CSV
```

### Skill to Create Next
**"api-documentation-generation"** — Auto-generate OpenAPI docs from rule definitions

---

## ☁️ Phase 4: Infrastructure & Deployment (Week 4+) — Azure Setup

### Selected Tools (Tier 3)
- **Azure IaC Generator (Bicep/Terraform)** → Generate infrastructure code
- **Azure Database (PostgreSQL)** → Managed seed pack database
- **Azure Functions** → Serverless rule evaluation endpoints (optional)
- **Azure App Service** → Host FastAPI backend
- **Azure Storage** → Versioned seed pack storage, audit logs

### Architecture Decision Tree
```
┌─ Do you want serverless (pay-per-call)?
│  ├─ YES → Azure Functions + Cosmos DB
│  └─ NO  → App Service + PostgreSQL (simpler, cheaper for baseline load)
│
└─ Do you need multi-region failover?
   ├─ YES → Traffic Manager + replicated DB
   └─ NO  → Single region (simpler for MVP)
```

### Bicep/Terraform Templates to Generate
- PostgreSQL server + seed pack database + firewall rules
- App Service Plan + Function App (FastAPI runtime)
- Application Insights + monitoring dashboards
- Key Vault (for API keys, connection strings)

### Deployment Checklist
- [ ] Run `terraform plan` to preview Azure resources
- [ ] Run `terraform apply` to provision
- [ ] Deploy FastAPI container to App Service
- [ ] Load-test rule evaluation under Azure
- [ ] Set up CI/CD pipeline (GitHub Actions → Azure)

### Skill to Create Next
**"azure-deployment-validation"** — Pre-flight checks before `terraform apply`

---

## 🧰 Phase 5: Observability & Operations (Ongoing) — Monitoring

### Tools to Layer In
- **Azure Monitor** — CPU, memory, request latency dashboards
- **Azure Log Analytics** → Query rule engine logs via KQL
- **Datadog** (optional) → Advanced APM if needed later

### Success Metrics
- Rule evaluation latency: < 100ms (p50), < 500ms (p99)
- CSV import throughput: > 1000 rows/sec
- DB query performance tracked

---

## 📊 Tool Selection Matrix

| Phase | Tool | Free Tier | Install Extension? | Notes |
|-------|------|-----------|-------------------|-------|
| 1 | Database Tools | ✅ | (built-in MCP) | mcp_activate_mssql_database_management_tools |
| 1 | JSON Validator | ✅ | `pip install jsonschema` | Python library |
| 1 | CSV Parser | ✅ | `pip install pandas pyyaml` | Python library |
| 2a | Great Expectations | ✅ | `pip install great-expectations` | Data profiling |
| 2b | OpenTelemetry | ✅ | `pip install opentelemetry-api` | Tracing SDK |
| 2b | Jaeger | ✅ | Docker: `docker run jaegertracing/all-in-one` | Self-hosted backend |
| 2c | FastAPI | ✅ | `pip install fastapi uvicorn` | API framework |
| 2c | PostgREST | ✅ | Docker: `docker run postgrest/postgrest` | REST wrapper |
| 3 | Azure IaC Generator | ✅ | (MCP server) | `mcp_azure_mcp_deploy` |
| 3 | Bicep CLI | ✅ | `az bicep install` | Already in Azure CLI |
| 4 | Terraform | ✅ | CLI: `terraform init` | IaC tool |
| 5 | Azure Monitor | ✅ | (Portal only) | Cloud observability |

---

## 🔄 Progression Logic: Auto-Suggest Next Layer

After Phase 1 tools are activated:
- **Q1:** "Need to test data quality?" → Suggest Phase 2a
- **Q2:** "Want to debug rule execution?" → Suggest Phase 2b
- **Q3:** "Ready to expose data as APIs?" → Suggest Phase 2c
- **Q4:** "Ready to deploy?" → Suggest Phase 4 (Bicep/Terraform)
- **Q5:** "Need production monitoring?" → Suggest Phase 5

---

## 🛑 Workspace Saturation Checkpoint

**When to split into multiple workspaces/containers:**

After Phase 3 completion (local API running), consider:
- **Dev Environment** (current): Rule engine + API layer + tests
- **Data Factory** (new container): ETL pipelines for source ingestion
- **Infrastructure** (IaC folder): Bicep/Terraform isolated from code

**Trigger:** If you have >50 files in root, consider splitting.

---

## 📝 Next Skills to Create

Based on this roadmap:
1. **rule-engine-tracing-setup** (Phase 2b)
2. **api-documentation-generation** (Phase 2c)
3. **azure-deployment-validation** (Phase 4)
4. **data-quality-testing-framework** (Phase 2a optional)

---

## 🚀 Quick Start: Activate Phase 1 NOW

See section below: [Tier 1 Activation](#tier-1-activation)
