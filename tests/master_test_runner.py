#!/usr/bin/env python3
"""
🗡️ CONVERGIO MASTER TEST RUNNER
================================

Purpose: Unified test execution and orchestration for the complete Convergio test suite:
- Comprehensive agent testing (48 agents)
- Multi-agent workflow validation
- Ali proactive intelligence testing
- AutoGen 0.7.2 integration tests
- Database and cost tracking validation
- Security validation suite
- Performance and load testing
- Report generation and analysis

Author: Convergio Test Suite
Last Updated: August 2025
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
MASTER_LOG_FILE = LOG_DIR / f"master_test_runner_{TIMESTAMP}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(MASTER_LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TestSuiteResult:
    """Result of a test suite execution."""
    suite_name: str
    success: bool
    duration_seconds: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    exit_code: int
    log_file: str
    report_file: Optional[str]
    errors: List[str]
    summary: Dict[str, Any]


class MasterTestRunner:
    """
    Master test runner for orchestrating all Convergio test suites.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self.load_default_config()
        self.results: List[TestSuiteResult] = []
        self.start_time = None
        self.end_time = None
        
        # Test suite definitions
        self.test_suites = {
            "agents": {
                "name": "Comprehensive Agent Suite",
                "module": "tests.e2e.test_comprehensive_agent_suite",
                "timeout": 1800,  # 30 minutes
                "critical": True,
                "description": "Test all 48 agents and their capabilities"
            },
            "workflows": {
                "name": "Multi-Agent Workflows",
                "module": "tests.e2e.test_multiagent_workflows",
                "timeout": 1200,  # 20 minutes
                "critical": True,
                "description": "Test complex multi-agent conversation workflows"
            },
            "ali_proactive": {
                "name": "Ali Proactive Intelligence",
                "module": "tests.e2e.test_ali_proactive_intelligence",
                "timeout": 900,  # 15 minutes
                "critical": True,
                "description": "Test Ali's proactive intelligence features"
            },
            "autogen": {
                "name": "AutoGen 0.7.2 Integration",
                "module": "tests.e2e.test_autogen_integration",
                "timeout": 1500,  # 25 minutes
                "critical": True,
                "description": "Test AutoGen framework integration"
            },
            "database_cost": {
                "name": "Database & Cost Tracking",
                "module": "tests.e2e.test_database_cost_tracking",
                "timeout": 600,  # 10 minutes
                "critical": True,
                "description": "Test database operations and cost tracking"
            },
            "security": {
                "name": "Security Validation",
                "module": "tests.e2e.test_security_validation",
                "timeout": 900,  # 15 minutes
                "critical": True,
                "description": "Test security controls and vulnerability detection"
            },
            "e2e_basic": {
                "name": "Basic End-to-End",
                "module": "tests.e2e.test_end_to_end",
                "timeout": 600,  # 10 minutes
                "critical": False,
                "description": "Basic end-to-end user journey tests"
            }
        }
    
    def load_default_config(self) -> Dict[str, Any]:
        """Load default test runner configuration."""
        return {
            "parallel_execution": True,
            "max_parallel_suites": 3,
            "continue_on_failure": True,
            "generate_reports": True,
            "cleanup_logs": False,
            "timeout_seconds": 3600,  # 1 hour total
            "retry_failed_tests": True,
            "max_retries": 1,
            "environment_checks": True,
            "performance_monitoring": True
        }
    
    async def check_environment(self) -> bool:
        """Check if the test environment is ready."""
        logger.info("🔍 Checking test environment...")
        
        checks = {
            "Backend API": self.check_backend_api,
            "Database": self.check_database,
            "Redis": self.check_redis,
            "Python Environment": self.check_python_env
        }
        
        all_passed = True
        for check_name, check_func in checks.items():
            try:
                if await check_func():
                    logger.info(f"  ✅ {check_name}: Ready")
                else:
                    logger.error(f"  ❌ {check_name}: Failed")
                    all_passed = False
            except Exception as e:
                logger.error(f"  ❌ {check_name}: Error - {e}")
                all_passed = False
        
        return all_passed
    
    async def check_backend_api(self) -> bool:
        """Check if backend API is accessible."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:9000/health")
                return response.status_code == 200
        except Exception:
            return False
    
    async def check_database(self) -> bool:
        """Check if database is accessible."""
        try:
            # Add backend to path for imports
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
            from src.core.database import get_db_session
            
            async for db in get_db_session():
                result = await db.execute("SELECT 1")
                return result.scalar() == 1
        except Exception:
            return False
    
    async def check_redis(self) -> bool:
        """Check if Redis is accessible."""
        try:
            import redis.asyncio as redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            await r.ping()
            await r.aclose()
            return True
        except Exception:
            return False
    
    async def check_python_env(self) -> bool:
        """Check if required Python packages are available."""
        required_packages = [
            "pytest", "httpx", "asyncio", "sqlalchemy", "redis",
            "pydantic", "fastapi", "uvicorn"
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                logger.error(f"Missing required package: {package}")
                return False
        
        return True
    
    def run_test_suite(self, suite_key: str, suite_config: Dict[str, Any]) -> TestSuiteResult:
        """Run a single test suite."""
        logger.info(f"🏃 Starting {suite_config['name']}...")
        
        start_time = time.time()
        suite_log_file = LOG_DIR / f"{suite_key}_{TIMESTAMP}.log"
        
        try:
            # Prepare command
            cmd = [
                sys.executable, "-m", "pytest",
                "-v", "-s",
                "--tb=short",
                "--color=yes",
                "--maxfail=5",
                f"--timeout={suite_config['timeout']}",
                f"--junit-xml={LOG_DIR}/{suite_key}_{TIMESTAMP}_junit.xml",
                f"--log-file={suite_log_file}",
                f"tests/e2e/{suite_key.replace('_', '_')}.py"
            ]
            
            # Handle special module paths
            if suite_key == "agents":
                cmd[-1] = "tests/e2e/test_comprehensive_agent_suite.py"
            elif suite_key == "ali_proactive":
                cmd[-1] = "tests/e2e/test_ali_proactive_intelligence.py"
            elif suite_key == "database_cost":
                cmd[-1] = "tests/e2e/test_database_cost_tracking.py"
            elif suite_key == "e2e_basic":
                cmd[-1] = "tests/e2e/test_end_to_end.py"
            
            # Set environment variables
            env = os.environ.copy()
            env["PYTEST_CURRENT_TEST"] = suite_key
            env["TEST_SUITE"] = suite_config['name']
            
            # Run the test suite
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=suite_config['timeout'],
                env=env,
                cwd=Path(__file__).resolve().parents[1]
            )
            
            duration = time.time() - start_time
            
            # Parse test results from output
            total_tests, passed_tests, failed_tests = self.parse_pytest_output(result.stdout)
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Look for JSON report file
            report_file = None
            possible_reports = [
                LOG_DIR / f"{suite_key}_test_results_{TIMESTAMP}.json",
                LOG_DIR / f"{suite_key.replace('_', '_')}_test_results_{TIMESTAMP}.json"
            ]
            
            for report_path in possible_reports:
                if report_path.exists():
                    report_file = str(report_path)
                    break
            
            # Collect errors
            errors = []
            if result.returncode != 0:
                errors.append(f"Exit code: {result.returncode}")
            if result.stderr:
                errors.extend(result.stderr.split('\n')[:5])  # First 5 error lines
            
            # Create summary
            summary = {
                "suite_name": suite_config['name'],
                "duration_seconds": duration,
                "exit_code": result.returncode,
                "stdout_lines": len(result.stdout.split('\n')),
                "stderr_lines": len(result.stderr.split('\n')),
                "command": ' '.join(cmd)
            }
            
            test_result = TestSuiteResult(
                suite_name=suite_config['name'],
                success=result.returncode == 0,
                duration_seconds=duration,
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                success_rate=success_rate,
                exit_code=result.returncode,
                log_file=str(suite_log_file),
                report_file=report_file,
                errors=errors,
                summary=summary
            )
            
            status = "✅" if test_result.success else "❌"
            logger.info(f"  {status} {suite_config['name']}: {passed_tests}/{total_tests} tests passed ({duration:.1f}s)")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"  ⏰ {suite_config['name']}: Timeout after {duration:.1f}s")
            
            return TestSuiteResult(
                suite_name=suite_config['name'],
                success=False,
                duration_seconds=duration,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                success_rate=0,
                exit_code=-1,
                log_file=str(suite_log_file),
                report_file=None,
                errors=[f"Timeout after {suite_config['timeout']} seconds"],
                summary={"timeout": True}
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"  ❌ {suite_config['name']}: Exception - {e}")
            
            return TestSuiteResult(
                suite_name=suite_config['name'],
                success=False,
                duration_seconds=duration,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                success_rate=0,
                exit_code=-2,
                log_file=str(suite_log_file),
                report_file=None,
                errors=[str(e)],
                summary={"exception": str(e)}
            )
    
    def parse_pytest_output(self, output: str) -> Tuple[int, int, int]:
        """Parse pytest output to extract test counts."""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        # Look for pytest summary line
        lines = output.split('\n')
        for line in lines:
            if 'passed' in line or 'failed' in line or 'error' in line:
                if '::' not in line:  # Avoid test function lines
                    # Try to extract numbers
                    words = line.split()
                    for i, word in enumerate(words):
                        if word == 'passed' and i > 0:
                            try:
                                passed_tests = int(words[i-1])
                            except ValueError:
                                pass
                        elif word == 'failed' and i > 0:
                            try:
                                failed_tests = int(words[i-1])
                            except ValueError:
                                pass
        
        total_tests = passed_tests + failed_tests
        
        # Fallback: count test function calls
        if total_tests == 0:
            test_lines = [line for line in lines if '::test_' in line and ('PASSED' in line or 'FAILED' in line)]
            total_tests = len(test_lines)
            passed_tests = len([line for line in test_lines if 'PASSED' in line])
            failed_tests = len([line for line in test_lines if 'FAILED' in line])
        
        return total_tests, passed_tests, failed_tests
    
    async def run_all_suites(self) -> Dict[str, Any]:
        """Run all test suites according to configuration."""
        logger.info("🚀 Starting Convergio Master Test Suite")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Configuration: {self.config}")
        logger.info(f"Master log: {MASTER_LOG_FILE}")
        logger.info("="*100)
        
        self.start_time = time.time()
        
        # Environment checks
        if self.config.get("environment_checks", True):
            if not await self.check_environment():
                logger.error("❌ Environment checks failed. Aborting test run.")
                return {"error": "Environment checks failed"}
        
        # Determine execution strategy
        if self.config.get("parallel_execution", True):
            await self.run_suites_parallel()
        else:
            await self.run_suites_sequential()
        
        self.end_time = time.time()
        
        # Generate final report
        final_report = self.generate_final_report()
        
        logger.info("="*100)
        logger.info("📊 CONVERGIO MASTER TEST SUITE COMPLETED")
        logger.info(f"Total time: {self.end_time - self.start_time:.1f}s")
        logger.info(f"Final report: {final_report.get('report_file', 'Not generated')}")
        logger.info("="*100)
        
        return final_report
    
    async def run_suites_parallel(self):
        """Run test suites in parallel."""
        logger.info(f"🔀 Running {len(self.test_suites)} test suites in parallel...")
        
        max_workers = min(self.config.get("max_parallel_suites", 3), len(self.test_suites))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_suite = {
                executor.submit(self.run_test_suite, suite_key, suite_config): suite_key
                for suite_key, suite_config in self.test_suites.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_suite):
                suite_key = future_to_suite[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    
                    # Check if we should continue on critical failure
                    if not result.success and self.test_suites[suite_key].get("critical", False):
                        if not self.config.get("continue_on_failure", True):
                            logger.error(f"❌ Critical test suite failed: {result.suite_name}. Stopping execution.")
                            # Cancel remaining futures
                            for remaining_future in future_to_suite:
                                remaining_future.cancel()
                            break
                            
                except Exception as e:
                    logger.error(f"❌ Exception in {suite_key}: {e}")
                    # Create failed result
                    failed_result = TestSuiteResult(
                        suite_name=self.test_suites[suite_key]['name'],
                        success=False,
                        duration_seconds=0,
                        total_tests=0,
                        passed_tests=0,
                        failed_tests=0,
                        success_rate=0,
                        exit_code=-3,
                        log_file="",
                        report_file=None,
                        errors=[str(e)],
                        summary={"executor_exception": str(e)}
                    )
                    self.results.append(failed_result)
    
    async def run_suites_sequential(self):
        """Run test suites sequentially."""
        logger.info(f"🔄 Running {len(self.test_suites)} test suites sequentially...")
        
        for suite_key, suite_config in self.test_suites.items():
            result = self.run_test_suite(suite_key, suite_config)
            self.results.append(result)
            
            # Check if we should continue on critical failure
            if not result.success and suite_config.get("critical", False):
                if not self.config.get("continue_on_failure", True):
                    logger.error(f"❌ Critical test suite failed: {result.suite_name}. Stopping execution.")
                    break
            
            # Brief pause between suites
            await asyncio.sleep(2)
    
    def retry_failed_tests(self):
        """Retry failed test suites if configured."""
        if not self.config.get("retry_failed_tests", True):
            return
        
        max_retries = self.config.get("max_retries", 1)
        failed_results = [r for r in self.results if not r.success]
        
        if not failed_results:
            return
        
        logger.info(f"🔁 Retrying {len(failed_results)} failed test suites (max {max_retries} retries)...")
        
        for retry_attempt in range(max_retries):
            retry_results = []
            
            for failed_result in failed_results:
                # Find the original suite config
                suite_key = None
                for key, config in self.test_suites.items():
                    if config['name'] == failed_result.suite_name:
                        suite_key = key
                        break
                
                if suite_key:
                    logger.info(f"  🔄 Retry {retry_attempt + 1}/{max_retries}: {failed_result.suite_name}")
                    retry_result = self.run_test_suite(suite_key, self.test_suites[suite_key])
                    retry_results.append(retry_result)
                    
                    # Update original result if retry succeeded
                    if retry_result.success:
                        # Replace the failed result
                        for i, original_result in enumerate(self.results):
                            if original_result.suite_name == failed_result.suite_name:
                                self.results[i] = retry_result
                                break
            
            # Update failed results list for next retry
            failed_results = [r for r in retry_results if not r.success]
            if not failed_results:
                logger.info("  ✅ All retries successful!")
                break
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report."""
        if not self.config.get("generate_reports", True):
            return {"report_generation": "disabled"}
        
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        total_tests = sum(r.total_tests for r in self.results)
        total_passed = sum(r.passed_tests for r in self.results)
        total_failed = sum(r.failed_tests for r in self.results)
        successful_suites = len([r for r in self.results if r.success])
        
        # Calculate overall success rate
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        suite_success_rate = (successful_suites / len(self.results) * 100) if self.results else 0
        
        # Collect all individual test results
        individual_reports = []
        for result in self.results:
            if result.report_file and Path(result.report_file).exists():
                try:
                    with open(result.report_file, 'r') as f:
                        report_data = json.load(f)
                    individual_reports.append({
                        "suite_name": result.suite_name,
                        "report_data": report_data
                    })
                except Exception as e:
                    logger.warning(f"Could not load report for {result.suite_name}: {e}")
        
        # Generate executive summary
        executive_summary = {
            "test_execution_timestamp": datetime.now().isoformat(),
            "total_duration_seconds": round(total_duration, 2),
            "environment": "test",
            "test_suites_executed": len(self.results),
            "test_suites_successful": successful_suites,
            "suite_success_rate": round(suite_success_rate, 1),
            "total_tests_executed": total_tests,
            "total_tests_passed": total_passed,
            "total_tests_failed": total_failed,
            "overall_success_rate": round(overall_success_rate, 1),
            "critical_failures": len([r for r in self.results if not r.success and 
                                    any(self.test_suites[k].get('critical', False) for k in self.test_suites 
                                        if self.test_suites[k]['name'] == r.suite_name)])
        }
        
        # Generate suite-by-suite breakdown
        suite_breakdown = []
        for result in self.results:
            suite_info = {
                "suite_name": result.suite_name,
                "success": result.success,
                "duration_seconds": round(result.duration_seconds, 2),
                "total_tests": result.total_tests,
                "passed_tests": result.passed_tests,
                "failed_tests": result.failed_tests,
                "success_rate": round(result.success_rate, 1),
                "exit_code": result.exit_code,
                "error_count": len(result.errors),
                "log_file": result.log_file,
                "report_file": result.report_file
            }
            suite_breakdown.append(suite_info)
        
        # Generate recommendations
        recommendations = self.generate_recommendations()
        
        # Compile final report
        final_report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "Convergio Master Test Runner",
                "version": "1.0.0",
                "report_type": "comprehensive_test_execution"
            },
            "executive_summary": executive_summary,
            "suite_breakdown": suite_breakdown,
            "performance_metrics": {
                "average_suite_duration": round(total_duration / len(self.results), 2) if self.results else 0,
                "fastest_suite": min(self.results, key=lambda r: r.duration_seconds).suite_name if self.results else None,
                "slowest_suite": max(self.results, key=lambda r: r.duration_seconds).suite_name if self.results else None,
                "total_test_throughput": round(total_tests / total_duration, 2) if total_duration > 0 else 0
            },
            "recommendations": recommendations,
            "individual_suite_reports": individual_reports,
            "detailed_results": [
                {
                    "suite_name": r.suite_name,
                    "success": r.success,
                    "duration_seconds": r.duration_seconds,
                    "total_tests": r.total_tests,
                    "passed_tests": r.passed_tests,
                    "failed_tests": r.failed_tests,
                    "success_rate": r.success_rate,
                    "exit_code": r.exit_code,
                    "log_file": r.log_file,
                    "report_file": r.report_file,
                    "errors": r.errors,
                    "summary": r.summary
                }
                for r in self.results
            ]
        }
        
        # Save final report
        report_file = LOG_DIR / f"convergio_master_test_report_{TIMESTAMP}.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        final_report["report_file"] = str(report_file)
        
        # Generate summary log
        self.log_final_summary(final_report)
        
        return final_report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        failed_results = [r for r in self.results if not r.success]
        
        if failed_results:
            recommendations.append(f"Investigate and fix {len(failed_results)} failed test suites")
            
            # Specific recommendations based on failed suites
            for result in failed_results:
                if "timeout" in result.summary:
                    recommendations.append(f"Increase timeout for {result.suite_name} or optimize performance")
                elif result.exit_code == -1:
                    recommendations.append(f"Debug timeout issues in {result.suite_name}")
                elif "Security" in result.suite_name:
                    recommendations.append("Priority: Address security test failures immediately")
                elif "Agent" in result.suite_name:
                    recommendations.append("Review agent configurations and capabilities")
        
        # Performance recommendations
        slow_suites = [r for r in self.results if r.duration_seconds > 900]  # > 15 minutes
        if slow_suites:
            recommendations.append(f"Optimize performance for slow test suites: {', '.join(r.suite_name for r in slow_suites)}")
        
        # Coverage recommendations
        total_tests = sum(r.total_tests for r in self.results)
        if total_tests < 100:
            recommendations.append("Consider expanding test coverage - current test count seems low")
        
        # Success rate recommendations
        overall_success_rate = (sum(r.passed_tests for r in self.results) / total_tests * 100) if total_tests > 0 else 0
        if overall_success_rate < 95:
            recommendations.append("Aim for >95% test success rate - investigate failing tests")
        
        return recommendations
    
    def log_final_summary(self, report: Dict[str, Any]):
        """Log a comprehensive final summary."""
        summary = report["executive_summary"]
        breakdown = report["suite_breakdown"]
        
        logger.info(f"""\n📊 CONVERGIO TEST EXECUTION SUMMARY
========================================
Execution Time: {summary['total_duration_seconds']}s
Suites Executed: {summary['test_suites_executed']}
Suites Successful: {summary['test_suites_successful']} ({summary['suite_success_rate']}%)
Total Tests: {summary['total_tests_executed']}
Tests Passed: {summary['total_tests_passed']} ({summary['overall_success_rate']}%)
Tests Failed: {summary['total_tests_failed']}
Critical Failures: {summary['critical_failures']}

Suite Results:
{chr(10).join(f'  • {s["suite_name"]}: {s["passed_tests"]}/{s["total_tests"]} tests ({"✅" if s["success"] else "❌"})' for s in breakdown)}

Recommendations:
{chr(10).join(f'  • {rec}' for rec in report['recommendations'])}

Report saved to: {report.get('report_file', 'Not generated')}
""")


