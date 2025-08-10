#!/usr/bin/env python3
"""
Test Amy CFO's intelligent responses
"""

import asyncio
import json
from src.agents.services.agent_intelligence import AgentIntelligence
from src.agents.services.agent_loader import DynamicAgentLoader

async def test_amy_responses():
    """Test Amy CFO with different types of questions"""
    
    # Create Amy's intelligence
    amy_ai = AgentIntelligence("amy-cfo", None)
    
    test_questions = [
        "what's the trend of MSFT in the last year?",
        "analyze our Q4 revenue",
        "hello",
        "budget recommendations?",
        "xyz"  # Unclear query that should trigger clarification
    ]
    
    print("=" * 80)
    print("TESTING AMY CFO INTELLIGENT RESPONSES")
    print("=" * 80)
    
    for question in test_questions:
        print(f"\n🎯 Question: {question}")
        print("-" * 40)
        
        # Test intent analysis
        intent = await amy_ai._analyze_intent_and_data_needs(question)
        print(f"📊 Intent Analysis:")
        print(f"   - Needs Internal Data: {intent['needs_internal_data']}")
        print(f"   - Needs AI Analysis: {intent['needs_ai_analysis']}")
        print(f"   - Needs Clarification: {intent['needs_clarification']}")
        print(f"   - Confidence: {intent['confidence']}")
        
        # Test internal data fetch
        internal_data = await amy_ai._fetch_internal_data(question)
        if internal_data:
            print(f"💾 Internal Data Found: {internal_data[:100]}...")
        
        # Generate response (will use fallback since no OpenAI key in test)
        response = await amy_ai.generate_intelligent_response(
            message=question,
            context={"test_mode": True}
        )
        
        print(f"\n🤖 Amy's Response:")
        print(response)
        print("=" * 80)

async def test_system_prompts():
    """Test that system prompts include the framework"""
    
    print("\n" + "=" * 80)
    print("TESTING SYSTEM PROMPT GENERATION")
    print("=" * 80)
    
    # Load agent metadata
    loader = DynamicAgentLoader()
    await loader.load_agents()
    
    # Check Amy's system message
    amy_metadata = loader.agent_metadata.get("amy-cfo")
    if amy_metadata:
        system_message = loader._build_system_message(amy_metadata)
        
        # Check for key framework elements
        has_framework = "MANDATORY: Follow the Intelligent Decision Framework" in system_message
        has_data_sources = "Convergio DB/Vector" in system_message
        has_ai_intelligence = "AI intelligence" in system_message
        has_escalation = "escalate to Ali" in system_message
        
        print(f"\n✅ Framework included: {has_framework}")
        print(f"✅ Data sources mentioned: {has_data_sources}")
        print(f"✅ AI intelligence mentioned: {has_ai_intelligence}")
        print(f"✅ Escalation to Ali: {has_escalation}")
        
        print(f"\n📝 System Message Preview (first 500 chars):")
        print(system_message[:500])
    else:
        print("❌ Amy CFO metadata not found!")

if __name__ == "__main__":
    asyncio.run(test_amy_responses())
    asyncio.run(test_system_prompts())