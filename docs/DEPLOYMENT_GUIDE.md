# 🚀 Convergio Deployment Guide

*Comprehensive deployment and installation guide for the Convergio AI platform*

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Quick Start Deployment](#quick-start-deployment)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Cloud Platform Deployment](#cloud-platform-deployment)
8. [Configuration Management](#configuration-management)
9. [Security Hardening](#security-hardening)
10. [Monitoring & Maintenance](#monitoring--maintenance)

## Overview

Convergio is a unified AI platform that can be deployed in various configurations:

- **Development**: Single-server setup for testing and development
- **Production**: Multi-server setup with load balancing and redundancy
- **Cloud**: Managed cloud deployment on AWS, Azure, or GCP
- **Kubernetes**: Container orchestration for scalability
- **Hybrid**: On-premises with cloud AI services

### Architecture Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (SvelteKit)   │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│   Port: 4000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │     Redis       │              │
         └──────────────│   (Cache/Queue) │──────────────┘
                        │   Port: 6379    │
                        └─────────────────┘
```

## System Requirements

### Minimum Requirements

**Development Environment:**
- **CPU**: 4 cores (Intel i5/AMD Ryzen 5 equivalent)
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **OS**: Ubuntu 20.04+, macOS 12+, Windows 11 with WSL2

**Production Environment:**
- **CPU**: 8 cores (Intel Xeon/AMD EPYC)
- **RAM**: 32 GB
- **Storage**: 200 GB SSD (NVME preferred)
- **Network**: 1 Gbps
- **OS**: Ubuntu 20.04 LTS or CentOS 8

### Recommended Requirements

**Production Environment:**
- **CPU**: 16+ cores
- **RAM**: 64+ GB
- **Storage**: 500+ GB NVMe SSD
- **Network**: 10 Gbps
- **Database**: Dedicated server with 32+ GB RAM
- **Cache**: Dedicated Redis server with 16+ GB RAM

### Software Dependencies

**Required:**
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Nginx 1.20+

**Optional:**
- Docker 24+
- Kubernetes 1.25+
- Prometheus/Grafana
- ELK Stack

## Quick Start Deployment

### Local Development Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourdomain/convergio.git
   cd convergio
   ```

2. **Backend Setup**
   ```bash
   cd backend
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Setup environment
   cp .env.example .env
   # Edit .env with your configuration
   
   # Initialize database
   alembic upgrade head
   
   # Start backend
   uvicorn src.main:app --reload --port 8000
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   
   # Install dependencies
   npm install
   
   # Setup environment
   cp .env.example .env.local
   # Edit .env.local
   
   # Start frontend
   npm run dev
   ```

4. **Access Application**
   - Frontend: http://localhost:4000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Database Setup

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # CentOS/RHEL
   sudo dnf install postgresql postgresql-server postgresql-contrib
   sudo postgresql-setup --initdb
   ```

2. **Create Database**
   ```bash
   sudo -u postgres psql
   ```
   ```sql
   CREATE DATABASE convergio;
   CREATE USER convergio_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE convergio TO convergio_user;
   \q
   ```

3. **Configure PostgreSQL**
   ```bash
   # Edit postgresql.conf
   sudo nano /etc/postgresql/14/main/postgresql.conf
   
   # Key settings:
   max_connections = 200
   shared_buffers = 256MB
   effective_cache_size = 1GB
   work_mem = 4MB
   
   # Edit pg_hba.conf for authentication
   sudo nano /etc/postgresql/14/main/pg_hba.conf
   
   # Add line:
   local   convergio   convergio_user   md5
   
   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

### Redis Setup

1. **Install Redis**
   ```bash
   # Ubuntu/Debian
   sudo apt install redis-server
   
   # CentOS/RHEL
   sudo dnf install redis
   ```

2. **Configure Redis**
   ```bash
   sudo nano /etc/redis/redis.conf
   
   # Key settings:
   maxmemory 2gb
   maxmemory-policy allkeys-lru
   save 900 1
   save 300 10
   save 60 10000
   
   # Start Redis
   sudo systemctl start redis
   sudo systemctl enable redis
   ```

## Production Deployment

### Server Preparation

1. **System Updates**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install build-essential curl wget git htop
   ```

2. **Create Service User**
   ```bash
   sudo useradd -m -s /bin/bash convergio
   sudo usermod -aG sudo convergio
   ```

3. **Install Dependencies**
   ```bash
   # Python 3.11
   sudo apt install python3.11 python3.11-venv python3.11-dev
   
   # Node.js 18
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt install -y nodejs
   
   # Nginx
   sudo apt install nginx
   ```

### Application Deployment

1. **Deploy Backend**
   ```bash
   # Switch to service user
   sudo su - convergio
   
   # Clone and setup
   git clone https://github.com/yourdomain/convergio.git
   cd convergio/backend
   
   # Create virtual environment
   python3.11 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install gunicorn
   
   # Setup environment
   cp .env.example .env
   # Configure production settings
   
   # Run migrations
   alembic upgrade head
   
   # Test application
   gunicorn src.main:app --bind 0.0.0.0:8000 --workers 4
   ```

2. **Deploy Frontend**
   ```bash
   cd ../frontend
   
   # Install dependencies
   npm ci --production
   
   # Build for production
   npm run build
   
   # Test build
   npm run preview
   ```

3. **Create Systemd Services**

   **Backend Service** (`/etc/systemd/system/convergio-backend.service`):
   ```ini
   [Unit]
   Description=Convergio Backend API
   After=network.target postgresql.service redis.service
   Requires=postgresql.service redis.service
   
   [Service]
   Type=notify
   User=convergio
   Group=convergio
   WorkingDirectory=/home/convergio/convergio/backend
   Environment=PATH=/home/convergio/convergio/backend/venv/bin
   ExecStart=/home/convergio/convergio/backend/venv/bin/gunicorn src.main:app --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
   ExecReload=/bin/kill -s HUP $MAINPID
   Restart=always
   RestartSec=10
   KillMode=mixed
   TimeoutStopSec=5
   PrivateTmp=true
   
   [Install]
   WantedBy=multi-user.target
   ```

   **Frontend Service** (`/etc/systemd/system/convergio-frontend.service`):
   ```ini
   [Unit]
   Description=Convergio Frontend
   After=network.target
   
   [Service]
   Type=simple
   User=convergio
   Group=convergio
   WorkingDirectory=/home/convergio/convergio/frontend
   ExecStart=/usr/bin/node build/index.js
   Restart=always
   RestartSec=10
   Environment=NODE_ENV=production
   Environment=PORT=3000
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Start Services**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable convergio-backend convergio-frontend
   sudo systemctl start convergio-backend convergio-frontend
   
   # Check status
   sudo systemctl status convergio-backend
   sudo systemctl status convergio-frontend
   ```

### Nginx Configuration

1. **Create Nginx Configuration** (`/etc/nginx/sites-available/convergio`):
   ```nginx
   upstream backend {
       least_conn;
       server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
   }
   
   upstream frontend {
       server 127.0.0.1:3000 max_fails=3 fail_timeout=30s;
   }
   
   # Redirect HTTP to HTTPS
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;
       return 301 https://$server_name$request_uri;
   }
   
   # Main HTTPS server
   server {
       listen 443 ssl http2;
       server_name yourdomain.com www.yourdomain.com;
   
       # SSL Configuration
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       ssl_session_timeout 1d;
       ssl_session_cache shared:SSL:50m;
       ssl_session_tickets off;
   
       # Modern configuration
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
       ssl_prefer_server_ciphers off;
   
       # HSTS
       add_header Strict-Transport-Security "max-age=63072000" always;
   
       # Security headers
       add_header X-Frame-Options DENY;
       add_header X-Content-Type-Options nosniff;
       add_header X-XSS-Protection "1; mode=block";
       add_header Referrer-Policy "strict-origin-when-cross-origin";
       add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss:";
   
       # Gzip compression
       gzip on;
       gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
   
       # Rate limiting
       limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
       limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
   
       # Backend API
       location /api/ {
           limit_req zone=api burst=20 nodelay;
           
           proxy_pass http://backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           
           proxy_connect_timeout 60s;
           proxy_send_timeout 60s;
           proxy_read_timeout 60s;
           
           # WebSocket support
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   
       # Health checks
       location /health {
           proxy_pass http://backend;
           access_log off;
       }
   
       # Metrics (restrict access)
       location /metrics {
           proxy_pass http://backend;
           allow 10.0.0.0/8;
           allow 172.16.0.0/12;
           allow 192.168.0.0/16;
           deny all;
       }
   
       # Frontend application
       location / {
           proxy_pass http://frontend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   
       # Static assets with caching
       location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
           proxy_pass http://frontend;
           expires 1y;
           add_header Cache-Control "public, immutable";
       }
   }
   ```

2. **Enable Site and SSL**
   ```bash
   # Enable site
   sudo ln -s /etc/nginx/sites-available/convergio /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   
   # Install Certbot for SSL
   sudo snap install core; sudo snap refresh core
   sudo snap install --classic certbot
   sudo ln -s /snap/bin/certbot /usr/bin/certbot
   
   # Get SSL certificate
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   
   # Test auto-renewal
   sudo certbot renew --dry-run
   ```

## Docker Deployment

### Dockerfile Configuration

**Backend Dockerfile** (`backend/Dockerfile`):
```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=app:app . .

# Switch to app user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "src.main:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]
```

**Frontend Dockerfile** (`frontend/Dockerfile`):
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine AS production

RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

WORKDIR /app

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/build ./build
COPY --from=builder /app/package*.json ./

# Install production dependencies only
RUN npm ci --only=production && npm cache clean --force

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

CMD ["node", "build/index.js"]
```

### Docker Compose Configuration

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    container_name: convergio-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: convergio
      POSTGRES_USER: convergio_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256 --auth-local=scram-sha-256"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U convergio_user -d convergio"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  redis:
    image: redis:7-alpine
    container_name: convergio-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: convergio-backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://convergio_user:${POSTGRES_PASSWORD}@postgres:5432/convergio
      REDIS_URL: redis://redis:6379
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      JWT_SECRET: ${JWT_SECRET}
      ENVIRONMENT: production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./backend/logs:/app/logs
      - ./backend/data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: convergio-frontend
    restart: unless-stopped
    environment:
      PUBLIC_API_URL: http://backend:8000
      NODE_ENV: production
    depends_on:
      backend:
        condition: service_healthy
    ports:
      - "3000:3000"

  nginx:
    image: nginx:alpine
    container_name: convergio-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
  nginx_logs:

networks:
  default:
    name: convergio-network
```

**Environment File** (`.env`):
```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# Application
JWT_SECRET=your_jwt_secret_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Security
SECRET_KEY=your_secret_key

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Monitoring
PROMETHEUS_ENABLED=true
```

### Docker Deployment Commands

```bash
# Clone repository
git clone https://github.com/yourdomain/convergio.git
cd convergio

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Scale backend
docker-compose up -d --scale backend=3

# Update application
git pull
docker-compose build
docker-compose up -d

# Backup database
docker-compose exec postgres pg_dump -U convergio_user convergio > backup.sql

# Restore database
docker-compose exec -T postgres psql -U convergio_user convergio < backup.sql
```

## Kubernetes Deployment

### Namespace and ConfigMap

**namespace.yaml**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: convergio
  labels:
    name: convergio
```

**configmap.yaml**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: convergio-config
  namespace: convergio
data:
  DATABASE_URL: "postgresql://convergio_user:password@postgres:5432/convergio"
  REDIS_URL: "redis://redis:6379"
  ENVIRONMENT: "production"
  CORS_ORIGINS: "https://yourdomain.com"
```

### Database Deployment

**postgres-deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: convergio
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14-alpine
        env:
        - name: POSTGRES_DB
          value: convergio
        - name: POSTGRES_USER
          value: convergio_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: convergio-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: convergio
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### Application Deployment

**backend-deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: convergio-backend
  namespace: convergio
spec:
  replicas: 3
  selector:
    matchLabels:
      app: convergio-backend
  template:
    metadata:
      labels:
        app: convergio-backend
    spec:
      containers:
      - name: backend
        image: yourdomain/convergio-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: convergio-config
        - secretRef:
            name: convergio-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: convergio-backend
  namespace: convergio
spec:
  selector:
    app: convergio-backend
  ports:
  - port: 8000
    targetPort: 8000
```

### Ingress Configuration

**ingress.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: convergio-ingress
  namespace: convergio
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - yourdomain.com
    secretName: convergio-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: convergio-backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: convergio-frontend
            port:
              number: 3000
```

### Horizontal Pod Autoscaler

**hpa.yaml**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: convergio-backend-hpa
  namespace: convergio
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: convergio-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Cloud Platform Deployment

### AWS Deployment

**ECS Task Definition**:
```json
{
  "family": "convergio-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/convergio-task-role",
  "containerDefinitions": [
    {
      "name": "convergio-backend",
      "image": "yourdomain/convergio-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:convergio/database"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:convergio/openai"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/convergio-backend",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

**Terraform Configuration**:
```hcl
# main.tf
provider "aws" {
  region = var.aws_region
}

# VPC and Networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "convergio-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = false
  
  tags = {
    Environment = "production"
    Project     = "convergio"
  }
}

# RDS Database
resource "aws_db_instance" "postgres" {
  identifier = "convergio-postgres"
  
  engine         = "postgres"
  engine_version = "14.9"
  instance_class = "db.r6g.large"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type         = "gp3"
  storage_encrypted    = true
  
  db_name  = "convergio"
  username = "convergio_user"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "convergio-postgres-final-snapshot"
  
  tags = {
    Name = "convergio-postgres"
    Environment = "production"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "convergio" {
  name = "convergio"
  
  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      
      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs.name
      }
    }
  }
  
  tags = {
    Environment = "production"
    Project     = "convergio"
  }
}

# Application Load Balancer
resource "aws_lb" "convergio" {
  name               = "convergio-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = module.vpc.public_subnets
  
  enable_deletion_protection = true
  
  tags = {
    Environment = "production"
    Project     = "convergio"
  }
}
```

### Azure Deployment

**ARM Template** (azuredeploy.json):
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "appName": {
      "type": "string",
      "defaultValue": "convergio"
    },
    "location": {
      "type": "string",
      "defaultValue": "[resourceGroup().location]"
    }
  },
  "resources": [
    {
      "type": "Microsoft.ContainerInstance/containerGroups",
      "apiVersion": "2021-03-01",
      "name": "[concat(parameters('appName'), '-backend')]",
      "location": "[parameters('location')]",
      "properties": {
        "containers": [
          {
            "name": "convergio-backend",
            "properties": {
              "image": "yourdomain/convergio-backend:latest",
              "ports": [
                {
                  "port": 8000,
                  "protocol": "TCP"
                }
              ],
              "environmentVariables": [
                {
                  "name": "ENVIRONMENT",
                  "value": "production"
                }
              ],
              "resources": {
                "requests": {
                  "cpu": 2,
                  "memoryInGB": 4
                }
              }
            }
          }
        ],
        "osType": "Linux",
        "ipAddress": {
          "type": "Public",
          "ports": [
            {
              "port": 8000,
              "protocol": "TCP"
            }
          ]
        }
      }
    }
  ]
}
```

### GCP Deployment

**Cloud Run Service**:
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: convergio-backend
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "100"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/execution-environment: gen2
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
      - image: gcr.io/your-project/convergio-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: production
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: convergio-secrets
              key: database-url
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
          requests:
            cpu: "1"
            memory: "2Gi"
```

## Configuration Management

### Environment Variables

**Core Configuration**:
```bash
# Application
APP_NAME=Convergio
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:pass@host:port/db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://host:port/db
REDIS_MAX_CONNECTIONS=100

# AI Services
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
OPENAI_ORG_ID=your_org_id

# Security
JWT_SECRET=your_jwt_secret
SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_encryption_key

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
TRUSTED_HOSTS=yourdomain.com,www.yourdomain.com

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=INFO

# Features
ENABLE_AGENT_HOT_RELOAD=true
ENABLE_GRAPHFLOW=true
ENABLE_COST_TRACKING=true
ENABLE_VECTOR_SEARCH=true

# Limits
MAX_CONCURRENT_CONVERSATIONS=1000
DEFAULT_RATE_LIMIT=100
COST_ALERT_THRESHOLD=0.8
```

### Configuration Files

**config/production.yaml**:
```yaml
app:
  name: "Convergio"
  version: "1.0.0"
  environment: "production"
  debug: false

database:
  url: "${DATABASE_URL}"
  pool_size: 20
  max_overflow: 30
  echo: false
  
redis:
  url: "${REDIS_URL}"
  max_connections: 100
  decode_responses: true

ai_services:
  openai:
    api_key: "${OPENAI_API_KEY}"
    org_id: "${OPENAI_ORG_ID}"
    default_model: "gpt-4-turbo-preview"
    max_tokens: 4000
    temperature: 0.7
    
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    default_model: "claude-3-sonnet"
    max_tokens: 4000
    temperature: 0.7

security:
  jwt_secret: "${JWT_SECRET}"
  jwt_expiry: 28800  # 8 hours
  encryption_key: "${ENCRYPTION_KEY}"
  
cors:
  origins:
    - "https://yourdomain.com"
    - "https://www.yourdomain.com"
  allow_credentials: true
  
rate_limiting:
  default_limit: 100
  default_window: 60
  burst_limit: 10
  
features:
  agent_hot_reload: true
  graphflow: true
  cost_tracking: true
  vector_search: true
  multi_tenancy: false
  
monitoring:
  prometheus: true
  sentry_dsn: "${SENTRY_DSN}"
  log_level: "INFO"
  
cost_management:
  alert_threshold: 0.8
  daily_limit: 1000.0
  emergency_shutdown: false
```

## Security Hardening

### SSL/TLS Configuration

1. **Strong SSL Configuration**
   ```nginx
   # SSL protocols and ciphers
   ssl_protocols TLSv1.2 TLSv1.3;
   ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
   ssl_prefer_server_ciphers off;
   
   # SSL session settings
   ssl_session_timeout 1d;
   ssl_session_cache shared:SSL:50m;
   ssl_session_tickets off;
   
   # OCSP stapling
   ssl_stapling on;
   ssl_stapling_verify on;
   ssl_trusted_certificate /etc/ssl/certs/ca-certificates.crt;
   
   # Security headers
   add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
   add_header X-Frame-Options DENY always;
   add_header X-Content-Type-Options nosniff always;
   add_header X-XSS-Protection "1; mode=block" always;
   add_header Referrer-Policy "strict-origin-when-cross-origin" always;
   ```

2. **Certificate Management**
   ```bash
   # Automated certificate renewal
   crontab -e
   
   # Add line:
   0 12 * * * /usr/bin/certbot renew --quiet
   ```

### Firewall Configuration

1. **UFW Setup**
   ```bash
   # Reset firewall
   sudo ufw --force reset
   
   # Default policies
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   
   # SSH access (change default port)
   sudo ufw allow 2222/tcp
   
   # HTTP/HTTPS
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   
   # Database (only from app servers)
   sudo ufw allow from 10.0.1.0/24 to any port 5432
   
   # Redis (only from app servers)
   sudo ufw allow from 10.0.1.0/24 to any port 6379
   
   # Enable firewall
   sudo ufw enable
   ```

2. **Fail2Ban Configuration**
   ```bash
   # Install fail2ban
   sudo apt install fail2ban
   
   # Create custom jail
   sudo nano /etc/fail2ban/jail.local
   ```
   
   ```ini
   [DEFAULT]
   bantime = 3600
   findtime = 600
   maxretry = 5
   
   [sshd]
   enabled = true
   port = 2222
   
   [nginx-http-auth]
   enabled = true
   
   [nginx-limit-req]
   enabled = true
   filter = nginx-limit-req
   action = iptables-multiport[name=ReqLimit, port="http,https", protocol=tcp]
   logpath = /var/log/nginx/error.log
   findtime = 600
   bantime = 7200
   maxretry = 10
   ```

### Application Security

1. **Environment Security**
   ```bash
   # Secure environment file
   sudo chown root:convergio /etc/convergio/.env
   sudo chmod 640 /etc/convergio/.env
   
   # Secure secrets directory
   sudo chmod 700 /etc/convergio/secrets
   sudo chown -R root:convergio /etc/convergio/secrets
   ```

2. **Database Security**
   ```sql
   -- Create read-only user for monitoring
   CREATE USER monitoring WITH PASSWORD 'secure_password';
   GRANT CONNECT ON DATABASE convergio TO monitoring;
   GRANT USAGE ON SCHEMA public TO monitoring;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring;
   
   -- Revoke unnecessary permissions
   REVOKE ALL ON DATABASE convergio FROM PUBLIC;
   ```

## Monitoring & Maintenance

### Health Monitoring

1. **Application Health Checks**
   ```bash
   #!/bin/bash
   # health_check.sh
   
   # Check application health
   curl -f http://localhost:8000/health || exit 1
   
   # Check database connectivity
   pg_isready -h localhost -p 5432 -U convergio_user || exit 1
   
   # Check Redis connectivity
   redis-cli ping || exit 1
   
   # Check disk space
   df -h / | awk 'NR==2{if($5+0 > 90) exit 1}'
   
   # Check memory usage
   free | awk 'NR==2{if($3/$2 > 0.9) exit 1}'
   ```

2. **Monitoring Stack**
   ```yaml
   # monitoring/docker-compose.yml
   version: '3.8'
   
   services:
     prometheus:
       image: prom/prometheus:latest
       ports:
         - "9090:9090"
       volumes:
         - ./prometheus.yml:/etc/prometheus/prometheus.yml
         - prometheus_data:/prometheus
   
     grafana:
       image: grafana/grafana:latest
       ports:
         - "3001:3000"
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=admin
       volumes:
         - grafana_data:/var/lib/grafana
         - ./dashboards:/var/lib/grafana/dashboards
   
     alertmanager:
       image: prom/alertmanager:latest
       ports:
         - "9093:9093"
       volumes:
         - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
   
   volumes:
     prometheus_data:
     grafana_data:
   ```

### Backup Strategy

1. **Automated Backups**
   ```bash
   #!/bin/bash
   # backup.sh
   
   BACKUP_DIR="/backups/convergio"
   DATE=$(date +%Y%m%d_%H%M%S)
   
   # Database backup
   pg_dump -h localhost -U convergio_user convergio | gzip > \
     "$BACKUP_DIR/convergio_db_$DATE.sql.gz"
   
   # Redis backup
   redis-cli --rdb "$BACKUP_DIR/convergio_redis_$DATE.rdb"
   
   # Application data backup
   tar -czf "$BACKUP_DIR/convergio_data_$DATE.tar.gz" \
     /home/convergio/convergio/backend/data
   
   # Upload to cloud storage
   aws s3 sync $BACKUP_DIR s3://company-backups/convergio/
   
   # Clean old backups (keep 30 days)
   find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
   find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete
   ```

2. **Backup Schedule**
   ```bash
   # Add to crontab
   crontab -e
   
   # Full backup daily at 2 AM
   0 2 * * * /opt/convergio/scripts/backup.sh
   
   # Incremental backup every 6 hours
   0 */6 * * * /opt/convergio/scripts/incremental_backup.sh
   ```

### Log Management

1. **Log Rotation**
   ```bash
   # /etc/logrotate.d/convergio
   /var/log/convergio/*.log {
       daily
       missingok
       rotate 30
       compress
       delaycompress
       notifempty
       create 0644 convergio convergio
       postrotate
           systemctl reload convergio
       endscript
   }
   ```

2. **Centralized Logging**
   ```yaml
   # filebeat.yml
   filebeat.inputs:
   - type: log
     enabled: true
     paths:
       - /var/log/convergio/*.log
     fields:
       service: convergio
       environment: production
   
   output.elasticsearch:
     hosts: ["elasticsearch:9200"]
     index: "convergio-logs-%{+yyyy.MM.dd}"
   ```

---

*This deployment guide provides comprehensive instructions for deploying Convergio in various environments. For specific deployment questions or issues, consult the troubleshooting guide or contact technical support.*

*Last updated: August 2025 - Convergio FASE 11 Deployment Guide*