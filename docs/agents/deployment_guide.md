# Convergio AutoGen Deployment Guide

## Prerequisites

### System Requirements

- **Python**: 3.10+ 
- **Redis**: 7.0+
- **PostgreSQL**: 15+ with pgvector extension
- **Docker**: 20.10+
- **Kubernetes**: 1.25+ (for production)

### API Keys Required

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic (optional)
ANTHROPIC_API_KEY=sk-ant-...

# Observability (optional)
JAEGER_ENDPOINT=http://localhost:14268
PROMETHEUS_ENDPOINT=http://localhost:9090
```

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/convergio/convergio.git
cd convergio
```

### 2. Setup Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
vim .env
```

Required environment variables:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=50

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/convergio
VECTOR_DB_URL=postgresql://user:pass@localhost:5432/convergio_vectors

# Model Configuration
DEFAULT_MODEL=gpt-4o-mini
FALLBACK_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-3-small

# Cost & Safety
DAILY_COST_LIMIT_USD=50.0
CONVERSATION_COST_LIMIT_USD=5.0
COST_SAFETY_ENABLED=true

# Feature Flags
RAG_ENABLED=true
STREAMING_ENABLED=true
SPEAKER_POLICY_ENABLED=true
GRAPHFLOW_ENABLED=true
HITL_ENABLED=false
OBSERVABILITY_ENABLED=true

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=convergio-autogen
```

### 4. Start Services

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start PostgreSQL with pgvector
docker run -d \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  ankane/pgvector:latest

# Initialize database
python scripts/init_db.py

# Start API server
python -m uvicorn backend.src.main:app --reload --port 8000
```

### 5. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Feature flags status
curl http://localhost:8000/api/v1/agents/feature-flags
```

## Docker Deployment

### 1. Build Images

```bash
# Build backend image
docker build -t convergio-backend:latest -f docker/Dockerfile.backend .

# Build frontend image (if applicable)
docker build -t convergio-frontend:latest -f docker/Dockerfile.frontend .
```

### 2. Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_DB: convergio
      POSTGRES_USER: convergio
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

  backend:
    image: convergio-backend:latest
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://convergio:${DB_PASSWORD}@postgres:5432/convergio
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14268:14268"
      - "4317:4317"

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  redis-data:
  postgres-data:
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Scale backend
docker-compose up -d --scale backend=3
```

## Kubernetes Deployment

### 1. Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: convergio
```

### 2. ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: convergio-config
  namespace: convergio
data:
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  DEFAULT_MODEL: "gpt-4o-mini"
  RAG_ENABLED: "true"
  STREAMING_ENABLED: "true"
```

### 3. Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: convergio-secrets
  namespace: convergio
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-..."
  DB_PASSWORD: "..."
  REDIS_PASSWORD: "..."
```

### 4. Deployment

```yaml
# deployment.yaml
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
        image: convergio-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: convergio-config
        - secretRef:
            name: convergio-secrets
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### 5. Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: convergio-backend
  namespace: convergio
spec:
  selector:
    app: convergio-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 6. Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: convergio-ingress
  namespace: convergio
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.convergio.com
    secretName: convergio-tls
  rules:
  - host: api.convergio.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: convergio-backend
            port:
              number: 80
```

### 7. Deploy to Kubernetes

```bash
# Apply configurations
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Check deployment status
kubectl get pods -n convergio
kubectl get svc -n convergio
kubectl get ingress -n convergio

# View logs
kubectl logs -f deployment/convergio-backend -n convergio

# Scale deployment
kubectl scale deployment convergio-backend --replicas=5 -n convergio
```

## Production Deployment

### 1. Infrastructure Setup

```terraform
# terraform/main.tf
provider "aws" {
  region = var.region
}

module "vpc" {
  source = "./modules/vpc"
  cidr_block = "10.0.0.0/16"
}

module "eks" {
  source = "./modules/eks"
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  node_groups = {
    main = {
      desired_capacity = 3
      max_capacity = 10
      min_capacity = 2
      instance_types = ["t3.large"]
    }
  }
}

module "rds" {
  source = "./modules/rds"
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  engine = "postgres"
  engine_version = "15.3"
  instance_class = "db.r6g.xlarge"
}

module "elasticache" {
  source = "./modules/elasticache"
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  node_type = "cache.r6g.large"
  num_cache_nodes = 3
}
```

