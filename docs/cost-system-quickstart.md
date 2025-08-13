# 🚀 Cost Tracking System - Quick Start Guide

## 📋 Prerequisites

1. **PostgreSQL Database** - Running and accessible
2. **Redis** - For caching and real-time data
3. **Python Dependencies** - All requirements installed
4. **API Keys** - For pricing updates (optional)

## ⚡ Quick Setup (5 minutes)

### 1. Database Migration

```bash
# Apply the cost tracking tables
psql -h localhost -U convergio -d convergio -f migrations/create_cost_tracking_tables.sql
```

### 2. Start the Backend

```bash
# Make sure all services start
python -m src.main
```

### 3. Test the System

```bash
# Run the comprehensive test suite
python test_enhanced_cost_system.py
```

## 🎯 Immediate Usage

### Check System Status
```bash
curl http://localhost:9000/api/v1/cost-management/system/status
```

### Get Real-time Costs
```bash
curl http://localhost:9000/api/v1/cost-management/realtime/current
```

### Set Budget Limits
```bash
curl -X POST http://localhost:9000/api/v1/cost-management/budget/limits \
  -H "Content-Type: application/json" \
  -d '{
    "daily_limit": 50.0,
    "monthly_limit": 1500.0,
    "provider_limits": {
      "openai": 100.0,
      "anthropic": 100.0,
      "perplexity": 20.0
    }
  }'
```

## 🔧 Configuration

### Default Settings (Can be Changed)
- **Daily Budget**: $50.00
- **Monthly Budget**: $1500.00
- **Provider Limits**: OpenAI $100, Anthropic $100, Perplexity $20
- **Update Frequency**: Frontend 30s, Pricing 24h, Monitoring 5min

### Alert Thresholds
- **Healthy**: < 50% of budget
- **Moderate**: 50-74% of budget  
- **Warning**: 75-89% of budget
- **Critical**: 90-99% of budget
- **Exceeded**: ≥ 100% of budget

## 🚨 Emergency Procedures

### Circuit Breaker Override
```bash
curl -X POST http://localhost:9000/api/v1/cost-management/circuit-breaker/override \
  -H "Content-Type: application/json" \
  -d '{
    "override_code": "EMERGENCY_OVERRIDE",
    "duration_minutes": 60
  }'
```

### Resume Suspended Provider
```bash
curl -X POST http://localhost:9000/api/v1/cost-management/providers/openai/resume
```

### Manual System Check
```bash
curl -X POST http://localhost:9000/api/v1/cost-management/system/check
```

## 📊 Monitoring Dashboard

Access the admin dashboard for complete system overview:
```
GET /api/v1/cost-management/admin/dashboard
```

Returns comprehensive data including:
- Budget utilization across all time periods
- Circuit breaker status and suspended services
- Cost predictions and trend analysis
- Provider credit status
- System health indicators

## 🔍 Troubleshooting

### Common Issues

1. **Frontend shows $0.00**
   - Check backend is running on port 9000
   - Verify API endpoint responds: `curl localhost:9000/api/v1/cost-management/realtime/current`

2. **Database errors**
   - Ensure PostgreSQL is running
   - Verify migrations are applied
   - Check database connection in logs

3. **Circuit breaker stuck OPEN**
   - Check budget limits vs actual spend
   - Use emergency override if needed
   - Review suspension reasons in status

4. **Pricing not updating**
   - Check web search integration
   - Verify current date usage (August 2025)
   - Manual trigger: `POST /pricing/update`

### Log Analysis
```bash
# Check for errors
grep "❌" logs/convergio.log | tail -10

# Monitor budget alerts  
grep "🚨" logs/convergio.log | tail -5

# Circuit breaker activity
grep "🚦" logs/convergio.log | tail -5
```

## 🎯 Key URLs

- **Real-time Costs**: `/cost-management/realtime/current`
- **Budget Status**: `/cost-management/budget/status`
- **System Health**: `/cost-management/system/status`
- **Admin Dashboard**: `/cost-management/admin/dashboard`
- **Circuit Breaker**: `/cost-management/circuit-breaker/status`

## 📈 Success Indicators

✅ **System Working Correctly When:**
- Frontend shows live cost updates
- Budget utilization percentages are accurate
- Alerts trigger at correct thresholds
- Circuit breaker activates when limits exceeded
- Pricing updates automatically with current dates
- All background services show "healthy" status

## 🚀 Next Steps

1. **Customize Budget Limits** - Set appropriate limits for your usage
2. **Configure Alerts** - Set up notification channels for critical alerts
3. **Monitor Usage Patterns** - Use analytics to optimize costs
4. **Set up Dashboards** - Create custom views for your team
5. **Test Emergency Procedures** - Ensure override codes work

---

**Need Help?** Check the full documentation: `/docs/cost-tracking-system.md`

**Emergency Contact**: Use override codes for immediate budget limit bypass