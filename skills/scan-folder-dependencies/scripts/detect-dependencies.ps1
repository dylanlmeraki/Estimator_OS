# detect-dependencies.ps1
# 
# Usage: .\detect-dependencies.ps1 -FolderPath "C:\my\project" -Scope "medium"
# Scope options: "quick" (root only), "medium" (1 subdir level), "thorough" (full tree)

param(
    [string]$FolderPath = (Get-Location).Path,
    [ValidateSet("quick", "medium", "thorough")]
    [string]$Scope = "medium"
)

# Normalize path
$FolderPath = Resolve-Path $FolderPath -ErrorAction SilentlyContinue
if (-not $FolderPath) {
    Write-Error "Folder not found: $FolderPath"
    exit 1
}

Write-Host "[SCAN] Scanning folder: $FolderPath (Scope: $Scope)" -ForegroundColor Cyan

# Detection patterns (language/framework -> file signatures)
$detectionPatterns = @{
    "Python"           = @('*.py', 'requirements.txt', 'pyproject.toml', 'setup.py', 'poetry.lock', 'Pipfile', 'tox.ini')
    "TypeScript"       = @('tsconfig.json', '*.ts', '*.tsx', '.eslintrc*')
    "JavaScript"       = @('package.json', '*.js', '*.jsx', '.eslintrc*')
    "Node.js"          = @('package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml')
    "Go"               = @('go.mod', 'go.sum', '*.go', 'Gopkg.toml')
    "Java"             = @('pom.xml', 'build.gradle', '*.java', 'Maven.build')
    ".NET/C#"          = @('*.csproj', '*.sln', '*.cs', 'packages.config')
    "Rust"             = @('Cargo.toml', 'Cargo.lock', '*.rs')
    "Terraform"        = @('*.tf', 'terraform.tfvars', '.terraform/', '*.tfstate')
    "Bicep"            = @('*.bicep')
    "Docker"           = @('Dockerfile', 'docker-compose.yml', '.dockerignore')
    "Kubernetes"       = @('k8s/', 'helm/', 'kube*.yaml', 'deployment*.yaml')
    "SQL/Database"     = @('*.sql', 'migrations/', 'schema.sql', '*.prisma')
    "PostgreSQL"       = @('psql', 'pgAdmin', '*.psql', 'migrations/')
    "Azure"            = @('azure.yaml', '.azure/', '*.bicep', 'function_app.py', 'static-web-app.yml')
    "YAML Config"      = @('*.yaml', '*.yml')
    "JSON Schemas"     = @('*.schema.json', '*-dto.json', '*manifest*.json')
    "JSON Data"        = @('*.json')
    "CSV Data"         = @('*.csv')
    "Markdown"         = @('*.md', 'docs/', '.instructions.md', 'SKILL.md')
    "Git"              = @('.git/', '.github/', '.gitignore', 'pull_request_template.md')
    "MCP/Agents"       = @('*.agent.md', '.instructions.md', 'SKILL.md', 'agents/', 'copilot-instructions.md')
    "Testing"          = @('test/', 'spec/', '*.test.ts', 'jest.config.js', 'pytest.ini', '.mocha')
}

# Determine max depth based on scope
$maxDepth = switch ($Scope) {
    "quick"     { 0 }      # Root files only
    "medium"    { 3 }      # Root + 2 levels subdirectories
    "thorough"  { 99 }     # Unlimited recursion
}

# Collect all file names using Get-ChildItem
$allFiles = @()
try {
    if ($maxDepth -eq 0) {
        # Quick: root only (no recursion)
        $allFiles = (Get-ChildItem -Path $FolderPath -File -ErrorAction SilentlyContinue | 
                      Select-Object -ExpandProperty Name)
    } else {
        # Medium/Thorough: use -Recurse with depth limit
        $allFiles = (Get-ChildItem -Path $FolderPath -Recurse -Depth $maxDepth -File -ErrorAction SilentlyContinue | 
                      Where-Object { $_.FullName -notmatch '(node_modules|\.git|\.venv|venv|bin|obj|\.github)' } |
                      Select-Object -ExpandProperty Name)
    }
} catch {
    Write-Host "[ERROR] Failed to scan folder: $_" -ForegroundColor Red
}

if (-not $allFiles) {
    $allFiles = @()
}

# Detect technologies
Write-Host "`n[TECHS] Detected Technologies:" -ForegroundColor Green
$detected = @{}
foreach ($tech in $detectionPatterns.Keys) {
    $patterns = $detectionPatterns[$tech]
    $matches = 0
    foreach ($pattern in $patterns) {
        $matches += ($allFiles | Where-Object { $_ -like $pattern }).Count
    }
    if ($matches -gt 0) {
        $detected[$tech] = $matches
        Write-Host "  [+] $tech (matched $matches files)" -ForegroundColor Yellow
    }
}

if ($detected.Count -eq 0) {
    Write-Host "  [!] No recognized technologies detected. Folder may be empty or use uncommon tech." -ForegroundColor Yellow
}

# Summary statistics
Write-Host "`n[STATS] Folder Statistics:" -ForegroundColor Green
Write-Host "  Total files scanned: $($allFiles.Count)" -ForegroundColor White
Write-Host "  Technologies detected: $($detected.Count)" -ForegroundColor White
Write-Host "  Scan scope: $Scope" -ForegroundColor White

# Output JSON for programmatic consumption
$output = @{
    FolderPath = $FolderPath
    Scope      = $Scope
    Detected   = $detected
    FileCount  = $allFiles.Count
    Timestamp  = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
}

Write-Host "`n[JSON] Output (for integration):" -ForegroundColor Cyan
$output | ConvertTo-Json | Write-Host

# Return exit code for scripting
exit 0
