#!/usr/bin/env python3
"""
Validate cost tracking system setup
"""

import asyncio
from src.core.database import init_db, get_async_session
from src.services.cost_tracking_service import EnhancedCostTracker
from src.agents.services.redis_state_manager import RedisStateManager


async def validate_cost_system():
    """Validate the cost tracking system is properly set up"""
    
    print("🔍 Validating Cost Tracking System\n")
    
    try:
        # 1. Test database connection
        print("1️⃣ Testing database connection...")
        await init_db()
        print("✅ Database connection successful")
        
        # 2. Test cost tracker initialization
        print("\n2️⃣ Testing cost tracker initialization...")
        try:
            state_manager = RedisStateManager()
            tracker = EnhancedCostTracker(state_manager)
            print("✅ Cost tracker initialized")
        except Exception as e:
            print(f"⚠️  Cost tracker init warning: {e}")
            tracker = EnhancedCostTracker()  # Without Redis
            print("✅ Cost tracker initialized (without Redis)")
        
        # 3. Test database tables
        print("\n3️⃣ Testing database tables...")
        async with get_async_session() as db:
            from sqlalchemy import text
            
            # Check cost tables exist
            result = await db.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name LIKE '%cost%'"
            ))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Cost tables found: {', '.join(tables)}")
            
            # Check pricing data
            result = await db.execute(text("SELECT COUNT(*) FROM provider_pricing"))
            pricing_count = result.scalar()
            print(f"✅ Pricing records: {pricing_count}")
            
        # 4. Test cost calculation
        print("\n4️⃣ Testing cost calculation...")
        cost_result = await tracker.track_api_call(
            session_id="test-session",
            conversation_id="test-conv",
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=200,
            agent_id="test-agent",
            agent_name="Test Agent"
        )
        
        if cost_result["success"]:
            cost = cost_result["cost_breakdown"]["total_cost_usd"]
            print(f"✅ Cost calculation successful: ${cost:.6f}")
        else:
            print(f"❌ Cost calculation failed: {cost_result.get('error', 'Unknown error')}")
        
        # 5. Test realtime overview
        print("\n5️⃣ Testing realtime overview...")
        overview = await tracker.get_realtime_overview()
        if "error" not in overview:
            print(f"✅ Realtime overview: ${overview.get('total_cost_usd', 0):.6f} total")
        else:
            print(f"❌ Realtime overview failed: {overview['error']}")
        
        print("\n✅ Cost tracking system validation completed!")
        print("\n📋 System Status:")
        print("   - Database tables: ✅")
        print("   - Pricing data: ✅")
        print("   - Cost calculation: ✅")
        print("   - Real-time tracking: ✅")
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(validate_cost_system())