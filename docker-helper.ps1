# Convergio Docker Helper Script (PowerShell)

param(
    [Parameter(Position=0)]
    [string]$Command = "",
    
    [Parameter(Position=1)]
    [string]$Service = ""
)

# Colors for output
$ErrorActionPreference = "Stop"

function Write-Header {
    Write-Host "🐳 Convergio Docker Helper" -ForegroundColor Blue
    Write-Host "=========================" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Test-Dependencies {
    try {
        $null = Get-Command docker -ErrorAction Stop
        $null = Get-Command docker-compose -ErrorAction Stop
        Write-Success "Docker dependencies are available"
        return $true
    }
    catch {
        Write-Error "Docker or Docker Compose is not installed or not in PATH"
        return $false
    }
}

function Test-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found. Creating from template..."
        if (Test-Path "backend\.env.example") {
            Copy-Item "backend\.env.example" ".env"
            Write-Warning "Please edit .env file and add your API keys before starting services"
            return $false
        }
        else {
            Write-Error "No .env.example template found"
            exit 1
        }
    }
    Write-Success ".env file found"
    return $true
}

function Start-Services {
    Write-Header
    
    if (-not (Test-Dependencies)) {
        exit 1
    }
    
    $envOk = Test-EnvFile
    
    if (-not $envOk) {
        Write-Host ""
        Write-Warning "Please edit the .env file with your API keys and run this script again"
        exit 1
    }
    
    Write-Host ""
    Write-Host "Starting Convergio services..." -ForegroundColor Blue
    docker-compose up -d
    
    Write-Host ""
    Write-Success "Services started! Waiting for health checks..."
    Start-Sleep -Seconds 10
    
    Write-Host ""
    Write-Host "Service Status:" -ForegroundColor Blue
    docker-compose ps
    
    Write-Host ""
    Write-Host "Access URLs:" -ForegroundColor Blue
    Write-Host "Frontend:  http://localhost:4000"
    Write-Host "Backend:   http://localhost:9000"
    Write-Host "API Docs:  http://localhost:9000/docs"
    Write-Host "Health:    http://localhost:9000/health"
}

function Stop-Services {
    Write-Header
    Write-Host "Stopping Convergio services..." -ForegroundColor Blue
    docker-compose down
    Write-Success "Services stopped"
}

function Restart-Services {
    Write-Header
    Write-Host "Restarting Convergio services..." -ForegroundColor Blue
    docker-compose restart
    Write-Success "Services restarted"
}

function Show-Logs {
    param([string]$ServiceName)
    
    if ([string]::IsNullOrEmpty($ServiceName)) {
        Write-Host "Viewing all service logs (Ctrl+C to exit):" -ForegroundColor Blue
        docker-compose logs -f
    }
    else {
        Write-Host "Viewing logs for $ServiceName (Ctrl+C to exit):" -ForegroundColor Blue
        docker-compose logs -f $ServiceName
    }
}

