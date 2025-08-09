# Convergio AutoGen Migration & Rollout Guide

## Overview

This guide provides comprehensive instructions for migrating from the legacy agent system to the new AutoGen-based architecture and managing the staged rollout process.

## Migration Timeline

### Phase 1: Development Environment (Week 1)
- Enable all features in dev
- Run comprehensive tests
- Gather performance metrics
- Fix identified issues

### Phase 2: Staging Environment (Week 2)
- Deploy with conservative feature flags
- Run load tests
- Validate integrations
- Monitor for 48 hours

### Phase 3: Production Canary (Week 3)
- 5% traffic rollout
- Monitor key metrics
- Gather user feedback
- Adjust configurations

### Phase 4: Production Rollout (Week 4)
- Gradual increase: 5% → 25% → 50% → 100%
- Monitor at each stage
- Ready for instant rollback

## Feature Flag Configuration

### Initial Rollout Configuration

```python
# config/feature_flags_prod.json
{
  "flags": {
    "rag_in_loop": {
      "enabled": true,
      "strategy": "percentage",
      "percentage": 5.0
    },
    "true_streaming": {
      "enabled": true,
      "strategy": "canary",
      "percentage": 5.0,
      "whitelist_groups": ["beta_testers"]
    },
    "speaker_policy": {
      "enabled": true,
      "strategy": "on"
    },
    "graphflow": {
      "enabled": true,
      "strategy": "group_based",
      "whitelist_groups": ["enterprise"]
    },
    "hitl": {
      "enabled": false,
      "strategy": "off"
    },
    "cost_safety": {
      "enabled": true,
      "strategy": "on"
    }
  }
}
```

### Progressive Rollout Schedule

| Week | RAG | Streaming | Speaker Policy | GraphFlow | HITL | Cost Safety |
|------|-----|-----------|----------------|-----------|------|-------------|
| 1    | 5%  | 5%        | 100%          | Enterprise| Off  | 100%        |
| 2    | 25% | 25%       | 100%          | Enterprise| Test | 100%        |
| 3    | 50% | 50%       | 100%          | 50%       | 10%  | 100%        |
| 4    | 100%| 100%      | 100%          | 100%      | 25%  | 100%        |

## Migration Steps

### Step 1: Pre-Migration Checks

```bash
# 1. Backup current system
./scripts/backup_production.sh

# 2. Verify dependencies
python scripts/check_dependencies.py

# 3. Run migration validator
python scripts/validate_migration.py

# Expected output:
# ✅ Database schema compatible
# ✅ Redis version compatible
# ✅ API keys configured
# ✅ Feature flags initialized
```

### Step 2: Database Migration

```sql
-- migrations/001_autogen_tables.sql

-- Add AutoGen-specific tables
CREATE TABLE IF NOT EXISTS agent_metadata (
    agent_id UUID PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    capabilities JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversation_turns (
    turn_id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    agent_name VARCHAR(255),
    cost_usd DECIMAL(10, 6),
    tokens INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workflow_executions (
    execution_id UUID PRIMARY KEY,
    workflow_id VARCHAR(255),
    status VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes
CREATE INDEX idx_conversation_turns_conversation_id ON conversation_turns(conversation_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
```

### Step 3: Configuration Updates

```yaml
# kubernetes/configmap-update.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: convergio-config
  namespace: convergio
data:
  # Legacy settings (keep for rollback)
  LEGACY_AGENT_ENABLED: "true"
  
  # AutoGen settings
  AUTOGEN_ENABLED: "true"
  AUTOGEN_MAX_TURNS: "10"
  AUTOGEN_TIMEOUT: "120"
  
  # Feature flags
  RAG_ENABLED: "true"
  STREAMING_ENABLED: "true"
  SPEAKER_POLICY_ENABLED: "true"
  GRAPHFLOW_ENABLED: "true"
  HITL_ENABLED: "false"
  COST_SAFETY_ENABLED: "true"
  
  # Rollout configuration
  ROLLOUT_STRATEGY: "canary"
  CANARY_PERCENTAGE: "5"
```

### Step 4: Deploy AutoGen Components

```bash
# 1. Deploy new services
kubectl apply -f kubernetes/autogen-deployment.yaml

# 2. Verify deployment
kubectl get pods -n convergio | grep autogen

# 3. Check health
curl http://api.convergio.com/health/autogen

# 4. Run smoke tests
python tests/smoke/test_autogen_basic.py
```

### Step 5: Traffic Routing

```yaml
# kubernetes/virtualservice.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: convergio-routing
  namespace: convergio
spec:
  hosts:
  - api.convergio.com
  http:
  - match:
    - headers:
        x-feature-autogen:
          exact: "true"
    route:
    - destination:
        host: convergio-autogen
        port:
          number: 8000
      weight: 100
  - route:
    - destination:
        host: convergio-legacy
        port:
          number: 8000
      weight: 95
    - destination:
        host: convergio-autogen
        port:
          number: 8000
      weight: 5  # 5% canary
```

