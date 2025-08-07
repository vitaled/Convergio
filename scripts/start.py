#!/usr/bin/env python3
"""
🚀 Convergio - REAL Production Startup Script
Launch the unified backend with ZERO technical debt!
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all dependencies are installed and environment is correct for local dev"""
    print("🔍 Checking dependencies...")
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required!")
        sys.exit(1)
    if not Path("backend/src/main.py").exists():
        print("❌ Run this script from the Convergio root directory!")
        sys.exit(1)
    if not Path("backend/.env").exists():
        print("❌ backend/.env file not found! Copy backend/.env.example to backend/.env and configure it.")
        sys.exit(1)
    print("✅ Dependencies check passed")


def install_requirements():
    """Install Python requirements for backend"""
    print("📦 Installing Python requirements (backend)...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"
        ], check=True, cwd=Path.cwd())
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements!")
        sys.exit(1)


def check_environment():
    """Check environment variables from backend/.env"""
    print("🔧 Checking environment configuration...")
    from dotenv import load_dotenv
    load_dotenv(dotenv_path="backend/.env")
    required_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "POSTGRES_HOST",
        "REDIS_HOST"
    ]
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    if missing_vars:
        print(f"❌ Missing environment variables in backend/.env: {missing_vars}")
        sys.exit(1)
    print("✅ Environment configuration valid")


def check_services():
    """Check if required services (Postgres, Redis) are running"""
    print("🔍 Checking required services...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", 5432),
            database=os.getenv("POSTGRES_DB", "convergio_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        conn.close()
        print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("💡 Make sure PostgreSQL is running and database exists (check backend/.env)")
        sys.exit(1)
    try:
        import redis
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Make sure Redis is running (check backend/.env)")
        sys.exit(1)


def test_openai_api():
    """Test OpenAI API connection"""
    
    print("🤖 Testing OpenAI API connection...")
    
    try:
        import httpx
        import asyncio
        
        async def test_api():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": "Hello, test connection"}],
                        "max_tokens": 10
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    print("✅ OpenAI API connection successful")
                    return True
                else:
                    print(f"❌ OpenAI API test failed: {response.status_code}")
                    return False
        
        result = asyncio.run(test_api())
        if not result:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        sys.exit(1)


def count_agents():
    """Count available agents in the system"""
    
    print("🤖 Counting available agents...")
    
    try:
        agents_dir = Path("backend/src/agents/definitions")
        if not agents_dir.exists():
            print("❌ Agents directory not found!")
            return
        
        agent_files = list(agents_dir.glob("*.md"))
        excluded_files = {"CommonValuesAndPrinciples.md", "MICROSOFT_VALUES.md"}
        valid_agents = [f for f in agent_files if f.name not in excluded_files]
        
        print(f"✅ Found {len(valid_agents)} REAL agents ready for deployment:")
        for agent_file in valid_agents[:10]:  # Show first 10
            agent_name = agent_file.stem.replace("-", " ").title()
            print(f"   • {agent_name}")
        
        if len(valid_agents) > 10:
            print(f"   ... and {len(valid_agents) - 10} more agents")
            
    except Exception as e:
        print(f"⚠️ Could not count agents: {e}")


def start_backend():
    """Start the FastAPI backend for local development"""
    print("🚀 Starting Convergio Backend (local dev mode)...")
    print("=" * 60)
    print("🌐 Backend URL: http://localhost:9000")
    print("📚 API Docs: http://localhost:9000/docs")
    print("❤️ Health Check: http://localhost:9000/health")
    print("🔐 Authentication: http://localhost:9000/api/v1/auth")
    print("🤖 AI Agents: http://localhost:9000/api/v1/agents")
    print("🔍 Vector Search: http://localhost:9000/api/v1/vector")
    print("=" * 60)
    print("🛑 Press Ctrl+C to stop")
    print()
    
    def open_browser_tabs():
        """Open browser tabs for backend endpoints and frontend after a delay"""
        import webbrowser
        import time
        
        # Wait 5 seconds for the backend to start
        time.sleep(5)
        
        try:
            # Open backend endpoints
            print("🌐 Opening browser tabs for testing...")
            webbrowser.open("http://localhost:9000/health")
            time.sleep(1)  # Small delay between tabs
            webbrowser.open("http://localhost:9000/docs")
            time.sleep(1)
            
            # Try to open frontend if available
            try:
                import httpx
                response = httpx.get("http://localhost:4000", timeout=2)
                if response.status_code == 200:
                    webbrowser.open("http://localhost:4000")
                    print("✅ Frontend tab opened (http://localhost:4000)")
            except:
                print("💡 Frontend not running. Start it with: cd frontend && npm run dev")
                
        except Exception as e:
            print(f"⚠️ Could not open browser tabs: {e}")
    
    # Start browser opening in a separate thread
    import threading
    browser_thread = threading.Thread(target=open_browser_tabs, daemon=True)
    browser_thread.start()
    
    try:
        os.chdir("backend")
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.main:app",
            "--host", "0.0.0.0",
            "--port", "9000",
            "--reload",
            "--log-level", "info"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Convergio...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        sys.exit(1)


def main():
    print("🚀 CONVERGIO - LOCAL DEVELOPMENT STARTUP")
    print("=" * 50)
    print("🎯 Docker is NOT required. This script is for bare metal local dev.")
    print("🤖 REAL AI agents | REAL vector search | REAL everything")
    print("=" * 50)
    print()
    check_dependencies()
    install_requirements()
    check_environment()
    check_services()
    test_openai_api()
    count_agents()
    print()
    print("✅ ALL SYSTEMS GO! Starting backend...")
    print()
    start_backend()
    print()
    print("👉 To start the frontend, open a new terminal and run:")
    print("   cd frontend && npm install && npm run dev")


if __name__ == "__main__":
    main()
