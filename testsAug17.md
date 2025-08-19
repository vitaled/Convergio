# 🎯 **Piano Test End-to-End Convergio - 17 Agosto 2025**

## **Obiettivo**
Creare e eseguire test Playwright che simulino use case reali di Convergio con:
- ✅ Risposte reali degli agenti AI (no mock)  
- ✅ Chiamate effettive a OpenAI/Anthropic/Perplexity
- ✅ Orchestrazioni multi-agenti
- ✅ Test allineati al business di Convergio
- ✅ Focus su Ali (Chief of Staff) e workflow reali

## **Configurazione Verificata**
- ✅ **API Keys**: OpenAI, Anthropic, Perplexity configurate
- ✅ **Database**: PostgreSQL (localhost:5432/convergio_db) operativo
- ✅ **Redis**: Configurato e funzionante  
- ✅ **Servizi**: Backend (9000), Frontend (4000)
- ✅ **Test Users**: admin@convergio.io, roberdan@convergio.local

## **Test Cases Strategici**

### **🤖 Scenario 1: Ali Intelligence & Strategic Queries**
**Obiettivo**: Testare Ali come Chief of Staff per query strategiche

**Test Cases:**
1. **Ali Strategic Analysis**
   - Query: "Ali, analizza la strategia di crescita per Q4 2024"
   - Attese: Risposta articolata, multi-step reasoning, dati strutturati
   - Validazioni: Risposta > 200 caratteri, no errori console, tempo < 30s

2. **Ali Multi-Agent Coordination**  
   - Query: "Ali, coordina Amy (CFO) e Marcus (PM) per un business plan"
   - Attese: Orchestrazione multi-agenti, deleghe specifiche, risultati coordinati
   - Validazioni: Coinvolgimento multipli agenti, risposte coordinate

3. **Ali Research & Internet Search**
   - Query: "Ali, trova le ultime tendenze nel settore AI per consulenza"
   - Attese: Ricerca web via Perplexity, analisi di mercato aggiornata
   - Validazioni: Dati recenti, fonti web citate, analisi personalizzata

### **💼 Scenario 2: Business Operations & Project Management**

**Test Cases:**
4. **Project Creation & Management**
   - Azione: Creazione nuovo progetto tramite UI
   - Query a Marcus (PM): "Crea una roadmap per questo progetto"
   - Attese: Progetto creato, roadmap dettagliata
   - Validazioni: Progetto salvato in DB, risposta strutturata

5. **Talent & Resource Management**  
   - Query a Giulia (HR): "Trova i migliori talenti per questo progetto"
   - Attese: Analisi competenze, raccomandazioni talenti
   - Validazioni: Lista talenti, criteri di matching, disponibilità

6. **Financial Analysis**
   - Query a Amy (CFO): "Analizza il budget e ROI previsto"  
   - Attese: Analisi finanziaria dettagliata, proiezioni
   - Validazioni: Calcoli numerici corretti, grafici/tabelle

### **🔍 Scenario 3: Research & Knowledge Integration**

**Test Cases:**
7. **Technical Architecture Consultation**
   - Query a Baccio (Tech Architect): "Progetta l'architettura per una piattaforma SaaS"
   - Attese: Diagrammi architetturali, stack tecnologico
   - Validazioni: Dettagli tecnici, best practices, scalabilità

8. **Market Intelligence**
   - Query combinata: Ali + ricerca web + analisi competitiva
   - Attese: Report di mercato con dati aggiornati
   - Validazioni: Fonti esterne, trend analysis, raccomandazioni

### **🎨 Scenario 4: Creative & Design Workflows**

**Test Cases:**
9. **UX/UI Design Process**
   - Query a Sara (UX Designer): "Progetta l'interfaccia per dashboard executive"
   - Attese: Wireframes, user journey, principi design
   - Validazioni: Mockups descrittivi, usabilità, accessibilità

10. **Content & Storytelling**
    - Query a Riccardo (Storyteller): "Crea la narrative per il lancio prodotto"
    - Attese: Storia coinvolgente, messaggi chiave
    - Validazioni: Tono appropriato, call-to-action, audience targeting

### **⚡ Scenario 5: Performance & Stress Testing**

**Test Cases:**
11. **Concurrent Multi-Agent Sessions**
    - 5 query simultanee a agenti diversi
    - Attese: Tutte le risposte completate correttamente
    - Validazioni: No timeout, no errors, risposte coerenti

