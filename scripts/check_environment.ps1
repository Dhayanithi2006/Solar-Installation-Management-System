# ==============================================================================
# SunPower Solutions — Environment & Service Health Check
# ==============================================================================

Write-Host "=== Odoo Environment Health Check ===" -ForegroundColor Cyan

# 1. Check HTTP Port 8069
Write-Host "Testing HTTP connection to Odoo (http://localhost:8069)..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8069/web/login" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host " [OK] (Status: 200 OK)" -ForegroundColor Green
    } else {
        Write-Host " [WARNING] (Status: $($response.StatusCode))" -ForegroundColor Yellow
    }
} catch {
    Write-Host " [OFFLINE] (Server not yet responding on port 8069)" -ForegroundColor Yellow
}

# 2. Check Host PostgreSQL Port 5000
Write-Host "Testing Host PostgreSQL Service on Port 5000..." -NoNewline
$tcp5000 = Test-NetConnection -ComputerName localhost -Port 5000 -WarningAction SilentlyContinue
if ($tcp5000.TcpTestSucceeded) {
    Write-Host " [OK] (Port 5000 Open)" -ForegroundColor Green
} else {
    Write-Host " [OFFLINE]" -ForegroundColor Red
}

# 3. Check Docker Container Status
Write-Host "Testing Docker Containers..." -NoNewline
docker compose -f "$PSScriptRoot\..\config\docker-compose.yml" ps --format json 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host " [OK]" -ForegroundColor Green
    docker compose -f "$PSScriptRoot\..\config\docker-compose.yml" ps
} else {
    Write-Host " [DOCKER STOPPED / NOT RUNNING]" -ForegroundColor Yellow
}

