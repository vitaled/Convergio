# 🔍 ANALISI PROFONDA DEI PROBLEMI

## PROBLEMA RADICE IDENTIFICATO

### ❌ **Ali NON è un vero orchestratore AutoGen!**

## ARCHITETTURA ATTUALE (SBAGLIATA)
```
Ali Intelligence API
    └── Funzione Python hardcoded
        ├── Finti "reasoning steps"
        ├── Database query (reale)
        └── Risposta generica inventata
```

## ARCHITETTURA CORRETTA (DA IMPLEMENTARE)
```
Ali Intelligence API
    └── AutoGen GroupChat Orchestrator
        ├── Ali (AssistantAgent con system prompt CEO)
        ├── Amy (AssistantAgent con tools per database)
        ├── Sofia (AssistantAgent con Perplexity tool)
        ├── Luke (AssistantAgent con technical analysis)
        └── Steve (AssistantAgent con strategy synthesis)
```

## PROBLEMI SPECIFICI

### 1. **NO AUTOGEN 0.7.x**
- Non c'è `from autogen import AssistantAgent, ConversableAgent`
- Non c'è `from autogen_ext.models.openai import OpenAIChatCompletionClient`
- Gli agenti NON sono veri agenti AutoGen

### 2. **NO PERPLEXITY TOOL**
- Perplexity API key è nel .env ✅
- MA non c'è nessun tool/function registrato per usarla
- Sofia dovrebbe avere:
```python
@ali.register_for_llm(description="Search web for real-time data")
@sofia.register_for_execution()
async def search_web(query: str) -> str:
    # Chiamata a Perplexity API
    return perplexity_search(query)
```

### 3. **ALI NON ORCHESTRA**
- Ali è solo una funzione che genera testo
- Non c'è GroupChat
- Non c'è message passing tra agenti
- Non c'è tool execution

### 4. **COST TRACKING ROTTO**
- I costi non vengono tracciati perché:
  - Non c'è hook su OpenAI client
  - Non c'è callback per token counting
  - AutoGen 0.7.x ha tracking built-in ma non è usato

## SINTOMI vs CAUSE

| SINTOMO | CAUSA RADICE |
|---------|--------------|
| "23.5% YoY" sempre uguale | Hardcoded in `_get_database_insights()` |
| Perplexity non usata | Nessun tool registrato |
| Costi non tracciati | No AutoGen callbacks |
| Risposte inventate | No real agent orchestration |
| Ali non coordina | Non è un vero orchestrator |

## SOLUZIONE RICHIESTA

### 1. **Implementare Ali come VERO orchestratore AutoGen**
```python
from autogen import AssistantAgent, GroupChat, GroupChatManager
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Client OpenAI
client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Ali come orchestratore principale
ali = AssistantAgent(
    name="Ali_ChiefOfStaff",
    system_message="You are Ali, Chief of Staff...",
    model_client=client
)

# Altri agenti
amy = AssistantAgent(name="Amy_CFO", ...)
sofia = AssistantAgent(name="Sofia_Marketing", ...)

# GroupChat per orchestrazione
groupchat = GroupChat(
    agents=[ali, amy, sofia, luke, steve],
    messages=[],
    max_round=10,
    selection_method="auto"
)

manager = GroupChatManager(groupchat=groupchat)
```

### 2. **Registrare Perplexity come tool**
```python
from autogen import register_function

def search_perplexity(query: str) -> str:
    """Search web using Perplexity API"""
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {PERPLEXITY_KEY}"},
        json={"model": "sonar-medium-online", "messages": [{"role": "user", "content": query}]}
    )
    return response.json()["choices"][0]["message"]["content"]

# Registra per Sofia
register_function(
    search_perplexity,
    caller=sofia,
    executor=ali,
    description="Search web for real-time data"
)
```

### 3. **Cost tracking con callbacks**
```python
def track_token_usage(messages, response, **kwargs):
    tokens = response.usage.total_tokens
    cost = calculate_cost(tokens, "gpt-4o-mini")
    cost_tracker.add_cost(cost, tokens)

client.register_hook("on_completion", track_token_usage)
```

## VERIFICA RICHIESTA
1. Ali deve essere un VERO GroupChatManager
2. Gli agenti devono essere VERI AssistantAgent
3. Perplexity deve essere un tool registrato
4. I costi devono essere tracciati via callbacks
5. Le risposte devono venire da VERA orchestrazione multi-agente