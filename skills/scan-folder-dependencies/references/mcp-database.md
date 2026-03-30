# MCP Servers & Tools Database

Comprehensive reference of free-tier MCP servers, skills, tools, and VS Code extensions with meaningful impact on codebases.

## Detection Patterns → Suggested MCP/Tools

### Python Ecosystem

**Pattern Match:** `*.py`, `requirements.txt`, `pyproject.toml`, `setup.py`, `poetry.lock`, `Pipfile`

| MCP/Tool | Free Tier | Use Case |
|----------|-----------|----------|
| Pylance Development Tools | ✅ (integrated) | Code analysis, syntax checking, environment management, refactoring |
| Python Environment Manager | ✅ (built-in) | Virtual env config, package management, interpreter selection |
| Kusto (Azure Data Explorer) | ✅ (free with logging) | Log analysis, telemetry queries, time-series data |
| Database Schema Inspection | ✅ (varies by DB) | PostgreSQL, MySQL, MSSQL schema browsing |

### Node.js / TypeScript Ecosystem

**Pattern Match:** `package.json`, `tsconfig.json`, `*.ts`, `*.tsx`, `.eslintrc`, `yarn.lock`

| MCP/Tool | Free Tier | Use Case |
|----------|-----------|----------|
| TypeScript Language Server | ✅ (integrated) | Type checking, quick fixes, refactoring |
| npm / yarn / pnpm tools | ✅ (CLI) | Dependency audit, tree analysis, version management |
| Vite / Next.js build tools | ✅ (CLI) | Build optimization, dev server, static export |
| ESLint / Prettier | ✅ (CLI + extensions) | Linting, formatting, code quality gates |

### Infrastructure-as-Code (Terraform, Bicep, CloudFormation)

**Pattern Match:** `*.tf`, `*.bicep`, `*.json` (ARM), `*.yaml` (CloudFormation), `terraform.tfstate`

| MCP/Tool | Free Tier | Use Case |
|----------|-----------|----------|
| Azure IaC Generator (Bicep/Terraform) | ✅ (Subagent) | Generate infrastructure code, best practices |
| Terraform validator | ✅ (CLI `terraform fmt/validate`) | Syntax checking, formatting |
| Azure Resource Lookup | ✅ (Azure CLI, free tier) | Query existing resources, inventory |
| Azure Compliance Audits | ✅ (azqr open-source) | Security posture, best practice checks |
| Cloud Architect (Azure) | ✅ (MCP) | Design recommendations, topology planning |

### Container & Orchestration

**Pattern Match:** `Dockerfile`, `docker-compose.yml`, `k8s/`, `*.yaml` (K8s), `helm/`

| MCP/Tool | Free Tier | Use Case |
|----------|-----------|----------|
| Container Tools Config | ✅ (built-in) | Docker/podman command generation |
| Azure Container Registry (ACR) | ✅ (free tier limited) | Image push/pull, registry operations |
| Azure Kubernetes Service (AKS) | ✅ (pay-per-use, free tier for learning) | Cluster provisioning, operations |
| Docker Compose Orchestration | ✅ (CLI) | Multi-container orchestration, dev environments |

### Database & SQL

**Pattern Match:** `*.sql`, `migrations/`, `schema.sql`, `*.prisma`, `psql`, `mysql`, `sqlalchemy`

| MCP/Tool | Free Tier | Use Case |
|----------|-----------|----------|
| MSSQL Database Tools | ✅ (MCP) | Connect, query, schema management for SQL Server |
| PostgreSQL Tools | ✅ (psql CLI, pgAdmin) | Query execution, schema inspection |
| Database Schema Migration | ✅ (Neon MCP) | Diff schemas, generate migrations, apply safely |
| Cosmos DB Best Practices | ✅ (Skill) | NoSQL optimization, partitioning guidance |

### Azure Services

**Pattern Match:** `azure.yaml`, `.azure/`, `*.bicep`, ARM templates, App Service config, Function app config

| MCP/Tool | Free Tier | Use Case |
|----------|-----------|----------|
| Azure Developer CLI (azd) | ✅ (CLI) | Project init, provisioning, deployment orchestration |
| Azure CLI | ✅ (CLI) | Resource management, queries, operations |
| Azure Diagnostics (AppLens) | ✅ (MCP) | Troubleshoot production issues, root cause analysis |
| Azure Compliance & Security | ✅ (azqr, Skill) | Audit posture, Key Vault expiration, orphaned resources |
| Azure Cost Optimization | ✅ (Subagent) | Identify savings, analyze spending, rightsize resources |
| Azure RBAC Helper | ✅ (Skill) | Find least-privilege role, generate YAML/CLI |
| Azure Quotas & Limits | ✅ (Skill) | Check capacity, validate provisioning feasibility |
| Azure Storage Tools | ✅ (Skill) | Blob, file share, queue, table, data lake operations |

