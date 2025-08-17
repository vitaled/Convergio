#!/usr/bin/env python3
"""
🤖 CONVERGIO COMPREHENSIVE AGENT TEST SUITE
==========================================

Purpose: Test all 48 agents in the Convergio ecosystem for:
- Agent initialization and availability
- Core capabilities verification
- Agent-specific tool usage
- Response quality and consistency
- Performance and reliability

This suite dynamically discovers and tests all agents defined in the system.

Author: Convergio Test Suite
Last Updated: August 2025
"""

import asyncio
import json
import logging
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pytest
import httpx
from dataclasses import dataclass

# Setup paths
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from src.core.config import get_settings
from src.agents.services.agent_loader import DynamicAgentLoader

# Configure logging
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(exist_ok=True)
TEST_NAME = Path(__file__).stem
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"{TEST_NAME}_{TIMESTAMP}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class AgentTestResult:
    """Result of testing a single agent."""
    agent_id: str
    name: str
    role: str
    category: str
    tier: str
    initialization_success: bool
    response_received: bool
    response_time_ms: float
    capabilities_tested: List[str]
    tools_tested: List[str]
    errors: List[str]
    warnings: List[str]
    test_score: float  # 0-100


class ComprehensiveAgentTestSuite:
    """
    Comprehensive test suite for all Convergio agents.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "http://localhost:9000"
        self.agent_loader = DynamicAgentLoader(
            "/Users/roberdan/GitHub/convergio/backend/src/agents/definitions"
        )
        self.test_results: List[AgentTestResult] = []
        self.agent_definitions = {}
        
    async def discover_agents(self) -> Dict[str, Any]:
        """Discover all available agents in the system."""
        logger.info("🔍 Discovering all agents...")
        
        # Load agent definitions
        definitions_path = Path("/Users/roberdan/GitHub/convergio/backend/src/agents/definitions")
        agent_files = list(definitions_path.glob("*.md"))
        
        agents = {}
        for agent_file in agent_files:
            if agent_file.name in ["CommonValuesAndPrinciples.md", "agent.schema.json"]:
                continue
                
            try:
                content = agent_file.read_text()
                if "---" in content:
                    yaml_content = content.split("---")[1]
                    metadata = yaml.safe_load(yaml_content)
                    if metadata and "agent_id" in metadata:
                        agents[metadata["agent_id"]] = {
                            "metadata": metadata,
                            "file_path": str(agent_file),
                            "content": content
                        }
            except Exception as e:
                logger.warning(f"Failed to parse {agent_file.name}: {e}")
        
        logger.info(f"📊 Discovered {len(agents)} agents")
        self.agent_definitions = agents
        return agents
    
    async def test_agent_initialization(self, agent_id: str, agent_data: Dict) -> bool:
        """Test if an agent can be properly initialized."""
        try:
            metadata = agent_data["metadata"]
            
            # Check required fields
            required_fields = ["agent_id", "name", "role", "tier", "category"]
            for field in required_fields:
                if field not in metadata:
                    logger.error(f"Agent {agent_id} missing required field: {field}")
                    return False
            
            # Check if agent has system prompt
            content = agent_data["content"]
            if len(content.split("---")[-1].strip()) < 100:
                logger.warning(f"Agent {agent_id} has very short system prompt")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent {agent_id}: {e}")
            return False
    
    async def test_agent_conversation(self, agent_id: str, agent_data: Dict) -> tuple[bool, float, str]:
        """Test agent conversation capability."""
        try:
            metadata = agent_data["metadata"]
            
            # Prepare test message based on agent category
            test_messages = {
                "strategic": "What is your strategic recommendation for our company?",
                "financial": "What are the key financial metrics we should monitor?",
                "technical": "What technical architecture would you recommend?",
                "marketing": "What marketing strategy would you suggest?",
                "operations": "How can we optimize our operational processes?",
                "creative": "What creative approach would you recommend?",
                "security": "What security measures should we implement?",
                "hr": "What talent acquisition strategy do you suggest?",
                "legal": "What compliance considerations should we be aware of?",
                "analytics": "What data insights can you provide?"
            }
            
            category = metadata.get("category", "general")
            test_message = test_messages.get(category, "Please introduce yourself and your capabilities.")
            
            start_time = time.time()
            
            async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
                response = await client.post(
                    "/api/v1/agents/conversation",
                    json={
                        "message": test_message,
                        "agent": agent_id,
                        "session_id": f"test_{agent_id}_{TIMESTAMP}",
                        "context": {"test_mode": True}
                    }
                )
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response", data.get("content", ""))
                    
                    if len(response_text) > 10:
                        return True, response_time, response_text
                    else:
                        return False, response_time, "Empty or very short response"
                else:
                    return False, response_time, f"HTTP {response.status_code}: {response.text}"
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
            return False, response_time, str(e)
    
    async def test_agent_capabilities(self, agent_id: str, agent_data: Dict) -> List[str]:
        """Test agent's declared capabilities."""
        tested_capabilities = []
        metadata = agent_data["metadata"]
        capabilities = metadata.get("capabilities", [])
        
        for capability in capabilities[:3]:  # Test up to 3 capabilities
            try:
                test_message = f"Please demonstrate your capability in: {capability}"
                
                async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as client:
                    response = await client.post(
                        "/api/v1/agents/conversation",
                        json={
                            "message": test_message,
                            "agent": agent_id,
                            "session_id": f"cap_test_{agent_id}_{TIMESTAMP}",
                            "context": {"capability_test": capability}
                        }
                    )
                    
                    if response.status_code == 200:
                        tested_capabilities.append(capability)
                        
            except Exception as e:
                logger.warning(f"Failed to test capability '{capability}' for {agent_id}: {e}")
        
        return tested_capabilities
    
    async def test_agent_tools(self, agent_id: str, agent_data: Dict) -> List[str]:
        """Test agent's declared tools."""
        tested_tools = []
        metadata = agent_data["metadata"]
        tools = metadata.get("tools", [])
        
        if isinstance(tools, list) and tools:
            for tool in tools[:2]:  # Test up to 2 tools
                tool_name = tool.get("name") if isinstance(tool, dict) else str(tool)
                
                # Skip tools that require external resources in test environment
                skip_tools = ["web_search", "email_send", "file_upload", "external_api"]
                if any(skip in tool_name.lower() for skip in skip_tools):
                    continue
                
                try:
                    test_message = f"Please use your {tool_name} tool to help me with a task"
                    
                    async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
                        response = await client.post(
                            "/api/v1/agents/conversation",
                            json={
                                "message": test_message,
                                "agent": agent_id,
                                "session_id": f"tool_test_{agent_id}_{TIMESTAMP}",
                                "context": {"tool_test": tool_name}
                            }
                        )
                        
                        if response.status_code == 200:
                            tested_tools.append(tool_name)
                            
                except Exception as e:
                    logger.warning(f"Failed to test tool '{tool_name}' for {agent_id}: {e}")
        
        return tested_tools
    
    def calculate_test_score(self, result: AgentTestResult) -> float:
        """Calculate overall test score for an agent (0-100)."""
        score = 0.0
        
        # Initialization (30 points)
        if result.initialization_success:
            score += 30
        
        # Response received (25 points)
        if result.response_received:
            score += 25
        
        # Response time (15 points)
        if result.response_time_ms < 5000:  # Under 5 seconds
            score += 15
        elif result.response_time_ms < 10000:  # Under 10 seconds
            score += 10
        elif result.response_time_ms < 20000:  # Under 20 seconds
            score += 5
        
        # Capabilities tested (15 points)
        if result.capabilities_tested:
            score += min(15, len(result.capabilities_tested) * 5)
        
        # Tools tested (10 points)
        if result.tools_tested:
            score += min(10, len(result.tools_tested) * 5)
        
        # Deduct for errors (5 points per error)
        score -= min(20, len(result.errors) * 5)
        
        return max(0, min(100, score))
    
    async def test_single_agent(self, agent_id: str, agent_data: Dict) -> AgentTestResult:
        """Test a single agent comprehensively."""
        logger.info(f"🧪 Testing agent: {agent_id}")
        
        metadata = agent_data["metadata"]
        errors = []
        warnings = []
        
        # Initialize result
        result = AgentTestResult(
            agent_id=agent_id,
            name=metadata.get("name", agent_id),
            role=metadata.get("role", "Unknown"),
            category=metadata.get("category", "Unknown"),
            tier=metadata.get("tier", "Unknown"),
            initialization_success=False,
            response_received=False,
            response_time_ms=0.0,
            capabilities_tested=[],
            tools_tested=[],
            errors=errors,
            warnings=warnings,
            test_score=0.0
        )
        
        try:
            # Test 1: Initialization
            result.initialization_success = await self.test_agent_initialization(agent_id, agent_data)
            
            # Test 2: Basic conversation
            response_success, response_time, response_content = await self.test_agent_conversation(agent_id, agent_data)
            result.response_received = response_success
            result.response_time_ms = response_time
            
            if not response_success:
                errors.append(f"Conversation failed: {response_content}")
            
            # Test 3: Capabilities (only if basic conversation works)
            if response_success:
                result.capabilities_tested = await self.test_agent_capabilities(agent_id, agent_data)
                
                # Test 4: Tools (only if basic conversation works)
                result.tools_tested = await self.test_agent_tools(agent_id, agent_data)
            
            # Calculate final score
            result.test_score = self.calculate_test_score(result)
            
            # Log result summary
            status = "✅" if result.test_score >= 70 else "⚠️" if result.test_score >= 50 else "❌"
            logger.info(f"  {status} {agent_id}: {result.test_score:.1f}/100 (Response: {response_time:.0f}ms)")
            
        except Exception as e:
            errors.append(f"Test execution failed: {e}")
            logger.error(f"  ❌ {agent_id}: Test failed - {e}")
        
        return result
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite for all agents."""
        logger.info("🚀 Starting Comprehensive Agent Test Suite")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Log file: {LOG_FILE}")
        logger.info("="*80)
        
        # Discover agents
        agents = await self.discover_agents()
        
        if not agents:
            logger.error("No agents discovered! Test suite cannot continue.")
            return {"error": "No agents found"}
        
        # Test each agent
        total_start = time.time()
        
        # Test agents in parallel (limit concurrency to avoid overwhelming system)
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent tests
        
        async def test_with_semaphore(agent_id: str, agent_data: Dict):
            async with semaphore:
                return await self.test_single_agent(agent_id, agent_data)
        
        tasks = [
            test_with_semaphore(agent_id, agent_data)
            for agent_id, agent_data in agents.items()
        ]
        
        self.test_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [r for r in self.test_results if isinstance(r, AgentTestResult)]
        exceptions = [r for r in self.test_results if isinstance(r, Exception)]
        
        total_time = time.time() - total_start
        
        # Generate summary
        summary = self.generate_test_summary(valid_results, total_time)
        
        # Log exceptions
        for exc in exceptions:
            logger.error(f"Test execution exception: {exc}")
        
        logger.info("="*80)
        logger.info("📊 TEST SUITE COMPLETED")
        logger.info(f"Total time: {total_time:.1f}s")
        logger.info(f"Results saved to: {LOG_FILE}")
        logger.info("="*80)
        
        return summary
    
    def generate_test_summary(self, results: List[AgentTestResult], total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        if not results:
            return {"error": "No valid test results"}
        
        # Calculate statistics
        total_agents = len(results)
        passed = len([r for r in results if r.test_score >= 70])
        warnings = len([r for r in results if 50 <= r.test_score < 70])
        failed = len([r for r in results if r.test_score < 50])
        
        avg_score = sum(r.test_score for r in results) / total_agents
        avg_response_time = sum(r.response_time_ms for r in results) / total_agents
        
        # Category breakdown
        categories = {}
        tiers = {}
        
        for result in results:
            # Category stats
            if result.category not in categories:
                categories[result.category] = {"count": 0, "avg_score": 0, "scores": []}
            categories[result.category]["count"] += 1
            categories[result.category]["scores"].append(result.test_score)
            
            # Tier stats
            if result.tier not in tiers:
                tiers[result.tier] = {"count": 0, "avg_score": 0, "scores": []}
            tiers[result.tier]["count"] += 1
            tiers[result.tier]["scores"].append(result.test_score)
        
        # Calculate averages
        for cat_data in categories.values():
            cat_data["avg_score"] = sum(cat_data["scores"]) / len(cat_data["scores"])
        
        for tier_data in tiers.values():
            tier_data["avg_score"] = sum(tier_data["scores"]) / len(tier_data["scores"])
        
        # Top and bottom performers
        sorted_results = sorted(results, key=lambda r: r.test_score, reverse=True)
        top_performers = sorted_results[:5]
        bottom_performers = sorted_results[-5:]
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_time_seconds": round(total_time, 2),
            "overview": {
                "total_agents": total_agents,
                "passed": passed,
                "warnings": warnings,
                "failed": failed,
                "success_rate": round((passed / total_agents) * 100, 1),
                "average_score": round(avg_score, 1),
                "average_response_time_ms": round(avg_response_time, 1)
            },
            "category_breakdown": {
                cat: {"count": data["count"], "avg_score": round(data["avg_score"], 1)}
                for cat, data in categories.items()
            },
            "tier_breakdown": {
                tier: {"count": data["count"], "avg_score": round(data["avg_score"], 1)}
                for tier, data in tiers.items()
            },
            "top_performers": [
                {
                    "agent_id": r.agent_id,
                    "name": r.name,
                    "score": r.test_score,
                    "response_time_ms": round(r.response_time_ms, 1)
                }
                for r in top_performers
            ],
            "bottom_performers": [
                {
                    "agent_id": r.agent_id,
                    "name": r.name,
                    "score": r.test_score,
                    "errors": len(r.errors)
                }
                for r in bottom_performers
            ],
            "detailed_results": [
                {
                    "agent_id": r.agent_id,
                    "name": r.name,
                    "role": r.role,
                    "category": r.category,
                    "tier": r.tier,
                    "test_score": r.test_score,
                    "initialization_success": r.initialization_success,
                    "response_received": r.response_received,
                    "response_time_ms": round(r.response_time_ms, 1),
                    "capabilities_tested": len(r.capabilities_tested),
                    "tools_tested": len(r.tools_tested),
                    "errors": r.errors,
                    "warnings": r.warnings
                }
                for r in results
            ]
        }
        
        # Save detailed results to JSON
        results_file = LOG_DIR / f"agent_test_results_{TIMESTAMP}.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"📋 Detailed results saved to: {results_file}")
        
        # Log summary
        logger.info(f"""\n📊 AGENT TEST SUMMARY