12. **Complex Orchestration Workflow**
    - Workflow end-to-end: Ali → Marcus → Amy → Baccio → Sara
    - Attese: Coordinamento fluido, handoff corretto
    - Validazioni: Ogni passaggio documentato, risultato finale coerente

## **Implementazione Tecnica**

### **Struttura File Test**
```
tests/
├── e2e/
│   ├── test_ali_intelligence.spec.ts          # Scenario 1
│   ├── test_business_operations.spec.ts       # Scenario 2  
│   ├── test_research_workflows.spec.ts        # Scenario 3
│   ├── test_creative_workflows.spec.ts        # Scenario 4
│   └── test_performance_stress.spec.ts        # Scenario 5
├── fixtures/
│   ├── test-data.json                         # Dati test strutturati
│   └── user-credentials.json                  # Credenziali test
└── utils/
    ├── agent-helpers.ts                       # Helper per interazioni agenti
    ├── wait-helpers.ts                        # Wait utilities per AI responses
    └── validation-helpers.ts                  # Validatori custom
```

### **Configurazione Playwright**
- **Timeouts**: 60s per query AI, 120s per orchestrazioni complesse
- **Retry**: 2 tentativi per flaky tests dovuti a AI latency
- **Browsers**: Chrome (headless), Firefox (fallback)
- **Screenshots**: Su failure per debugging
- **Video**: Recording delle orchestrazioni complesse

### **Setup & Teardown**
- **Before Each**: Verifica servizi up, clean session storage
- **After Each**: Cleanup conversations, reset agent state  
- **Test Isolation**: Ogni test indipendente, no side effects

## **Criteri di Successo**

### **Funzionali**
- ✅ Tutte le risposte AI generate correttamente (no fallback)
- ✅ Orchestrazioni multi-agenti completate
- ✅ Ricerche web funzionanti (Perplexity integration)
- ✅ Dati persistiti correttamente in database

### **Performance**
- ✅ Query semplici: < 15 secondi
- ✅ Orchestrazioni complesse: < 60 secondi  
- ✅ Ricerche web: < 30 secondi
- ✅ Concurrent tests: no degradation

### **Qualità**
- ✅ Zero errori JavaScript in console
- ✅ Zero errori 500/400 nelle API calls
- ✅ Risposte AI > lunghezza minima e coerenza
- ✅ UI responsiva e navigabile

## **Execution Plan**

### **Fase 1: Setup & Configuration** ⏳
1. Verifica servizi (start.sh)
2. Setup Playwright environment  
3. Creazione test utilities

### **Fase 2: Core Agent Tests** ⏳
1. Implementazione Scenario 1 (Ali Intelligence)
2. Validazione risposte reali AI
3. Debug & optimization

### **Fase 3: Business Workflows** ⏳
1. Implementazione Scenari 2-4
2. Test orchestrazioni multi-agenti
3. Validazione persistenza dati

### **Fase 4: Performance & Stress** ⏳  
1. Implementazione Scenario 5
2. Load testing concurrent sessions
3. Optimization final

### **Fase 5: CI/CD Integration** ⏳
1. Configurazione automated runs
2. Reporting & monitoring
3. Documentation finale

## **Note di Implementazione**

### **Gestione Timing AI**
```typescript
// Wait helper per risposte AI variabili
const waitForAIResponse = async (page, selector, minLength = 100) => {
  await page.waitForSelector(selector)
  await page.waitForFunction(
    (sel, len) => document.querySelector(sel)?.textContent?.length > len,
    selector, minLength
  )
}
```

### **Validazione Qualità Risposte**
```typescript
// Validatore intelligenza risposta
const validateAIQuality = (response: string) => {
  return response.length > 200 && 
         !response.includes('I cannot') &&
         !response.includes('fallback') &&
         response.split(' ').length > 30
}
```

### **Orchestrazione Multi-Agenti**
```typescript
// Test coordinamento agenti
const testAgentOrchestration = async (page, query, expectedAgents) => {
  await sendQuery(page, query)
  for (const agent of expectedAgents) {
    await waitForAgentResponse(page, agent)
    const response = await getAgentResponse(page, agent)
    expect(validateAIQuality(response)).toBe(true)
  }
}
```

---

**🎯 Obiettivo: Sistema Convergio completamente funzionante con test realistici che validano ogni aspetto del business workflow attraverso AI responses autentiche.**