### AI/ML & Agents

**Pattern Match:** `agents/`, `*.agent.md`, `chat.ts`, `anthropic`, `openai`, `LLM`, `model`, `agent`, `MCP`

| MCP/Tool | Free Tier | Use Case |
|----------|-----------|----------|
| Agent Customization | ✅ (Skill) | Create/debug skills, instructions, agents, custom modes |
| Microsoft Foundry (AI Agents) | ✅ (free tier + paid) | Deploy, evaluate, optimize AI agents and workflows |
| AI Application Best Practices | ✅ (Skill) | Agent runners, code gen, model selection, tracing |
| Copilot SDK (GitHub Copilot) | ✅ (limited free) | Build copilot-powered apps with @github/copilot-sdk |

### Documentation & Design

**Pattern Match:** `*.md`, `docs/`, `*.spec.md`, `SKILL.md`, `.figma.json`

| MCP/Tool | Free Tier | Use Case |
|----------|-----------|----------|
| Figma Code Integration | ✅ (Figma free tier) | Map designs to code, sync components, Code Connect |
| Figma Design Capture | ✅ (Figma free tier) | Import web pages, capture HTML to design, FigJam scripts |
| Microsoft Documentation Search | ✅ (Web search) | Find official docs, code samples, best practices |
| Markdown Linting | ✅ (CLI extensions) | Format, link validation, structure checks |

### Testing & Quality

**Pattern Match:** `test/`, `spec/`, `*.test.ts`, `jest.config.js`, `.mocha`, pytest, `coverage/`

| MCP/Tool | Free Tier | Use Case |
|----------|-----------|----------|
| Testing Frameworks | ✅ (Jest, pytest, etc.) | Unit/integration test execution, coverage reports |
| Load Testing (Azure) | ✅ (free tier limited) | Performance benchmarks, locust/JMeter script generation |

### Git & Source Control

**Pattern Match:** `.git/`, `.github/`, `.gitignore`, `pull_request_template.md`

| MCP/Tool | Free Tier | Use Case |
|----------|-----------|----------|
| GitHub PR Management | ✅ (GitHub free) | Create, merge, review PRs programmatically |
| GitHub Search & Discovery | ✅ (GitHub free) | Find code, repos, contributors across GitHub |
| Branch Management (Git) | ✅ (Git CLI) | Create, switch, diff, worktree management |
| Gitlens Integration | ✅ (Gitlens free) | Blame, history, PR prioritization, commitizen |

### Enterprise & Compliance

**Pattern Match:** `HIPAA`, `SOC2`, `GDPR`, `.compliance/`, audit logs, encryption

| MCP/Tool | Free Tier | Use Case |
|----------|-----------|----------|
| Azure Compliance Audits (azqr) | ✅ (Open-source) | Scan compliance gaps, resource review, policy validation |
| Advanced Security Alerts (Azure DevOps) | ✅ (ADO free tier limited) | Vulnerability scanning, secret detection |

---

## Suggested Pairing Rules

When a user selects one MCP/Tool, auto-suggest related ones:

| If Selected | Then Suggest |
|-------------|-------------|
| Azure IaC Generator | → Azure validate, Azure deploy, Cloud Architect |
| Azure deploy | → Azure diagnostics, Azure cost optimization, Azure compliance |
| Terraform | → Azure IaC Generator, Terraform validator, Cloud Architect |
| Kubernetes (AKS) | → Azure container registry, Container tools, Helm/kubectl |
| Python + pytest | → Pylance tools, code analysis, Azure deploy (if cloud-bound) |
| Node.js + TypeScript | → ESLint, Prettier, npm audit, build tools (Vite/Next) |
| Database (PostgreSQL/MSSQL) | → Schema migration tools, Kusto logging, Azure diagnostics |
| AI Agents | → Agent customization, Foundry, Agent Framework code gen, tracing |
| Figma design files | → Code Connect (map to code), Design capture (import web) |

---

## Free Tier Notes

⚠️ **Important**:
- Some tools have **free tier quotas** (e.g., Azure functions: 1M invocations/month free)
- Others are **fully free & open-source** (e.g., Terraform, Git CLI, pytest, ESLint)
- Some require **Azure subscription** but offer **free tier** for learning/testing (e.g., AKS, Container Registry)
- **MCP servers** listed here assume open-source or officially free integrations

Verify current free tier status at official tool websites before heavy usage.

---

## How to Use This Database

1. **Detection script** runs and identifies file patterns from the folder
2. **Script cross-references** this database table by language/framework
3. **Top 5–10** suggestions are presented to the user (filtered by confidence score)
4. **User selects** which ones are relevant
5. **Pairing rules** auto-suggest complementary tools
6. **Output** includes quick-start commands and related skills