==================
Total Agents: {total_agents}
Passed (≥70): {passed} ({(passed/total_agents)*100:.1f}%)
Warnings (50-69): {warnings} ({(warnings/total_agents)*100:.1f}%)
Failed (<50): {failed} ({(failed/total_agents)*100:.1f}%)
Average Score: {avg_score:.1f}/100
Average Response Time: {avg_response_time:.0f}ms

Top Performers:
{chr(10).join(f'  • {r.name} ({r.agent_id}): {r.test_score:.1f}/100' for r in top_performers)}
""")
        
        return summary


# Pytest integration
class TestComprehensiveAgentSuite:
    """Pytest wrapper for the comprehensive agent test suite."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_all_agents_comprehensive(self):
        """Test all agents in the system comprehensively."""
        suite = ComprehensiveAgentTestSuite()
        results = await suite.run_comprehensive_test_suite()
        
        # Assert overall success
        assert "error" not in results, f"Test suite failed: {results.get('error')}"
        assert results["overview"]["total_agents"] > 0, "No agents tested"
        
        # Assert reasonable success rate (at least 70% of agents should work)
        success_rate = results["overview"]["success_rate"]
        assert success_rate >= 70, f"Success rate too low: {success_rate}% (expected ≥70%)"
        
        # Assert reasonable average score
        avg_score = results["overview"]["average_score"]
        assert avg_score >= 65, f"Average score too low: {avg_score}/100 (expected ≥65)"
        
        # Assert reasonable response times
        avg_response_time = results["overview"]["average_response_time_ms"]
        assert avg_response_time < 10000, f"Average response time too slow: {avg_response_time}ms (expected <10s)"


def run_agent_tests():
    """Execute the comprehensive agent test suite."""
    logger.info("Starting Convergio Comprehensive Agent Test Suite")
    
    # Configure pytest
    pytest_args = [
        __file__,
        "-v",
        "-s",
        "--tb=short",
        "--color=yes",
        "-m", "not slow or slow",  # Include slow tests
        f"--junit-xml={LOG_DIR}/agent_suite_{TIMESTAMP}_junit.xml"
    ]
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    # Report results
    logger.info("="*80)
    if exit_code == 0:
        logger.info("✅ ALL AGENT TESTS PASSED!")
    else:
        logger.error(f"❌ AGENT TESTS FAILED (exit code: {exit_code})")
    logger.info(f"Test results saved to: {LOG_FILE}")
    logger.info("="*80)
    
    return exit_code


if __name__ == "__main__":
    import sys
    # Run the test suite directly
    suite = ComprehensiveAgentTestSuite()
    
    async def main():
        return await suite.run_comprehensive_test_suite()
    
    results = asyncio.run(main())
    
    # Exit with appropriate code
    if "error" in results:
        sys.exit(1)
    elif results["overview"]["success_rate"] < 70:
        sys.exit(1)
    else:
        sys.exit(0)
