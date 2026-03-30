---
name: scan-folder-dependencies
description: "Scan a folder to detect all dependencies, file types, and frameworks, then suggest relevant MCP servers, skills, tools, and scripts with free tiers. Use when: opening a new folder, exploring a codebase, setting up workspace environment, modernizing a project, discovering available integrations."
argument-hint: "Folder path (optional; uses current workspace if omitted)"
---

# Scan Folder for Dependencies

Automatically detect technologies, frameworks, and patterns in a folder tree, then surface the most impactful free-tier MCP servers, skills, tools, and other resources that would enhance your workflow when used properly.

## When to Use

- **New folder opened**: Explore what MCP servers and tools would help
- **Project discovery**: Quickly understand a codebase's tech stack
- **Workspace setup**: Identify which Agent extensions and customizations apply
- **Modernization**: Find tools that could improve existing workflows
- **Research**: Detect patterns and suggest relevant skills/tools

## Procedure

### 1. Scan the Folder
<!-- Triggers the detection script to analyze:
   - File types and extensions
   - Framework patterns (via package.json, requirements.txt, pom.xml, go.mod, Dockerfile, etc.)
   - Language detection from source code
   - Folder structure depth and naming (e.g., `src/`, `tests/`, `infra/`, `sql/`)
   - Configuration files (terraform, bicep, docker-compose, etc.)
-->

Invoke this skill via `/scan-folder-dependencies` and provide:
- **Folder path** (optional): Absolute or workspace-relative path; defaults to the root of current workspace
- **Scope** (optional): `quick` (30 sec), `medium` (2-3 min), or `thorough` (5-10 min, includes nested folders)

Example: `/scan-folder-dependencies src/backend medium`

### 2. Review Detection Results

The skill will output:
- **Detected Technologies**: Languages, frameworks, tools actually found in the folder
- **Folder Stats**: File count, structure depth, key patterns identified
- **Inferred Use Cases**: What this codebase likely does (e.g., API, UI, data pipeline, infra-as-code)

### 3. Select MCP Servers & Tools

From the [master references](./references/mcp-database.md), the skill will suggest the **top 5–10 most impactful free-tier** MCP servers/tools based on detected tech:

| Detected | Suggested MCP/Tools |
|----------|---------------------|
| Python + pytest | Python environment tools, code analysis |
| Node.js + TypeScript | TypeScript linting, npm tools |
| Terraform + Azure | Azure Bicep/Terraform generators, resource lookup |
| PostgreSQL + Python | Database schema tools |
| Docker | Container registry, compose orchestration |

**You decide**: "Yes, I'd use that" → Tool gets added to the suggestion list. "No, not relevant" → Skip it.

### 4. Get Secondary Suggestions

Based on your primary MCP selections, the skill suggests:
- **Complementary skills** (in this workspace or globally)
- **Related tools** (that pair well together, e.g., Azure deploy + Azure validate)
- **Other MCP servers** that enhance the chosen ones

### 5. Implement & Confirm

The skill generates:
1. A **summary document** [suggestion template](./assets/suggestion-template.md) with all picks
2. **Quick-start commands** to enable selected tools or load skills
3. **Related skills to create next** — suggests follow-up skill creation based on detected patterns

## Reference Materials

- [MCP Servers & Tools Database](./references/mcp-database.md) — Complete list of free-tier MCP servers, tools, and extensions
- [Detection Script](./scripts/detect-dependencies.ps1) — PowerShell script that runs folder analysis
- [Suggestion Template](./assets/suggestion-template.md) — Output format for recommendations

## Tips

- **Quick mode** (30s) scans root files only; good for first impression
- **Medium mode** (2–3 min) includes one level of subdirectories; best default
- **Thorough mode** (5–10 min) crawls entire tree; best for large monorepos or unfamiliar projects
- **Re-run anytime**: Helpful when adding new file types or frameworks to a project
- **Hook future**: Once you build the Explorer watch hook, this skill becomes part of an automated workflow

## Common Outputs

**Django + PostgreSQL project:**
```
✓ Suggested: Python environment tools, Kusto (for logs), Database schema inspection
✓ Complementary: Azure deploy + Azure validate (if using Azure)
✓ Related: App Insights instrumentation (for monitoring)
```

**Terraform + Azure Infrastructure:**
```
✓ Suggested: Azure IaC Generator, Azure resource lookup, Azure compliance audits
✓ Complementary: Cloud Architect (for design review), Azure deploy
✓ Related: Azure RBAC (for identity/access), Azure cost optimization
```

**Monorepo (frontend + backend + infra):**
```
✓ Suggested: Multiple tools per subdirectory
✓ Complementary: Root-level orchestration (npm workspaces, yarn, pnpm)
✓ Related: CI/CD pipeline tools, multi-language linting
```