function Show-Status {
    Write-Header
    Write-Host "Service Status:" -ForegroundColor Blue
    docker-compose ps
    
    Write-Host ""
    Write-Host "Resource Usage:" -ForegroundColor Blue
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

function Invoke-Cleanup {
    Write-Header
    Write-Warning "This will remove all containers, networks, and volumes (including data!)"
    $confirmation = Read-Host "Are you sure? (y/N)"
    
    if ($confirmation -eq "y" -or $confirmation -eq "Y") {
        Write-Host "Cleaning up Convergio deployment..." -ForegroundColor Blue
        docker-compose down -v --remove-orphans
        Write-Success "Cleanup completed"
    }
    else {
        Write-Success "Cleanup cancelled"
    }
}

function Fix-BuildIssues {
    Write-Header
    Write-Host "Fixing common Docker build issues..." -ForegroundColor Blue
    
    Write-Host "1. Clearing Docker build cache..." -ForegroundColor Yellow
    docker system prune -f
    
    Write-Host "2. Rebuilding backend with no cache..." -ForegroundColor Yellow
    docker-compose build --no-cache backend
    
    Write-Success "Build fix attempt completed"
}

function Build-Minimal {
    Write-Header
    Write-Warning "This will use minimal requirements to build the backend"
    Write-Host "Building backend with minimal dependencies..." -ForegroundColor Blue
    
    # Temporarily replace Dockerfile
    Copy-Item "backend\Dockerfile" "backend\Dockerfile.backup"
    Copy-Item "backend\Dockerfile.minimal" "backend\Dockerfile"
    
    try {
        docker-compose build --no-cache backend
        Write-Success "Minimal build completed successfully"
    }
    catch {
        Write-Error "Minimal build failed: $_"
    }
    finally {
        # Restore original Dockerfile
        Move-Item "backend\Dockerfile.backup" "backend\Dockerfile" -Force
    }
}

function Build-NoOtel {
    Write-Header
    Write-Warning "This will build backend without OpenTelemetry packages to avoid protobuf conflicts"
    Write-Host "Building backend without OpenTelemetry..." -ForegroundColor Blue
    
    # Temporarily replace requirements
    Copy-Item "backend\requirements.txt" "backend\requirements.txt.backup"
    Copy-Item "backend\requirements-no-otel.txt" "backend\requirements.txt"
    
    try {
        docker-compose build --no-cache backend
        Write-Success "No-OpenTelemetry build completed successfully"
    }
    catch {
        Write-Error "No-OpenTelemetry build failed: $_"
    }
    finally {
        # Restore original requirements
        Move-Item "backend\requirements.txt.backup" "backend\requirements.txt" -Force
    }
}

function Test-Requirements {
    Write-Header
    Write-Host "Checking requirements.txt for conflicts..." -ForegroundColor Blue
    
    $requirements = Get-Content "backend\requirements.txt" | Where-Object { $_ -match "^[a-zA-Z0-9_-]+[=><]" }
    $packages = @{}
    $conflicts = @()
    
    foreach ($line in $requirements) {
        if ($line -match "^([a-zA-Z0-9_-]+)[\[\w\]]*[=><]") {
            $packageName = $matches[1]
            if ($packages.ContainsKey($packageName)) {
                $conflicts += "Duplicate package: $packageName"
                $conflicts += "  Previous: $($packages[$packageName])"
                $conflicts += "  Current:  $line"
            } else {
                $packages[$packageName] = $line
            }
        }
    }
    
    if ($conflicts.Count -gt 0) {
        Write-Error "Package conflicts found:"
        $conflicts | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        return $false
    } else {
        Write-Success "No package conflicts found in requirements.txt"
        return $true
    }
}

function Show-Help {
    Write-Header
    Write-Host ""
    Write-Host "Usage: .\docker-helper.ps1 [COMMAND] [OPTIONS]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  start              Start all services"
    Write-Host "  stop               Stop all services"
    Write-Host "  restart            Restart all services"
    Write-Host "  status             Show service status and resource usage"
    Write-Host "  logs [SERVICE]     View logs (all services or specific service)"
    Write-Host "  cleanup            Remove all containers and data (⚠️  destructive)"
    Write-Host "  fix-build          Fix common Docker build issues"
    Write-Host "  build-minimal      Build backend with minimal dependencies"
    Write-Host "  build-no-otel      Build backend without OpenTelemetry (avoids protobuf conflicts)"
    Write-Host "  test-requirements  Check requirements.txt for conflicts"
    Write-Host "  help               Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\docker-helper.ps1 start           # Start all services"
    Write-Host "  .\docker-helper.ps1 logs backend    # View backend logs"
    Write-Host "  .\docker-helper.ps1 logs            # View all logs"
    Write-Host "  .\docker-helper.ps1 status          # Check service status"
    Write-Host "  .\docker-helper.ps1 fix-build       # Fix build issues"
    Write-Host ""
}

# Main script logic
switch ($Command.ToLower()) {
    "start" {
        Start-Services
    }
    "stop" {
        Stop-Services
    }
    "restart" {
        Restart-Services
    }
    "logs" {
        Show-Logs $Service
    }
    "status" {
        Show-Status
    }
    "cleanup" {
        Invoke-Cleanup
    }
    "fix-build" {
        Fix-BuildIssues
    }
    "build-minimal" {
        Build-Minimal
    }
    "build-no-otel" {
        Build-NoOtel
    }
    "test-requirements" {
        Test-Requirements
    }
    "help" {
        Show-Help
    }
    "" {
        Show-Help
    }
    default {
        Write-Error "Unknown command: $Command"
        Write-Host ""
        Show-Help
        exit 1
    }
}