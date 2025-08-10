# Convergio Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Environment Variables](#environment-variables)
7. [Security Checklist](#security-checklist)
8. [Monitoring & Maintenance](#monitoring--maintenance)

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 20GB minimum

### Software Requirements
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)
- Kubernetes 1.25+ (for K8s deployment)

## Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/convergio/convergio.git
cd convergio
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
# Optional: set `DEFAULT_AI_MODEL` (default `gpt-5-nano`) for the backend global model.
# End users can also pick per-session model in the frontend Settings (gpt-5, gpt-5-mini, gpt-5-nano).
```

#### Initialize Database
```bash
# Create database
createdb convergio_db

# Run migrations
python -m alembic upgrade head

# Seed initial data (optional)
python scripts/seed_data.py
```

#### Start Backend Server
```bash
uvicorn src.main:app --host 0.0.0.0 --port 9000 --reload
```

### 3. Frontend Setup

#### Install Node Dependencies
```bash
cd frontend
npm install
```

#### Configure Environment
```bash
cp .env.example .env
# Edit .env with API URL
```

#### Start Frontend Server
```bash
npm run dev
# Frontend will be available at http://localhost:5173
```

## Docker Deployment

### 1. Build and Run with Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: convergio_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/convergio_db
      REDIS_URL: redis://redis:6379
      ENVIRONMENT: production
    ports:
      - "9000:9000"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    environment:
      VITE_API_URL: http://backend:9000
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

### 2. Deploy with Docker
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Production Deployment

### 1. Server Preparation

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3-pip postgresql redis nginx certbot

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Application Setup

#### Create Application User
```bash
sudo useradd -m -s /bin/bash convergio
sudo su - convergio
```

#### Deploy Application
```bash
# Clone repository
git clone https://github.com/convergio/convergio.git
cd convergio

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Systemd Service Configuration

#### Backend Service
```ini
# /etc/systemd/system/convergio-backend.service
[Unit]
Description=Convergio Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=convergio
Group=convergio
WorkingDirectory=/home/convergio/convergio/backend
Environment="PATH=/home/convergio/convergio/backend/venv/bin"
ExecStart=/home/convergio/convergio/backend/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 9000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable convergio-backend
sudo systemctl start convergio-backend
```

### 4. Nginx Configuration

```nginx
# /etc/nginx/sites-available/convergio
server {
    listen 80;
    server_name convergio.example.com;

    # Frontend
    location / {
        root /home/convergio/convergio/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5. SSL Configuration
```bash
# Install SSL certificate
sudo certbot --nginx -d convergio.example.com
```

## Kubernetes Deployment

### 1. Kubernetes Manifests

#### Deployment
```yaml
# k8s/deployment.yaml
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
        image: convergio/backend:latest
        ports:
        - containerPort: 9000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: convergio-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: convergio-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 9000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 9000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: convergio-backend
  namespace: convergio
spec:
  selector:
    app: convergio-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 9000
  type: LoadBalancer
```

#### Ingress
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: convergio-ingress
  namespace: convergio
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - convergio.example.com
    secretName: convergio-tls
  rules:
  - host: convergio.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: convergio-backend
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: convergio-frontend
            port:
              number: 80
```

### 2. Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace convergio

# Create secrets
kubectl create secret generic convergio-secrets \
  --from-literal=database-url=$DATABASE_URL \
  --from-literal=redis-url=$REDIS_URL \
  -n convergio

# Apply manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n convergio
kubectl get svc -n convergio
```

## Environment Variables

### Required Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/convergio_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=convergio_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Service Configuration
HOST=0.0.0.0
PORT=9000
WORKERS=4
```

### Optional Variables
```bash
# Monitoring
SENTRY_DSN=https://...@sentry.io/...
PROMETHEUS_PORT=9090

# Storage
S3_BUCKET=convergio-storage
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
```

## Security Checklist

### Pre-Deployment
- [ ] Change all default passwords
- [ ] Generate strong JWT secret
- [ ] Configure CORS properly
- [ ] Enable HTTPS/TLS
- [ ] Set secure file permissions (600 for .env)
- [ ] Remove debug mode in production
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up fail2ban

### Post-Deployment
- [ ] Verify SSL certificate
- [ ] Test authentication flow
- [ ] Check security headers
- [ ] Run security audit
- [ ] Configure backup strategy
- [ ] Set up monitoring alerts
- [ ] Document emergency procedures

## Monitoring & Maintenance

### Health Checks
```bash
# API health
curl https://convergio.example.com/health

# Database health
psql -U postgres -d convergio_db -c "SELECT 1;"

# Redis health
redis-cli ping
```

### Log Management
```bash
# View backend logs
journalctl -u convergio-backend -f

# View nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Docker logs
docker-compose logs -f backend
```

### Backup Strategy
```bash
# Database backup
pg_dump convergio_db > backup_$(date +%Y%m%d).sql

# Redis backup
redis-cli BGSAVE

# Application backup
tar -czf convergio_backup_$(date +%Y%m%d).tar.gz /home/convergio/convergio
```

### Updates
```bash
# Update application
cd /home/convergio/convergio
git pull origin main

# Update dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart services
sudo systemctl restart convergio-backend
```

## Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -U postgres -h localhost -d convergio_db

# Check logs
sudo journalctl -u postgresql
```

#### Redis Connection Failed
```bash
# Check Redis status
sudo systemctl status redis

# Test connection
redis-cli ping

# Check configuration
cat /etc/redis/redis.conf | grep bind
```

#### Port Already in Use
```bash
# Find process using port
sudo lsof -i :9000

# Kill process
sudo kill -9 <PID>
```

#### Permission Denied
```bash
# Fix file permissions
sudo chown -R convergio:convergio /home/convergio/convergio
chmod 600 backend/.env
```

## Support

For deployment support:
- Documentation: https://docs.convergio.com
- GitHub Issues: https://github.com/convergio/convergio/issues
- Email: support@convergio.com