## Monitoring During Migration

### Key Metrics to Track

```python
# monitoring/migration_metrics.py
MIGRATION_METRICS = {
    "latency": {
        "legacy_p95": "< 2s",
        "autogen_p95": "< 2s",
        "alert_threshold": "3s"
    },
    "error_rate": {
        "legacy": "< 0.1%",
        "autogen": "< 0.5%",  # Higher tolerance during migration
        "alert_threshold": "1%"
    },
    "cost_per_request": {
        "legacy": "< $0.01",
        "autogen": "< $0.02",  # May be higher initially
        "alert_threshold": "$0.05"
    },
    "success_rate": {
        "legacy": "> 99.9%",
        "autogen": "> 99%",
        "alert_threshold": "98%"
    }
}
```

### Monitoring Dashboard

```json
// grafana/migration-dashboard.json
{
  "dashboard": {
    "title": "AutoGen Migration Monitor",
    "panels": [
      {
        "title": "Traffic Distribution",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service=\"legacy\"}[5m]))",
            "legendFormat": "Legacy"
          },
          {
            "expr": "sum(rate(http_requests_total{service=\"autogen\"}[5m]))",
            "legendFormat": "AutoGen"
          }
        ]
      },
      {
        "title": "Comparative Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"legacy\"}[5m]))",
            "legendFormat": "Legacy P95"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"autogen\"}[5m]))",
            "legendFormat": "AutoGen P95"
          }
        ]
      },
      {
        "title": "Cost Comparison",
        "targets": [
          {
            "expr": "avg(convergio_cost_per_turn_usd{service=\"legacy\"})",
            "legendFormat": "Legacy Avg Cost"
          },
          {
            "expr": "avg(convergio_cost_per_turn_usd{service=\"autogen\"})",
            "legendFormat": "AutoGen Avg Cost"
          }
        ]
      }
    ]
  }
}
```

## Rollback Procedures

### Instant Rollback

```bash
#!/bin/bash
# scripts/rollback_autogen.sh

echo "🔄 Initiating AutoGen rollback..."

# 1. Disable feature flags
curl -X POST http://api.convergio.com/admin/feature-flags/disable-all \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 2. Route all traffic to legacy
kubectl patch virtualservice convergio-routing -n convergio \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/http/1/route/0/weight", "value":100}]'

# 3. Verify rollback
sleep 5
curl http://api.convergio.com/health | grep "legacy"

echo "✅ Rollback complete"
```

### Gradual Rollback

```python
# scripts/gradual_rollback.py
import time
import requests

def gradual_rollback(current_percentage: int, target: int = 0):
    """Gradually reduce AutoGen traffic"""
    
    while current_percentage > target:
        # Reduce by 5% every 5 minutes
        current_percentage = max(target, current_percentage - 5)
        
        response = requests.post(
            "http://api.convergio.com/admin/traffic/update",
            json={"autogen_percentage": current_percentage},
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        
        print(f"Traffic updated: AutoGen={current_percentage}%, Legacy={100-current_percentage}%")
        
        if current_percentage > target:
            time.sleep(300)  # Wait 5 minutes
    
    print("Rollback complete")

if __name__ == "__main__":
    gradual_rollback(current_percentage=25)
```

## Validation Tests

### Post-Migration Validation