def main():
    """Main entry point for the master test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Convergio Master Test Runner")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--parallel", action="store_true", default=True, help="Run tests in parallel")
    parser.add_argument("--no-parallel", action="store_false", dest="parallel", help="Run tests sequentially")
    parser.add_argument("--continue-on-failure", action="store_true", default=True, help="Continue on test failures")
    parser.add_argument("--no-env-check", action="store_false", dest="env_check", default=True, help="Skip environment checks")
    parser.add_argument("--timeout", type=int, default=3600, help="Total timeout in seconds")
    parser.add_argument("--max-workers", type=int, default=3, help="Maximum parallel workers")
    parser.add_argument("--retry", action="store_true", default=True, help="Retry failed tests")
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Override with command line arguments
    config.update({
        "parallel_execution": args.parallel,
        "continue_on_failure": args.continue_on_failure,
        "environment_checks": args.env_check,
        "timeout_seconds": args.timeout,
        "max_parallel_suites": args.max_workers,
        "retry_failed_tests": args.retry
    })
    
    # Create and run master test runner
    runner = MasterTestRunner(config)
    
    try:
        # Run the test suite
        final_report = asyncio.run(runner.run_all_suites())
        
        # Determine exit code
        if "error" in final_report:
            sys.exit(1)
        elif final_report["executive_summary"]["critical_failures"] > 0:
            sys.exit(1)
        elif final_report["executive_summary"]["overall_success_rate"] < 80:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.error("⚠️ Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Fatal error in master test runner: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
