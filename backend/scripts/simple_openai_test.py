#!/usr/bin/env python3
"""
Simple OpenAI model tester.
Tests a list of GPT-5 and GPT-4 nano/mini models, reports which work, and finds the cheapest available.
"""

import os
import asyncio

# API key and model config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-4o-mini"
ECONOMICAL_MODELS = ["gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-3.5-turbo"]

# List of models to test
TEST_MODELS = [
    "gpt-5.5-nano",
    "gpt-5.5-mini",
    "gpt-5-nano",
    "gpt-5-mini",
    "gpt-4.5-nano",
    "gpt-4.5-mini",
    "gpt-4o-mini",
    "gpt-4o-mini-2024-07-18"
]

async def test_openai_simple():
    print("🔍 Simple OpenAI test...")
    if not OPENAI_API_KEY:
        print("❌ No API key found. Please set OPENAI_API_KEY in your environment.")
        return False

    print(f"API Key (first 20 chars): {OPENAI_API_KEY[:20]}...")
    results = {}

    try:
        import openai
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

        messages = [
            {"role": "system", "content": "Rispondi brevemente in italiano."},
            {"role": "user", "content": "Ciao, chi sei?"}
        ]

        for model in TEST_MODELS:
            print(f"\n📌 Testing model: {model}")
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=50,
                    temperature=0.7
                )
                content = response.choices[0].message.content
                if content and content.strip():
                    print(f"✅ {model}: {content}")
                    results[model] = {"success": True, "reason": ""}
                else:
                    print(f"⚠️ {model}: Empty response")
                    results[model] = {"success": False, "reason": "Empty response"}
            except Exception as e:
                err_str = str(e)
                print(f"❌ {model}: {err_str}")
                if any(term in err_str.lower() for term in [
                    "model_not_found", "not found", "unsupported", "does not exist", "unavailable"
                ]):
                    print(f"ℹ️ Model '{model}' is unavailable for your API key or plan.")
                    err_str += " (unavailable for API key/plan)"
                results[model] = {"success": False, "reason": err_str}

        # Summary
        print("\n=== SUMMARY ===")
        success_models = [m for m, r in results.items() if r["success"]]
        failed_models = [m for m, r in results.items() if not r["success"]]
        print(f"✅ Successes: {success_models}")
        print("❌ Failures:", [f"{m}: {results[m]['reason']}" for m in failed_models])

        # Find cheapest working model
        cheapest_model = None
        for candidate in ECONOMICAL_MODELS:
            if candidate in success_models:
                cheapest_model = candidate
                break
        if cheapest_model:
            print(f"💰 Cheapest working model: {cheapest_model}")
        else:
            print("💰 No economical model from ECONOMICAL_MODELS list is available.")

        return len(success_models) > 0

    except ImportError:
        print("⚠️ openai library not available.")
        return False
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_openai_simple())
    print(f"\n🎯 Test result: {'SUCCESS' if result else 'FAILED'}")
