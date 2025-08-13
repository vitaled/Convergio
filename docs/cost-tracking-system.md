# 💰 Enhanced Cost Tracking System

## Panoramica

Il **Sistema di Tracciamento Costi Potenziato** è una soluzione completa per il monitoraggio, controllo e gestione intelligente dei costi API per tutti i modelli AI utilizzati nella piattaforma Convergio.

Questo sistema implementa funzionalità avanzate di budget management, circuit breaker automatico, aggiornamenti prezzi in tempo reale, e protezione contro il superamento dei limiti di spesa.

## 🚀 Caratteristiche Principali

### 1. **Tracciamento Costi Real-time**
- **Persistenza Database**: Tutti i costi vengono salvati in PostgreSQL con precisione decimale
- **Tracciamento Granulare**: Monitoraggio per sessione, conversazione, agente e modello
- **Metriche Avanzate**: Token usage, tempo di risposta, breakdown per provider
- **Aggiornamento Frontend**: Polling automatico ogni 30 secondi per dati real-time

### 2. **Aggiornamento Automatico Prezzi** 🔄
- **Ricerca Web Automatica**: Sistema che usa Perplexity per trovare prezzi aggiornati
- **Data Corrente**: Usa sempre la data odierna (Agosto 2025) nelle ricerche
- **Multi-Provider**: Supporta OpenAI, Anthropic, Perplexity e altri
- **Schedulazione**: Aggiornamenti automatici ogni 24 ore alle 6:00 UTC

### 3. **Monitoraggio Limiti Crediti** 🚨
- **Credit Tracking**: Monitoraggio crediti per ogni provider
- **Rilevamento Esaurimento**: Alert quando i crediti stanno per finire
- **Previsioni**: Stima giorni rimanenti prima dell'esaurimento
- **Soglie Configurabili**: Warning a 70%, Critical a 85%, Exhausted a 95%

### 4. **Sistema Budget Intelligente** 📊
- **Limiti Configurabili**: Budget giornalieri, mensili e per provider
- **Soglie Multiple**: Healthy < 50%, Moderate < 75%, Warning < 90%, Critical > 90%
- **Previsioni Spesa**: Algoritmo di trend analysis per predire costi futuri
- **Budget Breakdown**: Analisi dettagliata per provider, modello, agente e ora

### 5. **Circuit Breaker Automatico** 🚦
- **Protezione Automatica**: Sospende chiamate API al raggiungimento dei limiti
- **Stati Intelligenti**: CLOSED (normale), OPEN (bloccato), HALF-OPEN (test)
- **Granularità**: Sospensione per provider specifici o agenti individuali
- **Override Emergency**: Codici di override per situazioni critiche

### 6. **Dashboard e Monitoring** 🔧
- **Admin Dashboard**: Vista completa dello stato del sistema
- **Health Monitoring**: Controllo continuo dello stato dei servizi
- **Alert System**: Notifiche intelligenti per situazioni anomale
- **Background Services**: Monitoraggio automatico 24/7

## 🏗 Architettura del Sistema

### Backend Components

```
src/services/
├── cost_tracking_service.py      # Tracciamento core con database
├── budget_monitor_service.py     # Monitoraggio budget e limiti
├── circuit_breaker_service.py    # Circuit breaker e protezione
├── pricing_updater_service.py    # Aggiornamento prezzi automatico
└── cost_background_tasks.py      # Orchestrazione servizi background
```

### Database Schema

```
Database Tables:
├── cost_tracking              # Ogni chiamata API
├── cost_sessions              # Aggregazione per sessione
├── daily_cost_summary         # Riassunto giornaliero
├── provider_pricing           # Prezzi attuali e storici
└── cost_alerts               # Alert e notifiche
```

### API Endpoints

