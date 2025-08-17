# 🔧 Convergio Troubleshooting Guide

*Comprehensive troubleshooting guide for resolving Convergio platform issues*

## Table of Contents

1. [Quick Diagnostic Commands](#quick-diagnostic-commands)
2. [Common Issues & Solutions](#common-issues--solutions)
3. [System Health Checks](#system-health-checks)
4. [Agent Issues](#agent-issues)
5. [Performance Problems](#performance-problems)
6. [Database Issues](#database-issues)
7. [Network & Connectivity](#network--connectivity)
8. [Security Issues](#security-issues)
9. [Error Codes Reference](#error-codes-reference)
10. [Emergency Procedures](#emergency-procedures)

## Quick Diagnostic Commands

### System Status Check
```bash
# Quick system overview
./scripts/health_check.sh

# Detailed status
curl -s http://localhost:8000/health | jq '.'

# Service status
systemctl status convergio
systemctl status postgresql
systemctl status redis

# Resource usage
top -b -n 1 | head -20
df -h
free -h
```

### Log Analysis
```bash
# Recent errors
tail -100 /var/log/convergio/app.log | grep -i error

# Application logs
journalctl -u convergio -f --since "10 minutes ago"

# Database logs
tail -50 /var/log/postgresql/postgresql-*.log

# Redis logs
tail -50 /var/log/redis/redis-server.log
```

### Quick Fixes
```bash
# Restart services
sudo systemctl restart convergio
sudo systemctl restart redis
sudo systemctl restart postgresql

# Clear cache
redis-cli flushdb

# Reset connections
sudo systemctl reload nginx
```

## Common Issues & Solutions

### Issue: Platform Not Loading

**Symptoms:**
- Website not accessible
- "Connection refused" errors
- Blank pages or infinite loading

**Diagnosis:**
```bash
# Check if services are running
systemctl status convergio
systemctl status nginx

# Check ports
netstat -tlnp | grep :8000
netstat -tlnp | grep :4000

# Check logs
journalctl -u convergio --since "5 minutes ago"
tail -50 /var/log/nginx/error.log
```

**Solutions:**

1. **Service Not Running**
   ```bash
   # Start the service
   sudo systemctl start convergio
   sudo systemctl start nginx
   
   # Enable auto-start
   sudo systemctl enable convergio
   ```

2. **Port Conflicts**
   ```bash
   # Find process using port
   lsof -i :8000
   
   # Kill conflicting process
   kill -9 <PID>
   
   # Or change port in configuration
   export PORT=8001
   ```

3. **Configuration Issues**
   ```bash
   # Validate configuration
   python -c "from core.config import get_settings; print(get_settings())"
   
   # Check environment variables
   env | grep CONVERGIO
   ```

### Issue: Slow Performance

**Symptoms:**
- Long response times (>10 seconds)
- Timeouts
- UI lag and delays

**Diagnosis:**
```bash
# Check system resources
htop
iostat -x 1 5

# Database performance
psql -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Redis performance
redis-cli info memory
redis-cli slowlog get 10

# Application metrics
curl -s http://localhost:8000/metrics | grep response_time
```

**Solutions:**

1. **High CPU Usage**
   ```bash
   # Find CPU-intensive processes
   top -o %CPU
   
   # Restart high-usage services
   sudo systemctl restart convergio
   ```

2. **Memory Issues**
   ```bash
   # Check memory usage
   free -h
   
   # Clear system cache
   echo 3 | sudo tee /proc/sys/vm/drop_caches
   
   # Restart Redis if memory usage is high
   sudo systemctl restart redis
   ```

3. **Database Slow Queries**
   ```sql
   -- Kill long-running queries
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE state = 'active' 
   AND query_start < now() - interval '5 minutes';
   
   -- Analyze slow queries
   SELECT query, mean_time 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC LIMIT 5;
   ```

### Issue: Agent Not Responding

**Symptoms:**
- Agent conversations failing
- "Agent unavailable" errors
- Blank responses

**Diagnosis:**
```bash
# Check agent health
python scripts/check_agent_health.py

# Test individual agent
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "ali_chief_of_staff", "message": "test"}'

# Check API keys
python scripts/validate_api_keys.py

# Check rate limits
curl -I https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Solutions:**

1. **API Key Issues**
   ```bash
   # Validate API keys
   export OPENAI_API_KEY="your_new_key"
   
   # Test API connectivity
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

2. **Rate Limiting**
   ```bash
   # Check rate limit status
   python scripts/check_rate_limits.py
   
   # Wait and retry
   sleep 60
   ```

3. **Agent Configuration**
   ```bash
   # Reload agent configurations
   python scripts/reload_agents.py
   
   # Validate agent definitions
   python scripts/validate_agent_configs.py
   ```

### Issue: Database Connection Errors

**Symptoms:**
- "Database connection failed"
- "Too many connections"
- Data not saving

**Diagnosis:**
```sql
-- Check connection count
SELECT count(*) FROM pg_stat_activity;

-- Check connection limit
SELECT setting FROM pg_settings WHERE name = 'max_connections';

-- Active connections by state
SELECT state, count(*) 
FROM pg_stat_activity 
GROUP BY state;

-- Blocking queries
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_locks blocking_locks 
  ON blocking_locks.locktype = blocked_locks.locktype;
```

**Solutions:**

1. **Too Many Connections**
   ```sql
   -- Kill idle connections
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE state = 'idle' 
   AND query_start < now() - interval '1 hour';
   
   -- Increase connection limit (restart required)
   -- Edit postgresql.conf: max_connections = 200
   ```

2. **Connection Pool Issues**
   ```python
   # Restart application with fresh pool
   sudo systemctl restart convergio
   
   # Check pool configuration
   grep -r "pool_size" /etc/convergio/
   ```

3. **Database Locked**
   ```sql
   -- Find and kill blocking queries
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE pid IN (
     SELECT blocking_locks.pid 
     FROM pg_catalog.pg_locks blocking_locks
   );
   ```

## System Health Checks

### Automated Health Check Script

```bash
#!/bin/bash
# Comprehensive health check

echo "=== Convergio Health Check ==="
echo "Timestamp: $(date)"
echo

# Service status
echo "=== Service Status ==="
systemctl is-active convergio && echo "✓ Convergio: Running" || echo "✗ Convergio: Stopped"
systemctl is-active postgresql && echo "✓ PostgreSQL: Running" || echo "✗ PostgreSQL: Stopped"
systemctl is-active redis && echo "✓ Redis: Running" || echo "✗ Redis: Stopped"
systemctl is-active nginx && echo "✓ Nginx: Running" || echo "✗ Nginx: Stopped"
echo

# Port connectivity
echo "=== Port Connectivity ==="
nc -z localhost 8000 && echo "✓ Backend API: Accessible" || echo "✗ Backend API: Not accessible"
nc -z localhost 5432 && echo "✓ PostgreSQL: Accessible" || echo "✗ PostgreSQL: Not accessible"
nc -z localhost 6379 && echo "✓ Redis: Accessible" || echo "✗ Redis: Not accessible"
echo

# Resource usage
echo "=== Resource Usage ==="
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{print $5}')"
echo

# Database health
echo "=== Database Health ==="
DB_CONNECTIONS=$(psql -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null)
echo "Active DB Connections: ${DB_CONNECTIONS:-'ERROR'}"

# Redis health
echo "=== Redis Health ==="
REDIS_MEMORY=$(redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
echo "Redis Memory Usage: ${REDIS_MEMORY:-'ERROR'}"

# API health
echo "=== API Health ==="
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$API_STATUS" = "200" ]; then
    echo "✓ API Health: OK"
else
    echo "✗ API Health: ERROR (Status: $API_STATUS)"
fi

echo
echo "=== Health Check Complete ==="
```

### Performance Monitoring

```bash
#!/bin/bash
# Performance monitoring script

echo "=== Performance Metrics ==="

# Response time test
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/health)
echo "API Response Time: ${RESPONSE_TIME}s"

# Database performance
echo "=== Database Performance ==="
psql -c "
SELECT 
    'Query Performance' as metric,
    ROUND(AVG(mean_time)::numeric, 2) as avg_response_ms
FROM pg_stat_statements 
WHERE calls > 10;
"

# Cache hit ratio
echo "=== Cache Performance ==="
redis-cli info stats | grep keyspace_hits
redis-cli info stats | grep keyspace_misses

# Active processes
echo "=== Active Processes ==="
ps aux | grep convergio | grep -v grep | wc -l | xargs echo "Convergio Processes:"
```

## Agent Issues

### Agent Health Diagnostics

```python
#!/usr/bin/env python3
# Agent health check script

import asyncio
import aiohttp
import json
from datetime import datetime

async def check_agent_health():
    agents = [
        "ali_chief_of_staff",
        "antonio_strategy_expert", 
        "ava_analytics_virtuoso",
        "amy_cfo",
        "dan_engineering_gm"
    ]
    
    print(f"Agent Health Check - {datetime.now()}")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        for agent_id in agents:
            try:
                payload = {
                    "agent_id": agent_id,
                    "message": "Health check test",
                    "context": {"test": True}
                }
                
                start_time = datetime.now()
                async with session.post(
                    "http://localhost:8000/api/v1/agents/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()
                    
                    if response.status == 200:
                        print(f"✓ {agent_id}: OK ({response_time:.2f}s)")
                    else:
                        print(f"✗ {agent_id}: HTTP {response.status}")
                        
            except asyncio.TimeoutError:
                print(f"✗ {agent_id}: TIMEOUT")
            except Exception as e:
                print(f"✗ {agent_id}: ERROR - {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_agent_health())
```

### Agent Configuration Validation

```python
#!/usr/bin/env python3
# Validate agent configurations

import yaml
import json
import os
from pathlib import Path

def validate_agent_configs():
    agent_dir = Path("/app/backend/src/agents/definitions")
    errors = []
    
    for agent_file in agent_dir.glob("*.md"):
        try:
            with open(agent_file, 'r') as f:
                content = f.read()
                
            # Extract YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    yaml_content = parts[1]
                    try:
                        config = yaml.safe_load(yaml_content)
                        
                        # Validate required fields
                        required = ['name', 'description', 'tools']
                        for field in required:
                            if field not in config:
                                errors.append(f"{agent_file.name}: Missing {field}")
                                
                        # Validate tools format
                        if 'tools' in config and not isinstance(config['tools'], list):
                            errors.append(f"{agent_file.name}: Tools must be a list")
                            
                    except yaml.YAMLError as e:
                        errors.append(f"{agent_file.name}: Invalid YAML - {e}")
                else:
                    errors.append(f"{agent_file.name}: Invalid frontmatter format")
            else:
                errors.append(f"{agent_file.name}: Missing frontmatter")
                
        except Exception as e:
            errors.append(f"{agent_file.name}: Read error - {e}")
    
    if errors:
        print("Agent Configuration Errors:")
        for error in errors:
            print(f"  ✗ {error}")
        return False
    else:
        print("✓ All agent configurations valid")
        return True

if __name__ == "__main__":
    validate_agent_configs()
```

### Agent Response Testing

```bash
#!/bin/bash
# Test agent responses

echo "=== Agent Response Testing ==="

# Test Ali (Chief of Staff)
echo "Testing Ali..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "ali_chief_of_staff", "message": "Hello, please provide a brief status update."}')

if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "✓ Ali: Responding correctly"
else
    echo "✗ Ali: Response error"
    echo "$RESPONSE" | jq '.error // .'
fi

# Test Antonio (Strategy)
echo "Testing Antonio..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "antonio_strategy_expert", "message": "Provide a brief strategic insight."}')

if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "✓ Antonio: Responding correctly"
else
    echo "✗ Antonio: Response error"
    echo "$RESPONSE" | jq '.error // .'
fi

echo "=== Agent Testing Complete ==="
```

## Performance Problems

### Memory Issues

**Diagnosis:**
```bash
# Check memory usage by process
ps aux --sort=-%mem | head -10

# Check memory details
cat /proc/meminfo

# Check for memory leaks
valgrind --tool=memcheck --leak-check=full python -m uvicorn src.main:app
```

**Solutions:**

1. **High Memory Usage**
   ```bash
   # Restart application
   sudo systemctl restart convergio
   
   # Clear system cache
   sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
   
   # Check for memory leaks in logs
   grep -i "memory\|leak\|oom" /var/log/convergio/app.log
   ```

2. **Out of Memory Errors**
   ```bash
   # Check kernel messages
   dmesg | grep -i "killed process"
   
   # Increase swap space
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### CPU Issues

**Diagnosis:**
```bash
# Real-time CPU monitoring
htop

# CPU usage by process
ps aux --sort=-%cpu | head -10

# Check for high load
uptime
```

**Solutions:**

1. **High CPU Usage**
   ```bash
   # Identify CPU-intensive processes
   top -o %CPU
   
   # Check for infinite loops in logs
   grep -i "loop\|recursive\|infinite" /var/log/convergio/app.log
   
   # Restart if necessary
   sudo systemctl restart convergio
   ```

### Network Issues

**Diagnosis:**
```bash
# Network connectivity
ping -c 4 google.com

# DNS resolution
nslookup api.openai.com

# Port accessibility
telnet api.openai.com 443

# Network interface status
ip addr show
```

**Solutions:**

1. **DNS Issues**
   ```bash
   # Flush DNS cache
   sudo systemctl restart systemd-resolved
   
   # Check DNS configuration
   cat /etc/resolv.conf
   
   # Use alternative DNS
   echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
   ```

2. **Firewall Issues**
   ```bash
   # Check firewall status
   sudo ufw status
   
   # Allow necessary ports
   sudo ufw allow 8000
   sudo ufw allow 443
   sudo ufw allow 80
   ```

## Database Issues

### Connection Pool Exhaustion

**Diagnosis:**
```sql
-- Check active connections
SELECT count(*) as active_connections, state
FROM pg_stat_activity 
GROUP BY state;

-- Check connection limits
SELECT setting FROM pg_settings WHERE name = 'max_connections';

-- Long-running queries
SELECT pid, state, query_start, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
AND query_start < now() - interval '5 minutes';
```

**Solutions:**

1. **Kill Long-Running Queries**
   ```sql
   -- Terminate specific query
   SELECT pg_terminate_backend(12345);
   
   -- Kill all long-running queries
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE state = 'active' 
   AND query_start < now() - interval '10 minutes';
   ```

2. **Increase Connection Limits**
   ```bash
   # Edit PostgreSQL configuration
   sudo nano /etc/postgresql/14/main/postgresql.conf
   
   # Increase max_connections
   max_connections = 200
   
   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

### Slow Queries

**Diagnosis:**
```sql
-- Enable query statistics
SELECT * FROM pg_stat_statements_reset();

-- Find slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public';
```

**Solutions:**

1. **Create Missing Indexes**
   ```sql
   -- Common indexes for Convergio
   CREATE INDEX CONCURRENTLY idx_conversations_user_created 
   ON conversations(user_id, created_at);
   
   CREATE INDEX CONCURRENTLY idx_agent_interactions_timestamp 
   ON agent_interactions(timestamp DESC);
   
   CREATE INDEX CONCURRENTLY idx_users_email 
   ON users(email) WHERE status = 'active';
   ```

2. **Query Optimization**
   ```sql
   -- Analyze table statistics
   ANALYZE conversations;
   ANALYZE agent_interactions;
   
   -- Vacuum to reclaim space
   VACUUM ANALYZE conversations;
   ```

## Network & Connectivity

### API Connectivity Issues

**Diagnosis:**
```bash
# Test API endpoints
curl -v http://localhost:8000/health
curl -v http://localhost:8000/api/v1/agents

# Check SSL certificates
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Network route tracing
traceroute api.openai.com
```

**Solutions:**

1. **SSL Certificate Issues**
   ```bash
   # Renew certificates
   sudo certbot renew
   
   # Check certificate validity
   openssl x509 -in /etc/ssl/certs/yourdomain.com.crt -text -noout
   
   # Restart web server
   sudo systemctl restart nginx
   ```

2. **Proxy Issues**
   ```bash
   # Check proxy settings
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   
   # Bypass proxy for testing
   unset HTTP_PROXY HTTPS_PROXY
   ```

### Load Balancer Issues

**Diagnosis:**
```bash
# Check backend servers
curl -H "Host: yourdomain.com" http://backend1:8000/health
curl -H "Host: yourdomain.com" http://backend2:8000/health

# Check load balancer logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

**Solutions:**

1. **Backend Server Issues**
   ```bash
   # Check individual servers
   ssh backend1 "systemctl status convergio"
   ssh backend2 "systemctl status convergio"
   
   # Remove problematic server from rotation
   # Edit nginx configuration to remove server
   ```

## Security Issues

### Authentication Problems

**Diagnosis:**
```bash
# Check authentication logs
grep -i "auth\|login\|fail" /var/log/convergio/app.log

# Check failed login attempts
grep -i "failed.*login" /var/log/auth.log

# Check JWT token validation
python scripts/validate_jwt_tokens.py
```

**Solutions:**

1. **JWT Token Issues**
   ```bash
   # Regenerate JWT secret
   openssl rand -hex 32 > /etc/convergio/jwt_secret
   
   # Restart application
   sudo systemctl restart convergio
   ```

2. **Session Issues**
   ```bash
   # Clear Redis sessions
   redis-cli flushdb
   
   # Check session configuration
   grep -i session /etc/convergio/config.yaml
   ```

### Security Threats

**Diagnosis:**
```bash
# Check for suspicious activity
grep -i "injection\|attack\|breach" /var/log/convergio/app.log

# Check access logs for unusual patterns
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -10

# Check for brute force attempts
grep "Failed password" /var/log/auth.log | wc -l
```

**Solutions:**

1. **Block Suspicious IPs**
   ```bash
   # Block IP with iptables
   sudo iptables -A INPUT -s SUSPICIOUS_IP -j DROP
   
   # Block IP with fail2ban
   sudo fail2ban-client set convergio banip SUSPICIOUS_IP
   ```

2. **Enhanced Monitoring**
   ```bash
   # Enable additional logging
   echo "security.log_level = DEBUG" >> /etc/convergio/config.yaml
   
   # Monitor in real-time
   tail -f /var/log/convergio/security.log | grep -i alert
   ```

## Error Codes Reference

### HTTP Status Codes

| Code | Meaning | Common Causes | Solutions |
|------|---------|---------------|-----------|
| 400 | Bad Request | Invalid input data | Validate request format |
| 401 | Unauthorized | Missing/invalid auth | Check API keys |
| 403 | Forbidden | Insufficient permissions | Review user roles |
| 404 | Not Found | Invalid endpoint/resource | Check URL paths |
| 422 | Validation Error | Data validation failed | Fix input data |
| 429 | Rate Limited | Too many requests | Implement backoff |
| 500 | Internal Error | Server-side issue | Check logs |
| 502 | Bad Gateway | Upstream server issue | Check backend |
| 503 | Service Unavailable | System overloaded | Scale resources |

### Application Error Codes

| Code | Description | Troubleshooting |
|------|-------------|----------------|
| AGENT_UNAVAILABLE | Agent not responding | Check agent health, API keys |
| COST_LIMIT_EXCEEDED | Budget threshold reached | Review cost settings |
| RATE_LIMIT_EXCEEDED | Too many requests | Implement request throttling |
| DATABASE_CONNECTION_FAILED | DB connectivity issue | Check database status |
| INVALID_AGENT_CONFIG | Agent configuration error | Validate agent definitions |
| AUTHENTICATION_FAILED | Auth validation failed | Check credentials |
| VECTOR_SEARCH_FAILED | Search service issue | Check vector database |
| WORKFLOW_EXECUTION_FAILED | Workflow error | Review workflow definition |

## Emergency Procedures

### System Down

**Immediate Actions:**
1. **Check Basic Services**
   ```bash
   sudo systemctl status convergio postgresql redis nginx
   ```

2. **Restart All Services**
   ```bash
   sudo systemctl restart convergio
   sudo systemctl restart postgresql  
   sudo systemctl restart redis
   sudo systemctl restart nginx
   ```

3. **Check Logs for Errors**
   ```bash
   journalctl -u convergio --since "10 minutes ago" -p err
   ```

### Data Corruption

**Immediate Actions:**
1. **Stop All Services**
   ```bash
   sudo systemctl stop convergio
   ```

2. **Backup Current State**
   ```bash
   pg_dump convergio > /tmp/emergency_backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Restore from Last Known Good Backup**
   ```bash
   psql convergio < /backups/convergio_last_good.sql
   ```

### Security Breach

**Immediate Actions:**
1. **Isolate System**
   ```bash
   # Block all external traffic
   sudo ufw --force reset
   sudo ufw default deny incoming
   sudo ufw default deny outgoing
   ```

2. **Collect Evidence**
   ```bash
   # Preserve logs
   cp -r /var/log/convergio /tmp/incident_logs_$(date +%Y%m%d_%H%M%S)
   
   # Capture system state
   ps aux > /tmp/processes_$(date +%Y%m%d_%H%M%S).txt
   netstat -tuln > /tmp/network_$(date +%Y%m%d_%H%M%S).txt
   ```

3. **Notify Stakeholders**
   ```bash
   # Send incident notification
   python scripts/incident_notification.py --severity critical --type security_breach
   ```

### Recovery Verification

**Post-Recovery Checklist:**
```bash
#!/bin/bash
# Recovery verification script

echo "=== Recovery Verification ==="

# Service status
systemctl is-active convergio && echo "✓ Convergio running" || echo "✗ Convergio stopped"

# Database connectivity
psql -c "SELECT 1;" > /dev/null 2>&1 && echo "✓ Database connected" || echo "✗ Database error"

# API functionality
curl -f http://localhost:8000/health > /dev/null 2>&1 && echo "✓ API responding" || echo "✗ API error"

# Agent health
python scripts/test_agent_health.py && echo "✓ Agents healthy" || echo "✗ Agent issues"

# Data integrity
python scripts/verify_data_integrity.py && echo "✓ Data integrity OK" || echo "✗ Data corruption"

echo "=== Recovery Verification Complete ==="
```

---

*For additional support during critical incidents, contact the emergency response team or escalate to senior technical staff.*

*Last updated: August 2025 - Convergio FASE 11 Troubleshooting Guide*