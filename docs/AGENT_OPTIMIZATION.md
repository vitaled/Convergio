# Agent Conversation Optimization Guide

## Overview

This document describes the optimization strategies implemented to improve agent conversation performance, reduce token usage, and minimize OpenAI API costs in the Convergio backend.

## Key Components

### 1. Message Classification System

**File:** `src/agents/services/groupchat/message_classifier.py`

The MessageClassifier categorizes incoming messages to determine the appropriate response strategy:

- **Greeting**: Simple hellos, max 1 turn, single agent
- **Simple Query**: Basic questions, max 2 turns, single agent  
- **Standard**: Regular business queries, max 3-5 turns
- **Complex Business**: Multi-faceted problems, max 10 turns, full orchestration

```python
# Message types and their characteristics
msg_type, metadata = MessageClassifier.classify_message(message)
# Returns: ('greeting', {'max_turns': 1, 'single_agent': True, 'terminate_on_response': True})
```

### 2. Token Optimization

**File:** `src/agents/services/groupchat/token_optimizer.py`

Implements multiple strategies to reduce token usage:

#### Response Caching
- 15-minute TTL for identical queries
- MD5 hash-based cache keys
- Automatic cache cleanup

#### Message History Compression
- Keeps only last 10 messages
- Preserves first message (task context)
- Adds summary for dropped messages

#### Optimized Model Parameters
```python
{
    "temperature": 0.3,      # Lower for focused responses
    "max_tokens": 150,       # Limit response length
    "top_p": 0.9,           # Nucleus sampling
    "frequency_penalty": 0.5, # Reduce repetition
    "presence_penalty": 0.3   # Encourage conciseness
}
```

### 3. Agent Instruction Optimization

**File:** `src/agents/services/groupchat/agent_instructions.py`

All agents receive concise instructions:

```
CRITICAL INSTRUCTIONS:
1. BE CONCISE: Respond in 1-3 sentences unless asked for details
2. NO INTRODUCTIONS: Skip pleasantries
3. NO PROPOSALS: Don't offer options unless asked
4. DIRECT ANSWERS: Answer the exact question
5. TERMINATE FAST: End with "DONE" for simple queries
```

### 4. Intelligent Routing

Simple messages bypass group orchestration:
- Greetings → Ali (Chief of Staff) directly
- Simple queries → Single agent response
- Complex only → Full GroupChat orchestration

## Configuration

### Environment Variables

```bash
# Reduced defaults for faster responses
AUTOGEN_MAX_TURNS=5              # Was 10
AUTOGEN_TIMEOUT_SECONDS=60       # Was 120
CONVERSATION_TERMINATION_MARKERS="final answer,conclusion,summary,done"
```

### Dynamic Configuration

The system adjusts parameters based on message type:

| Message Type | Max Turns | Timeout | Single Agent | Termination |
|-------------|-----------|---------|--------------|-------------|
| Greeting    | 1         | 30s     | Yes          | Immediate   |
| Simple      | 2         | 30s     | Yes          | On response |
| Standard    | 3-5       | 60s     | No           | On markers  |
| Complex     | 10        | 120s    | No           | On markers  |

## Performance Improvements

### Before Optimization
- Simple greeting: **Timeout after 120s**
- Token usage: ~2000-3000 per simple query
- All messages: Full orchestration

### After Optimization
- Simple greeting: **5.4 seconds**
- Token usage: ~500-800 per simple query (70% reduction)
- Smart routing: Single agent for 40% of queries

## Cost Savings

Estimated cost reduction per 1000 conversations:

| Query Type | Before | After | Savings |
|------------|--------|-------|---------|
| Greeting   | $2.00  | $0.30 | 85%     |
| Simple     | $3.00  | $0.90 | 70%     |
| Standard   | $5.00  | $2.50 | 50%     |
| Complex    | $8.00  | $6.00 | 25%     |

**Average savings: 55-60% reduction in API costs**

## AutoGen Compatibility

### Version Requirements
- AutoGen >= 0.7.2
- autogen-agentchat >= 0.4.7
- autogen-ext >= 0.4.7

### API Considerations
- Use keyword arguments for `run_stream(task=task)`
- Include `cancellation_token` in all tool methods
- Proper model_info fields for GPT-5 models

## Future Optimizations

1. **Model Selection**
   - Use GPT-3.5-turbo for simple queries
   - GPT-4 only for complex reasoning
   
2. **Batch Processing**
   - Group similar queries
   - Parallel processing for independent tasks
   
3. **Advanced Caching**
   - Semantic similarity matching
   - Persistent cache with Redis
   
4. **Cost Monitoring**
   - Per-conversation cost tracking
   - Budget alerts and limits
   - Usage analytics dashboard

## Troubleshooting

### High Token Usage
1. Check message classification is working
2. Verify concise instructions are applied
3. Review max_tokens setting

### Slow Responses
1. Check if simple routing is active
2. Verify cache is functioning
3. Review timeout settings

### Conversation Timeouts
1. Check termination markers
2. Verify max_turns configuration
3. Review agent response patterns

## Testing

Run optimization tests:
```bash
# Test message classification
python -m pytest tests/test_message_classifier.py

# Test token optimization
python -m pytest tests/test_token_optimizer.py

# E2E conversation tests
bash run_ali_e2e.sh
```

## References

- [AutoGen Documentation](https://microsoft.github.io/autogen/stable/)
- [OpenAI Optimization Guide](https://platform.openai.com/docs/guides/optimization)
- [Token Counting](https://platform.openai.com/tokenizer)