```
Cost Management API (/api/v1/cost-management/):

Real-time Tracking:
├── GET  /realtime/current         # Costi real-time
├── POST /interactions             # Registra costo chiamata API
├── GET  /sessions/{id}            # Dettagli sessione
└── GET  /agents/{id}/costs        # Costi per agente

Budget Management:
├── GET  /budget/status            # Stato completo budget
├── GET  /budget/summary           # Riassunto budget
├── POST /budget/limits            # Imposta limiti budget
└── GET  /budget/circuit-breaker   # Stato circuit breaker

Pricing Management:
├── GET  /pricing/current          # Prezzi attuali
├── POST /pricing/update           # Aggiorna prezzi
└── GET  /pricing/comparison       # Confronto prezzi storici

System Administration:
├── GET  /admin/dashboard          # Dashboard admin completa
├── GET  /system/status            # Stato servizi background
├── POST /system/check             # Check manuale sistema
├── GET  /circuit-breaker/status   # Dettagli circuit breaker
├── POST /circuit-breaker/override # Override emergenza
├── POST /providers/{id}/resume    # Riattiva provider sospeso
└── POST /agents/{id}/resume       # Riattiva agente sospeso
```

## 🔧 Configurazione e Setup

### 1. Database Setup

Esegui le migrazioni per creare le tabelle:

```bash
# Applica le migrazioni
psql -h localhost -U convergio -d convergio -f migrations/create_cost_tracking_tables.sql
```

### 2. Configurazione Limiti

```python
# Imposta limiti budget via API
POST /cost-management/budget/limits
{
    "daily_limit": 50.0,
    "monthly_limit": 1500.0,
    "provider_limits": {
        "openai": 100.0,
        "anthropic": 100.0,
        "perplexity": 20.0
    }
}
```

### 3. Avvio Servizi Background

I servizi si avviano automaticamente con l'applicazione:

```python
# In src/main.py
from src.services.cost_background_tasks import start_cost_services

@app.on_event("startup")
async def startup():
    await start_cost_services()
```

## 📊 Utilizzo del Sistema

### Tracciamento Automatico

Il sistema traccia automaticamente ogni chiamata API:

```python
# Esempio di utilizzo nel codice agenti
from src.services.cost_tracking_service import EnhancedCostTracker

tracker = EnhancedCostTracker()
result = await tracker.track_api_call(
    session_id="session_123",
    conversation_id="conv_456", 
    provider="openai",
    model="gpt-4o",
    input_tokens=1000,
    output_tokens=500,
    agent_id="ali-chief-of-staff"
)
```

### Monitoraggio Budget

```python
# Controllo stato budget
from src.services.budget_monitor_service import budget_monitor

status = await budget_monitor.check_all_limits()
print(f"Budget Status: {status['daily_status']['status']}")
print(f"Utilization: {status['daily_status']['utilization_percent']}%")
```

### Circuit Breaker

```python
# Controllo prima delle chiamate API  
from src.services.circuit_breaker_service import circuit_breaker

should_block, reason = await circuit_breaker.check_should_block_request(
    provider="openai",
    agent_id="test-agent"
)

if should_block:
    print(f"Request blocked: {reason['message']}")
```

## 🔍 Monitoraggio e Alerting

### Tipi di Alert

1. **Budget Alerts**
   - Daily limit warning (75%)
   - Daily limit critical (95%)
   - Monthly limit critical (90%)

2. **Provider Alerts**
   - Credit warning (85%)
   - Credit exhausted (95%)

3. **System Alerts**
   - Cost spikes (singola chiamata > $1)
   - Session anomalies (costo > 3x media)
   - Circuit breaker activation

### Dashboard Metrics

Il dashboard admin mostra:

```json
{
    "system_health": {
        "overall_status": "healthy|moderate|warning|critical",
        "critical_issues": 0,
        "daily_utilization": 45.2,
        "monthly_utilization": 67.8
    },
    "budget_monitoring": {
        "daily_status": {...},
        "monthly_status": {...}, 
        "provider_status": {...},
        "predictions": {...}
    },
    "circuit_breaker": {
        "circuit_state": "CLOSED",
        "suspended_providers": [],
        "suspended_agents": []
    }
}
```

## 📈 Previsioni e Analytics

### Algoritmo di Previsione

Il sistema usa analisi di trend lineare sui dati degli ultimi 7 giorni:

