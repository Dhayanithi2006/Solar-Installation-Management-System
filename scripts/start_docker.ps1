# ==============================================================================
# SunPower Solutions — Launch Odoo 18.0 Development Stack
# ==============================================================================

Write-Host "Checking Docker status..." -ForegroundColor Cyan

# Check if Docker is responding
docker info >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker daemon is not running. Launching Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Users\Dhayanithi M U\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe"
    Write-Host "Waiting for Docker daemon to become responsive..." -ForegroundColor Yellow
    $retries = 30
    while ($retries -gt 0) {
        Start-Sleep -Seconds 2
        docker info >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Docker daemon is now responsive!" -ForegroundColor Green
            break
        }
        $retries--
    }
}

Set-Location -Path "$PSScriptRoot\..\config"
Write-Host "Starting Odoo and PostgreSQL containers..." -ForegroundColor Cyan
docker compose up -d

Write-Host "Checking container status..." -ForegroundColor Cyan
docker compose ps

Write-Host "Odoo 18.0 Web Interface: http://localhost:8069" -ForegroundColor Green

