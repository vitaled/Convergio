# 🚀 Quick Start Guide for Windows

This guide will help you get Convergio running with Docker on Windows.

## Prerequisites

1. **Docker Desktop for Windows**
   - Download from: https://docs.docker.com/desktop/windows/install/
   - Make sure WSL 2 is enabled
   - Ensure Docker Desktop is running

2. **PowerShell** (Windows 10/11 includes this by default)

## Quick Setup

### 1. Open PowerShell as Administrator

```powershell
# Navigate to the Convergio directory
cd "C:\Users\dvitale\vitaled.github\Convergio"

# Check if Docker is running
docker --version
docker-compose --version
```

### 2. Set Up Environment

```powershell
# Copy environment template
Copy-Item "backend\.env.example" ".env"

# Edit the .env file with your API keys
notepad .env
```

**Important**: Add your actual API keys to the `.env` file:
```bash
OPENAI_API_KEY=your-actual-openai-api-key-here
ANTHROPIC_API_KEY=your-actual-anthropic-api-key-here
```

### 3. Start Services

Option A: Using the helper script (recommended)
```powershell
# Make sure you can run scripts (run once as admin)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Start all services
.\docker-helper.ps1 start
```

Option B: Using Docker Compose directly
```powershell
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access the Application

- **Frontend**: http://localhost:4000
- **Backend API**: http://localhost:9000
- **API Documentation**: http://localhost:9000/docs

## Common Commands

```powershell
# Check service status
.\docker-helper.ps1 status
# or
docker-compose ps

# View logs
.\docker-helper.ps1 logs
# or
docker-compose logs -f

# View specific service logs
.\docker-helper.ps1 logs backend
# or
docker-compose logs -f backend

# Stop services
.\docker-helper.ps1 stop
# or
docker-compose down

# Restart services
.\docker-helper.ps1 restart
# or
docker-compose restart
```

## Troubleshooting

### Port Conflicts
If you get port conflicts, check what's using the ports:
```powershell
netstat -ano | findstr :4000
netstat -ano | findstr :9000
```

### Permission Issues
If you get permission errors:
```powershell
# Run PowerShell as Administrator
# Set execution policy (one time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Docker Issues
```powershell
# Check Docker status
docker info

# Restart Docker Desktop if needed
# Check Docker Desktop system tray icon
```

### WSL 2 Issues
If you have WSL 2 issues:
1. Enable WSL 2 in Windows Features
2. Install WSL 2 kernel update
3. Set WSL 2 as default: `wsl --set-default-version 2`

## Cleanup

To completely remove all containers and data:
```powershell
# Using helper script
.\docker-helper.ps1 cleanup

# Or manually
docker-compose down -v --remove-orphans
```

## Need Help?

1. Check the logs: `.\docker-helper.ps1 logs`
2. Verify services: `.\docker-helper.ps1 status`
3. Make sure your `.env` file has valid API keys
4. Ensure Docker Desktop is running
5. Check that ports 4000, 5432, 6379, and 9000 are available