```python
# tests/validate_migration.py
import asyncio
import pytest
from typing import List, Dict

class MigrationValidator:
    
    async def validate_all(self) -> Dict[str, bool]:
        """Run all validation checks"""
        results = {}
        
        # Check feature flags
        results["feature_flags"] = await self.validate_feature_flags()
        
        # Check agent availability
        results["agents"] = await self.validate_agents()
        
        # Check workflows
        results["workflows"] = await self.validate_workflows()
        
        # Check cost tracking
        results["cost_tracking"] = await self.validate_cost_tracking()
        
        # Check observability
        results["observability"] = await self.validate_observability()
        
        return results
    
    async def validate_feature_flags(self) -> bool:
        """Validate feature flags are correctly configured"""
        response = requests.get("http://api.convergio.com/api/v1/agents/feature-flags")
        flags = response.json()
        
        required_flags = [
            "rag_in_loop",
            "true_streaming",
            "speaker_policy",
            "cost_safety"
        ]
        
        for flag in required_flags:
            if flag not in flags or not flags[flag]["enabled"]:
                print(f"❌ Feature flag {flag} not properly configured")
                return False
        
        print("✅ All feature flags validated")
        return True
    
    async def validate_agents(self) -> bool:
        """Validate all agents are responsive"""
        response = requests.get("http://api.convergio.com/api/v1/agents/status")
        status = response.json()
        
        if status["total_agents"] < 8:
            print(f"❌ Only {status['total_agents']} agents available")
            return False
        
        print(f"✅ All {status['total_agents']} agents available")
        return True
    
    async def validate_workflows(self) -> bool:
        """Validate workflow execution"""
        response = requests.get("http://api.convergio.com/api/v1/workflows/catalog")
        workflows = response.json()
        
        required_workflows = [
            "strategic_analysis",
            "product_launch",
            "market_entry"
        ]
        
        available = [w["workflow_id"] for w in workflows]
        for workflow in required_workflows:
            if workflow not in available:
                print(f"❌ Workflow {workflow} not available")
                return False
        
        print("✅ All required workflows available")
        return True
    
    async def validate_cost_tracking(self) -> bool:
        """Validate cost tracking is operational"""
        response = requests.get("http://api.convergio.com/api/v1/agents/cost/summary")
        
        if response.status_code != 200:
            print("❌ Cost tracking not responding")
            return False
        
        summary = response.json()
        if "daily" not in summary:
            print("❌ Cost tracking data incomplete")
            return False
        
        print("✅ Cost tracking operational")
        return True
    
    async def validate_observability(self) -> bool:
        """Validate observability is collecting metrics"""
        response = requests.get("http://api.convergio.com/metrics")
        
        if response.status_code != 200:
            print("❌ Metrics endpoint not responding")
            return False
        
        metrics = response.text
        required_metrics = [
            "convergio_conversations_total",
            "convergio_agent_invocations_total",
            "convergio_cost_per_turn_usd"
        ]
        
        for metric in required_metrics:
            if metric not in metrics:
                print(f"❌ Metric {metric} not being collected")
                return False
        
        print("✅ All metrics being collected")
        return True
```

## Communication Plan

### Stakeholder Notifications

```markdown
# Email Template: Migration Start

Subject: Convergio AutoGen Migration - Phase 1 Beginning

Dear Team,

We are beginning the migration to our new AutoGen-based agent system. 

**What to Expect:**
- Initial rollout to 5% of traffic
- Possible minor latency variations
- New features gradually becoming available

**Timeline:**
- Week 1: 5% canary deployment
- Week 2: 25% if metrics are stable
- Week 3: 50% rollout
- Week 4: Full production

**Monitoring:**
- Dashboard: https://grafana.convergio.com/d/migration
- Status Page: https://status.convergio.com

**Support:**
- Slack: #autogen-migration
- On-call: autogen-oncall@convergio.com

Thank you for your patience during this upgrade.

Best regards,
Engineering Team
```

### User Communication

```markdown
# In-App Notification

🚀 **System Upgrade in Progress**

We're rolling out improvements to our AI agent system. You may experience:
- ✨ Faster response times
- 📊 Better context understanding
- 💬 More natural conversations

If you encounter any issues, please contact support.

[Learn More] [Dismiss]
```

## Success Criteria

### Migration Success Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Error Rate | < 0.5% | - | ⏳ |
| P95 Latency | < 2s | - | ⏳ |
| Cost per Request | < $0.02 | - | ⏳ |
| User Satisfaction | > 4.5/5 | - | ⏳ |
| Agent Availability | 100% | - | ⏳ |
| Feature Adoption | > 80% | - | ⏳ |

### Go/No-Go Decision Points

1. **After 5% Rollout (Day 2)**
   - Error rate < 1%
   - No critical bugs
   - Cost within 20% of projections

2. **After 25% Rollout (Week 2)**
   - User satisfaction maintained
   - Performance SLAs met
   - No security incidents

3. **After 50% Rollout (Week 3)**
   - All workflows functional
   - Cost optimizations effective
   - Positive user feedback

4. **Before 100% Rollout (Week 4)**
   - All success criteria met
   - Rollback tested successfully
   - Team confidence high

## Post-Migration Tasks

### Cleanup

```bash
# 1. Remove legacy code (after 30 days)
git branch legacy-backup
git rm -r legacy/

# 2. Remove legacy infrastructure
kubectl delete deployment convergio-legacy -n convergio

# 3. Archive legacy data
python scripts/archive_legacy_data.py

# 4. Update documentation
./scripts/update_docs.sh --remove-legacy
```

### Optimization

```python
# optimization/post_migration.py

async def optimize_autogen():
    """Post-migration optimizations"""
    
    # 1. Analyze usage patterns
    patterns = await analyze_usage_patterns()
    
    # 2. Optimize agent selection weights
    await optimize_selection_weights(patterns)
    
    # 3. Tune model selection
    await tune_model_selection(patterns)
    
    # 4. Adjust caching strategies
    await optimize_caching(patterns)
    
    print("✅ Post-migration optimizations complete")
```

## Support Resources

- **Documentation**: https://docs.convergio.com/autogen
- **Runbook**: https://wiki.convergio.com/autogen-runbook
- **Slack Channel**: #autogen-support
- **Emergency Hotline**: +1-xxx-xxx-xxxx

---

*Last Updated: January 2025*
*Version: 1.0.0*