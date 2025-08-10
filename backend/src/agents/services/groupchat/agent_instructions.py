"""
Agent Instruction Optimization Module
Provides concise system prompts and token optimization
"""

CONCISE_INSTRUCTIONS = """
CRITICAL INSTRUCTIONS FOR ALL AGENTS:

1. BE CONCISE: Respond in 1-3 sentences unless explicitly asked for details
2. NO INTRODUCTIONS: Skip pleasantries, get to the point
3. NO PROPOSALS: Don't offer options unless asked
4. DIRECT ANSWERS: Answer the exact question, nothing more
5. TERMINATE FAST: End with "DONE" for simple queries

For greetings: One sentence max
For status: 2-3 bullet points max  
For questions: Direct answer only
For complex tasks: Ask for clarification first

REMEMBER: Every token costs money. Be brief."""

def optimize_agent_prompt(original_prompt: str, message_type: str = "standard") -> str:
    """Add concise instructions to agent prompts based on message type"""
    
    if message_type in ["greeting", "simple_query"]:
        return f"{CONCISE_INSTRUCTIONS}\n\n{original_prompt}\n\nMAX RESPONSE: 50 words"
    else:
        return f"{CONCISE_INSTRUCTIONS}\n\n{original_prompt}"