```python
# Calcolo trend e previsioni
slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
tomorrow_prediction = intercept + slope * n
week_prediction = sum(intercept + slope * (n + i) for i in range(1, 8))
```

### Metriche Disponibili

- **Costo medio per interazione**
- **Trend di crescita/decrescita**
- **Previsione spesa prossimi 7/30 giorni**
- **Giorni rimanenti prima esaurimento budget**
- **Breakdown per ora del giorno**
- **Top consumer per agente/modello**

## 🚨 Gestione Emergenze

### Override Codes

Per situazioni di emergenza, usa i codici override:

```bash
# Codici validi per override emergency
- EMERGENCY_OVERRIDE
- BUDGET_OVERRIDE  
- ADMIN_OVERRIDE

# Attivazione via API
POST /cost-management/circuit-breaker/override
{
    "override_code": "EMERGENCY_OVERRIDE",
    "duration_minutes": 60
}
```

### Recovery Procedures

1. **Circuit Breaker Aperto**:
   - Verifica cause nel dashboard admin
   - Aumenta limiti se necessario
   - Usa override se urgente
   - Monitora recovery automatico

2. **Provider Sospeso**:
   - Controlla crediti rimanenti
   - Riattiva manualmente se risolto
   - Considera provider alternativi

3. **Budget Exceeded**:
   - Analizza cause nel breakdown
   - Valuta aumento limiti
   - Identifica agenti/modelli costosi

## 🧪 Testing

Il sistema include test completi:

```bash
# Esegui test suite completa
python test_enhanced_cost_system.py

# Test specifici
python test_cost_tracking.py
python validate_cost_system.py
```

## 📝 Prezzi Supportati (Agosto 2025)

### OpenAI
- **GPT-4o**: $2.50/$10.00 per million tokens (input/output)
- **GPT-4o-mini**: $0.15/$0.60 per million tokens
- **GPT-4-turbo**: $10.00/$30.00 per million tokens (legacy)

### Anthropic  
- **Claude 4 Sonnet**: $3.00/$15.00 per million tokens
- **Claude 3.5 Haiku**: $0.80/$4.00 per million tokens

### Perplexity
- **Sonar**: $1.00/$1.00 + $5.00 per 1000 searches
- **Sonar Pro**: $3.00/$15.00 + $10.00 per 1000 searches

## 🔐 Sicurezza

- **Input Validation**: Tutti gli input sono validati e sanitizzati
- **Rate Limiting**: Protection contro abuse delle API
- **Access Control**: Solo endpoint autorizzati per operazioni critiche
- **Audit Trail**: Logging completo di tutte le operazioni
- **Circuit Protection**: Prevenzione automatica overspend

## 🚀 Performance

- **Database Indexes**: Ottimizzazione query con indici appropriati
- **Caching**: Redis cache per dati frequentemente acceduti
- **Async Operations**: Tutte le operazioni DB sono asincrone
- **Background Processing**: Monitoring senza impatto performance
- **Materialized Views**: Pre-aggregazione per analytics veloci

## 📞 Supporto e Troubleshooting

### Log Analysis

```bash
# Cerca errori nei log
grep "❌" logs/convergio.log

# Monitor circuit breaker
grep "🚦" logs/convergio.log  

# Budget alerts
grep "🚨" logs/convergio.log
```

### Comandi Utili

```bash
# Check system status
curl http://localhost:9000/api/v1/cost-management/system/status

# Manual system check
curl -X POST http://localhost:9000/api/v1/cost-management/system/check

# Get budget summary
curl http://localhost:9000/api/v1/cost-management/budget/summary
```

---

## 🎯 Conclusioni

Il **Sistema di Tracciamento Costi Potenziato** fornisce una soluzione completa e robusta per la gestione intelligente dei costi API nella piattaforma Convergio.

Con funzionalità avanzate come aggiornamenti prezzi automatici, circuit breaker intelligente, e previsioni accurate, il sistema garantisce controllo totale sui costi mantenendo la performance e l'affidabilità del servizio.

**Sviluppato con ❤️ per Convergio - Agosto 2025**