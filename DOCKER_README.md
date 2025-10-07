# 🐳 Convergio Docker Deployment

This directory contains Docker Compose configuration for running Convergio in a containerized environment suitable for testing and development.

## 🏗️ Architecture

The Docker Compose setup includes:

- **PostgreSQL 16** with pgvector extension for vector operations
- **Redis 7** for caching and session storage
- **Backend** (Python FastAPI) running on port 9000
- **Frontend** (SvelteKit) running on port 4000

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB of available RAM
- Ports 4000, 5432, 6379, and 9000 available

### 1. Environment Setup

Create `.env` file in the root directory with your API keys:

```bash
# Copy and customize the environment template
cp backend/.env.example .env


# Edit .env and add your API keys
OPENAI_API_KEY=your-actual-openai-api-key
ANTHROPIC_API_KEY=your-actual-anthropic-api-key
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Start specific service
docker-compose up -d postgres redis
docker-compose up backend frontend
```

### 3. Verify Deployment

- **Frontend**: http://localhost:4000
- **Backend API**: http://localhost:9000
- **API Documentation**: http://localhost:9000/docs
- **Health Check**: http://localhost:9000/health

## 🔧 Configuration

### Database Initialization

The PostgreSQL container automatically runs migration scripts from `backend/migrations/` on first startup.

### Environment Variables

Key environment variables for the backend:

```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_DB=convergio_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# AI APIs (Required)
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Security (Change in production!)
SERVICE_REGISTRY_SECRET=development-secret-key-64-chars-long-change-in-production
JWT_SECRET=development-jwt-secret-change-in-production
```

## 🛠️ Development Workflow

### Logs and Debugging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Check service status
docker-compose ps
```

### Database Operations

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d convergio_db

# View database data
docker volume ls | grep convergio
```

### Rebuild Services

```bash
# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Rebuild all services
docker-compose build
docker-compose up -d
```

## 🔄 Data Persistence

Data is persisted using Docker volumes:

- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis data files

### Backup and Restore

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres convergio_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres convergio_db < backup.sql
```

## 🧹 Cleanup

```bash
# Stop all services
docker-compose down

# Remove containers and networks (keeps volumes)
docker-compose down --remove-orphans

# Remove everything including volumes (⚠️ Data loss!)
docker-compose down -v --remove-orphans
```

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts**: Make sure ports 4000, 5432, 6379, 9000 are available
2. **Memory issues**: Ensure at least 4GB RAM available
3. **Permission errors**: Check Docker daemon permissions
4. **Package hash errors**: If you see "THESE PACKAGES DO NOT MATCH THE HASHES" error during backend build

### Package Hash Error Fix

If you encounter a hash mismatch error during backend build:

```bash
# Clear Docker build cache
docker system prune -f

# Rebuild backend with no cache
docker-compose build --no-cache backend

# If error persists, try building with force reinstall
docker-compose build --no-cache --pull backend
```

The backend Dockerfile has been updated to handle package hash mismatches automatically.

### Health Checks

```bash
# Check service health
docker-compose ps

# Manual health checks
curl http://localhost:9000/health
curl http://localhost:4000
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test database connection
docker-compose exec postgres pg_isready -U postgres
```

## 🔒 Security Notes

⚠️ **Important**: This configuration is for development/testing only!

For production:
- Use secure passwords and secrets
- Enable SSL/TLS
- Configure proper firewall rules
- Use production-grade container orchestration
- Implement proper backup strategies

## 📁 File Structure

```
├── docker-compose.yml          # Main orchestration file
├── backend/
│   ├── Dockerfile             # Backend container definition
│   ├── .dockerignore          # Backend build exclusions
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── Dockerfile             # Frontend container definition
│   ├── .dockerignore          # Frontend build exclusions
│   └── package.json           # Node.js dependencies
└── .env                       # Environment variables (create this)
```

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify all services are healthy: `docker-compose ps`
3. Ensure your `.env` file is properly configured
4. Check Docker and Docker Compose versions