### 2. CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - run: |
        pip install -r requirements.txt
        pytest tests/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: docker/setup-buildx-action@v2
    - uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    - uses: docker/build-push-action@v4
      with:
        push: true
        tags: ghcr.io/convergio/backend:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: azure/setup-kubectl@v3
    - run: |
        kubectl set image deployment/convergio-backend \
          backend=ghcr.io/convergio/backend:${{ github.sha }} \
          -n convergio
        kubectl rollout status deployment/convergio-backend -n convergio
```

### 3. Monitoring Setup

```yaml
# monitoring/prometheus-values.yaml
serverFiles:
  prometheus.yml:
    scrape_configs:
    - job_name: convergio
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - convergio
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
```

```yaml
# monitoring/grafana-dashboard.json
{
  "dashboard": {
    "title": "Convergio AutoGen Metrics",
    "panels": [
      {
        "title": "Conversations per Minute",
        "targets": [
          {
            "expr": "rate(convergio_conversations_total[1m])"
          }
        ]
      },
      {
        "title": "Agent Response Time P95",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(convergio_agent_response_time_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Daily Cost",
        "targets": [
          {
            "expr": "convergio_daily_cost_usd"
          }
        ]
      }
    ]
  }
}
```

### 4. Backup & Recovery

```bash
# Backup script
#!/bin/bash
# backup.sh

# Backup PostgreSQL
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Backup Redis
redis-cli --rdb backup_$(date +%Y%m%d).rdb

# Upload to S3
aws s3 cp backup_$(date +%Y%m%d).sql s3://convergio-backups/
aws s3 cp backup_$(date +%Y%m%d).rdb s3://convergio-backups/

# Cleanup old backups
find . -name "backup_*.sql" -mtime +30 -delete
find . -name "backup_*.rdb" -mtime +30 -delete
```

## Performance Tuning

### 1. Redis Optimization

```redis
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 2. PostgreSQL Tuning

```sql
-- postgresql.conf
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10485kB
min_wal_size = 1GB
max_wal_size = 4GB
```

### 3. Application Optimization

```python
# gunicorn.conf.py
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 5
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
```bash
# Check memory usage
kubectl top pods -n convergio

# Restart pod with memory issues
kubectl delete pod <pod-name> -n convergio
```

2. **Slow Response Times**
```bash
# Check Redis latency
redis-cli --latency

# Check PostgreSQL slow queries
psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

3. **Cost Overruns**
```bash
# Check daily cost
curl http://api.convergio.com/api/v1/agents/cost/summary

# Adjust limits
kubectl set env deployment/convergio-backend DAILY_COST_LIMIT_USD=25 -n convergio
```

## Security Hardening

### 1. Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: convergio-network-policy
  namespace: convergio
spec:
  podSelector:
    matchLabels:
      app: convergio-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
```

### 2. RBAC Configuration

```yaml
# rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: convergio-role
  namespace: convergio
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "update"]
```

### 3. Secrets Management

```bash
# Use Kubernetes secrets
kubectl create secret generic api-keys \
  --from-literal=openai-key=$OPENAI_API_KEY \
  --from-literal=anthropic-key=$ANTHROPIC_API_KEY \
  -n convergio

# Use HashiCorp Vault
vault kv put secret/convergio/api-keys \
  openai_key=$OPENAI_API_KEY \
  anthropic_key=$ANTHROPIC_API_KEY
```

## Maintenance

### Daily Tasks

```bash
# Check system health
curl http://api.convergio.com/health

# Review costs
curl http://api.convergio.com/api/v1/agents/cost/summary

# Check error logs
kubectl logs -f deployment/convergio-backend -n convergio | grep ERROR
```

### Weekly Tasks

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Clean old logs
find /var/log/convergio -name "*.log" -mtime +7 -delete

# Vacuum PostgreSQL
psql -c "VACUUM ANALYZE;"
```

### Monthly Tasks

```bash
# Security updates
apt-get update && apt-get upgrade

# Performance review
python scripts/performance_report.py

# Cost optimization review
python scripts/cost_analysis.py
```

## Support

For deployment support:
- Documentation: https://docs.convergio.com
- Issues: https://github.com/convergio/convergio/issues
- Email: support@convergio.com
- Slack: convergio.slack.com