"""
End-to-End Streaming Test with Real Model
Validates streaming with tool events and collects performance metrics
"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
import websockets
from websockets.client import WebSocketClientProtocol
import structlog

from backend.src.agents.services.streaming.response_types import StreamingResponse
from backend.src.agents.services.streaming.protocol import (
    StreamingProtocol,
    StreamingEventType
)

logger = structlog.get_logger()


@dataclass
class StreamingMetrics:
    """Metrics collected during streaming session"""
    session_id: str
    first_token_latency_ms: Optional[int] = None
    total_duration_ms: Optional[int] = None
    total_chunks: int = 0
    text_chunks: int = 0
    tool_call_events: int = 0
    tool_result_events: int = 0
    handoff_events: int = 0
    error_events: int = 0
    heartbeat_events: int = 0
    
    # Detailed timings
    chunk_latencies: List[int] = field(default_factory=list)
    
    # Throughput
    tokens_per_second: Optional[float] = None
    chunks_per_second: Optional[float] = None
    
    # Tool event details
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    
    def calculate_metrics(self, total_tokens: int = 0):
        """Calculate derived metrics"""
        if self.chunk_latencies:
            # P50 and P95 latencies
            sorted_latencies = sorted(self.chunk_latencies)
            self.p50_latency_ms = sorted_latencies[len(sorted_latencies) // 2]
            self.p95_latency_ms = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            
        if self.total_duration_ms and self.total_duration_ms > 0:
            self.chunks_per_second = (self.total_chunks / self.total_duration_ms) * 1000
            if total_tokens > 0:
                self.tokens_per_second = (total_tokens / self.total_duration_ms) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StreamingE2ETest:
    """End-to-end streaming test harness"""
    
    def __init__(self, ws_url: str = ""):
        # Default to real API route if not provided
        self.ws_url = ws_url
        self.protocol = StreamingProtocol()
        
    async def run_streaming_session(
        self,
        message: str,
        agent_name: str = "ali_chief_of_staff",
        user_id: str = "test_user",
        include_tools: bool = True,
        timeout: int = 30
    ) -> StreamingMetrics:
        """Run a complete streaming session and collect metrics"""
        
        metrics = StreamingMetrics(session_id="")
        start_time = time.time()
        first_chunk_received = False
        
        # Build correct WS URL if not provided
        ws_url = self.ws_url or f"ws://localhost:9000/api/v1/agents/ws/streaming/{user_id}/{agent_name}"
        try:
            async with websockets.connect(ws_url) as websocket:
                # Send initial message
                init_message = {
                    "message": message,
                    "context": {
                        "include_tools": include_tools,
                        "test_mode": True
                    }
                }
                
                await websocket.send(json.dumps(init_message))
                logger.info(f"Sent initial message: {message[:50]}...")
                
                # Receive streaming responses
                async for raw_message in websocket:
                    try:
                        chunk_start = time.time()
                        frame = json.loads(raw_message)
                        # Parse streaming response according to protocol {type,event,data}
                        event, data = self.protocol.parse_frame(frame)
                        if isinstance(data, dict) and data.get("session_id"):
                            metrics.session_id = data.get("session_id")
                        
                        if event:
                            chunk_type = event
                            metrics.total_chunks += 1
                            
                            # Track first token latency
                            if not first_chunk_received and chunk_type in ["delta", "text"]:
                                metrics.first_token_latency_ms = int((chunk_start - start_time) * 1000)
                                first_chunk_received = True
                                logger.info(f"First token received in {metrics.first_token_latency_ms}ms")
                            
                            # Count event types
                            if chunk_type in ["delta", "text"]:
                                metrics.text_chunks += 1
                            elif chunk_type == "tool_call":
                                metrics.tool_call_events += 1
                                tool_info = {}
                                try:
                                    tool_info = json.loads(data.get("content", "{}")) if isinstance(data, dict) else {}
                                except Exception:
                                    tool_info = {}
                                metrics.tool_calls.append({
                                    "tool": (tool_info or {}).get("tool_name"),
                                    "args": (tool_info or {}).get("arguments"),
                                    "timestamp": chunk_start
                                })
                                logger.info(f"Tool call: {(tool_info or {}).get('tool_name')}")
                            elif chunk_type == "tool_result":
                                metrics.tool_result_events += 1
                                tool_res = {}
                                try:
                                    tool_res = json.loads(data.get("content", "{}")) if isinstance(data, dict) else {}
                                except Exception:
                                    tool_res = {}
                                metrics.tool_results.append({
                                    "tool": (tool_res or {}).get("tool_id"),
                                    "result": (tool_res or {}).get("result", "")[:100],
                                    "timestamp": chunk_start
                                })
                                logger.info(f"Tool result: {(tool_res or {}).get('tool_id')}")
                            elif chunk_type == "handoff":
                                metrics.handoff_events += 1
                                logger.info("Handoff event received")
                            elif chunk_type == "error":
                                metrics.error_events += 1
                                logger.error(f"Error event: {data}")
                            elif chunk_type == "heartbeat":
                                metrics.heartbeat_events += 1
                            elif chunk_type == "final":
                                # Session complete
                                logger.info("Received final chunk, session complete")
                                break
                            
                            # Track chunk latency
                            chunk_latency = int((time.time() - chunk_start) * 1000)
                            metrics.chunk_latencies.append(chunk_latency)
                        
                        # Check for completion
                        if frame.get("event") == "final" or (isinstance(data, dict) and data.get("chunk_type") == "final"):
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message: {e}")
                        metrics.error_events += 1
                    except Exception as e:
                        logger.error(f"Error processing chunk: {e}")
                        metrics.error_events += 1
                
                # Calculate total duration
                metrics.total_duration_ms = int((time.time() - start_time) * 1000)
                
                # Estimate tokens (rough approximation)
                estimated_tokens = metrics.text_chunks * 10  # Rough estimate
                metrics.calculate_metrics(estimated_tokens)
                
                logger.info(
                    f"Streaming session complete. Duration: {metrics.total_duration_ms}ms, "
                    f"Chunks: {metrics.total_chunks}, Tools: {metrics.tool_call_events}"
                )
                
        except asyncio.TimeoutError:
            logger.error(f"Streaming session timed out after {timeout}s")
            metrics.error_events += 1
        except Exception as e:
            logger.error(f"Streaming session failed: {e}")
            metrics.error_events += 1
        
        return metrics
    
    async def validate_streaming_events(self, metrics: StreamingMetrics) -> Dict[str, bool]:
        """Validate that streaming events meet expectations"""
        validations = {}
        
        # Basic streaming validation
        validations["session_created"] = bool(metrics.session_id)
        validations["received_chunks"] = metrics.total_chunks > 0
        validations["received_text"] = metrics.text_chunks > 0
        validations["no_errors"] = metrics.error_events == 0
        
        # Latency validation
        validations["first_token_fast"] = (
            metrics.first_token_latency_ms is not None and 
            metrics.first_token_latency_ms < 2000  # Under 2 seconds
        )
        
        # Tool event validation (if tools were expected)
        if metrics.tool_call_events > 0:
            validations["tool_calls_have_results"] = (
                metrics.tool_result_events >= metrics.tool_call_events
            )
            validations["tool_sequence_valid"] = self._validate_tool_sequence(metrics)
        
        # Performance validation
        if hasattr(metrics, "p50_latency_ms"):
            validations["p50_latency_acceptable"] = metrics.p50_latency_ms < 100
            validations["p95_latency_acceptable"] = metrics.p95_latency_ms < 500
        
        if metrics.chunks_per_second:
            validations["throughput_acceptable"] = metrics.chunks_per_second > 5
        
        return validations
    
    def _validate_tool_sequence(self, metrics: StreamingMetrics) -> bool:
        """Validate that tool calls and results follow correct sequence"""
        # Each tool call should have a corresponding result
        tool_call_names = [tc["tool"] for tc in metrics.tool_calls]
        tool_result_names = [tr["tool"] for tr in metrics.tool_results]
        
        # Check that each call has a result
        for call_name in tool_call_names:
            if call_name not in tool_result_names:
                return False
        
        # Check temporal ordering (calls before results)
        for call in metrics.tool_calls:
            call_time = call["timestamp"]
            # Find corresponding result
            for result in metrics.tool_results:
                if result["tool"] == call["tool"]:
                    if result["timestamp"] < call_time:
                        return False  # Result came before call
                    break
        
        return True
    
    async def run_performance_test(
        self,
        num_sessions: int = 10,
        concurrent: bool = False
    ) -> Dict[str, Any]:
        """Run multiple sessions to collect performance statistics"""
        
        test_messages = [
            "What's our current revenue and how can we improve it?",
            "Analyze our customer churn and provide recommendations",
            "Create a strategic plan for Q2 expansion",
            "Review our security posture and identify risks",
            "Optimize our workflow processes for efficiency"
        ]
        
        all_metrics: List[StreamingMetrics] = []
        
        if concurrent:
            # Run sessions concurrently
            tasks = []
            for i in range(num_sessions):
                message = test_messages[i % len(test_messages)]
                tasks.append(self.run_streaming_session(
                    message=message,
                    user_id=f"perf_test_user_{i}"
                ))
            
            all_metrics = await asyncio.gather(*tasks)
        else:
            # Run sessions sequentially
            for i in range(num_sessions):
                message = test_messages[i % len(test_messages)]
                metrics = await self.run_streaming_session(
                    message=message,
                    user_id=f"perf_test_user_{i}"
                )
                all_metrics.append(metrics)
                await asyncio.sleep(1)  # Small delay between sessions
        
        # Aggregate statistics
        stats = self._calculate_aggregate_stats(all_metrics)
        
        return {
            "total_sessions": num_sessions,
            "successful_sessions": sum(1 for m in all_metrics if m.error_events == 0),
            "aggregate_stats": stats,
            "individual_metrics": [m.to_dict() for m in all_metrics]
        }
    
    def _calculate_aggregate_stats(self, metrics_list: List[StreamingMetrics]) -> Dict[str, Any]:
        """Calculate aggregate statistics from multiple sessions"""
        
        if not metrics_list:
            return {}
        
        # Filter successful sessions
        successful = [m for m in metrics_list if m.error_events == 0]
        
        if not successful:
            return {"error": "No successful sessions"}
        
        stats = {
            "avg_first_token_latency_ms": sum(
                m.first_token_latency_ms for m in successful 
                if m.first_token_latency_ms
            ) / len(successful),
            
            "avg_total_duration_ms": sum(
                m.total_duration_ms for m in successful
                if m.total_duration_ms
            ) / len(successful),
            
            "avg_chunks_per_session": sum(m.total_chunks for m in successful) / len(successful),
            
            "tool_usage_rate": sum(
                1 for m in successful if m.tool_call_events > 0
            ) / len(successful),
            
            "avg_tool_calls_per_session": sum(
                m.tool_call_events for m in successful
            ) / len(successful),
            
            "error_rate": (len(metrics_list) - len(successful)) / len(metrics_list),
        }
        
        # Calculate percentiles across all sessions
        all_first_token_latencies = [
            m.first_token_latency_ms for m in successful 
            if m.first_token_latency_ms
        ]
        if all_first_token_latencies:
            sorted_latencies = sorted(all_first_token_latencies)
            stats["p50_first_token_ms"] = sorted_latencies[len(sorted_latencies) // 2]
            stats["p95_first_token_ms"] = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        
        return stats


@pytest.mark.asyncio
class TestStreamingE2E:
    """End-to-end streaming tests"""
    
    @pytest.fixture
    def test_harness(self):
        """Create test harness"""
        return StreamingE2ETest()
    
    @pytest.mark.asyncio
    async def test_basic_streaming_flow(self, test_harness):
        """Test basic streaming flow with text chunks"""
        # Run streaming session
        metrics = await test_harness.run_streaming_session(
            message="Hello, can you help me understand our Q1 performance?",
            include_tools=False
        )
        
        # Validate results
        validations = await test_harness.validate_streaming_events(metrics)
        
        assert validations["session_created"], "Session should be created"
        assert validations["received_chunks"], "Should receive chunks"
        assert validations["received_text"], "Should receive text chunks"
        assert validations["no_errors"], "Should have no errors"
        assert validations["first_token_fast"], "First token should arrive quickly"
    
    @pytest.mark.asyncio
    async def test_streaming_with_tools(self, test_harness):
        """Test streaming with tool call and result events"""
        # Run session that triggers tools
        metrics = await test_harness.run_streaming_session(
            message="Analyze our customer data and revenue metrics for Q1",
            include_tools=True
        )
        
        # Validate results
        validations = await test_harness.validate_streaming_events(metrics)
        
        assert validations["session_created"], "Session should be created"
        assert metrics.tool_call_events > 0, "Should have tool calls"
        assert metrics.tool_result_events > 0, "Should have tool results"
        assert validations.get("tool_calls_have_results", False), "Each tool call should have a result"
        assert validations.get("tool_sequence_valid", False), "Tool sequence should be valid"
    
    @pytest.mark.asyncio
    async def test_streaming_with_handoff(self, test_harness):
        """Test streaming with agent handoff events"""
        # Run session that triggers handoff
        metrics = await test_harness.run_streaming_session(
            message="I need financial analysis and then security review of our cloud infrastructure",
            agent_name="ali_chief_of_staff"
        )
        
        # Check for handoff events
        assert metrics.handoff_events > 0, "Should have handoff events between agents"
    
    @pytest.mark.asyncio
    async def test_streaming_performance(self, test_harness):
        """Test streaming performance metrics"""
        # Run performance test
        results = await test_harness.run_performance_test(
            num_sessions=5,
            concurrent=False
        )
        
        stats = results["aggregate_stats"]
        
        # Validate performance metrics
        assert results["successful_sessions"] >= 4, "At least 80% sessions should succeed"
        assert stats["avg_first_token_latency_ms"] < 2000, "Average first token should be under 2s"
        assert stats["p95_first_token_ms"] < 3000, "P95 first token should be under 3s"
        assert stats["error_rate"] < 0.2, "Error rate should be under 20%"
    
    @pytest.mark.asyncio
    async def test_concurrent_streaming(self, test_harness):
        """Test concurrent streaming sessions"""
        # Run concurrent sessions
        results = await test_harness.run_performance_test(
            num_sessions=3,
            concurrent=True
        )
        
        # Validate concurrent execution
        assert results["total_sessions"] == 3
        assert results["successful_sessions"] >= 2, "Most concurrent sessions should succeed"
    
    @pytest.mark.asyncio
    async def test_streaming_error_handling(self, test_harness):
        """Test streaming error handling"""
        # Send invalid message to trigger error
        metrics = await test_harness.run_streaming_session(
            message="",  # Empty message
            agent_name="invalid_agent"
        )
        
        # Should handle error gracefully
        assert metrics.error_events > 0, "Should have error events"
        assert metrics.session_id or metrics.total_chunks > 0, "Should still create session or send error chunk"
    
    @pytest.mark.asyncio
    async def test_streaming_heartbeat(self, test_harness):
        """Test heartbeat mechanism during streaming"""
        # Run longer session to trigger heartbeats
        metrics = await test_harness.run_streaming_session(
            message="Provide a detailed analysis of our entire business strategy including market position, competitive analysis, financial projections, and risk assessment",
            timeout=60
        )
        
        # Should receive heartbeat events for long-running session
        if metrics.total_duration_ms > 15000:  # If session took more than 15 seconds
            assert metrics.heartbeat_events > 0, "Should receive heartbeat events"


async def main():
    """Run E2E streaming tests and generate report"""
    
    print("\n" + "="*60)
    print("E2E STREAMING TEST SUITE")
    print("="*60)
    
    harness = StreamingE2ETest()
    
    # Run basic test
    print("\n1. Testing basic streaming...")
    basic_metrics = await harness.run_streaming_session(
        message="What's our revenue forecast for next quarter?",
        include_tools=False
    )
    basic_valid = await harness.validate_streaming_events(basic_metrics)
    print(f"   ✅ Basic streaming: {sum(basic_valid.values())}/{len(basic_valid)} checks passed")
    
    # Run tool test
    print("\n2. Testing streaming with tools...")
    tool_metrics = await harness.run_streaming_session(
        message="Analyze our customer metrics and financial data",
        include_tools=True
    )
    tool_valid = await harness.validate_streaming_events(tool_metrics)
    print(f"   ✅ Tool streaming: {sum(tool_valid.values())}/{len(tool_valid)} checks passed")
    
    # Run performance test
    print("\n3. Running performance test...")
    perf_results = await harness.run_performance_test(num_sessions=5)
    stats = perf_results["aggregate_stats"]
    
    print(f"\n   Performance Results:")
    print(f"   - Success rate: {perf_results['successful_sessions']}/{perf_results['total_sessions']}")
    print(f"   - Avg first token: {stats.get('avg_first_token_latency_ms', 0):.0f}ms")
    print(f"   - P50 first token: {stats.get('p50_first_token_ms', 0):.0f}ms")
    print(f"   - P95 first token: {stats.get('p95_first_token_ms', 0):.0f}ms")
    print(f"   - Avg duration: {stats.get('avg_total_duration_ms', 0):.0f}ms")
    print(f"   - Tool usage rate: {stats.get('tool_usage_rate', 0):.1%}")
    
    # Save results
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "basic_test": basic_metrics.to_dict(),
        "tool_test": tool_metrics.to_dict(),
        "performance_test": perf_results,
        "validations": {
            "basic": basic_valid,
            "tools": tool_valid
        }
    }
    
    with open("streaming_e2e_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to streaming_e2e_results.json")
    print("="*60)
    
    # Check if tests passed
    all_passed = (
        sum(basic_valid.values()) == len(basic_valid) and
        sum(tool_valid.values()) == len(tool_valid) and
        perf_results["successful_sessions"] >= perf_results["total_sessions"] * 0.8
    )
    
    if all_passed:
        print("✅ ALL E2E STREAMING TESTS PASSED")
    else:
        print("❌ SOME E2E STREAMING TESTS FAILED")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
