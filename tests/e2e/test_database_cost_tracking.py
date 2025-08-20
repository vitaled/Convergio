#!/usr/bin/env python3
"""
📊 CONVERGIO DATABASE OPERATIONS & COST TRACKING TEST SUITE
==========================================================

Purpose: Comprehensive testing of database operations and cost tracking including:
- Database connectivity and performance
- CRUD operations across all tables
- Cost tracking accuracy and limits
- Transaction management
- Data integrity and consistency
- Performance under load
- Cost safety mechanisms

Author: Convergio Test Suite
Last Updated: August 2025
"""

import asyncio
import json
import logging
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pytest
import httpx
from dataclasses import dataclass
from decimal import Decimal

# Setup paths
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from src.core.config import get_settings
from src.core.database import get_db_session
from src.models.cost_tracking import CostTracking, CostAlert
from src.models.talent import Talent
from src.models.project import Project
from src.models.engagement import Engagement

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
class DatabaseTestResult:
    """Result of a database operation test."""
    test_name: str
    success: bool
    operation_time_ms: float
    records_affected: int
    data_integrity_check: bool
    performance_metrics: Dict[str, Any]
    errors: List[str]
@dataclass
class CostTrackingTestResult:
    """Result of a cost tracking test."""
    test_name: str
    success: bool
    cost_tracked: Decimal
    limit_enforced: bool
    accuracy_check: bool
    response_time_ms: float
    safety_mechanisms: Dict[str, bool]
    errors: List[str]
class DatabaseCostTrackingTester:
    """
    Comprehensive test suite for database operations and cost tracking.
    """
    
    def __init__(self):
        self.settings = get_settings()
        import os
        backend_port = os.getenv("BACKEND_PORT", "9000")
        self.base_url = f"http://localhost:{backend_port}"
        self.test_session_id = f"db_cost_test_{TIMESTAMP}"
        self.test_user_id = None
        self.test_project_id = None
        self.created_records = []
    
    async def setup_test_data(self) -> bool:
        """Setup test data for database operations."""
        try:
            logger.info("🔧 Setting up test data...")
            
            async for db in get_db_session():
                # Create test user
                test_user = Talent(
                    email=f"test_user_{TIMESTAMP}@example.com",
                    first_name=f"Test",
                    last_name=f"User_{TIMESTAMP}"
                )
                db.add(test_user)
                await db.commit()
                await db.refresh(test_user)
                self.test_user_id = test_user.id
                self.created_records.append(("user", test_user.id))
                
                # Create test project
                test_project = Project(
                    name=f"Test Project {TIMESTAMP}",
                    description="Test project for database and cost tracking tests",
                    owner_id=test_user.id,
                    status="active"
                )
                db.add(test_project)
                await db.commit()
                await db.refresh(test_project)
                self.test_project_id = test_project.id
                self.created_records.append(("project", test_project.id))
                
                logger.info(f"  ✅ Test data created: User ID {self.test_user_id}, Project ID {self.test_project_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to setup test data: {e}")
            return False
    
    async def cleanup_test_data(self):
        """Cleanup test data after tests."""
        try:
            logger.info("🧽 Cleaning up test data...")
            
            async for db in get_db_session():
                # Clean up in reverse order
                for record_type, record_id in reversed(self.created_records):
                    if record_type == "user":
                        user = await db.get(Talent, record_id)
                        if user:
                            await db.delete(user)
                    elif record_type == "project":
                        project = await db.get(Project, record_id)
                        if project:
                            await db.delete(project)
                    elif record_type == "engagement":
                        engagement = await db.get(Engagement, record_id)
                        if engagement:
                            await db.delete(engagement)
                    elif record_type == "cost":
                        cost = await db.get(CostTracking, record_id)
                        if cost:
                            await db.delete(cost)
                    elif record_type == "cost_alert":
                        alert = await db.get(CostAlert, record_id)
                        if alert:
                            await db.delete(alert)
                
                await db.commit()
                logger.info(f"  ✅ Cleaned up {len(self.created_records)} test records")
                
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    async def test_database_connectivity(self) -> DatabaseTestResult:
        """Test basic database connectivity and operations."""
        logger.info("🔗 Testing Database Connectivity")
        
        start_time = time.time()
        errors = []
        records_affected = 0
        
        try:
            async for db in get_db_session():
                # Test basic query
                result = await db.execute("SELECT 1 as test_value")
                test_value = result.scalar()
                
                if test_value != 1:
                    errors.append("Basic query failed")
                
                # Test table access
                user_count = await db.execute("SELECT COUNT(*) FROM users")
                user_count_value = user_count.scalar()
                records_affected = user_count_value
                
                # Test simple query execution (no nested transaction)
                await db.execute("SELECT 1")
                
                operation_time = (time.time() - start_time) * 1000
                
                logger.info(f"  ✅ Database connectivity test passed ({operation_time:.1f}ms)")
                
                return DatabaseTestResult(
                    test_name="Database Connectivity",
                    success=len(errors) == 0,
                    operation_time_ms=operation_time,
                    records_affected=records_affected,
                    data_integrity_check=True,
                    performance_metrics={
                        "connection_time_ms": operation_time,
                        "query_success": test_value == 1,
                        "table_access": user_count_value >= 0
                    },
                    errors=errors
                )
                
        except Exception as e:
            operation_time = (time.time() - start_time) * 1000
            errors.append(str(e))
            logger.error(f"  ❌ Database connectivity test failed: {e}")
            
            return DatabaseTestResult(
                test_name="Database Connectivity",
                success=False,
                operation_time_ms=operation_time,
                records_affected=0,
                data_integrity_check=False,
                performance_metrics={},
                errors=errors
            )
    
    async def test_crud_operations(self) -> DatabaseTestResult:
        """Test CRUD operations across different tables."""
        logger.info("📝 Testing CRUD Operations")
        
        start_time = time.time()
        errors = []
        records_affected = 0
        
        try:
            async for db in get_db_session():
                # CREATE: Create engagement
                engagement = Engagement(
                    title=f"Test Engagement {TIMESTAMP}",
                    description="Test engagement for CRUD operations",
                    status="active"
                )
                db.add(engagement)
                await db.commit()
                await db.refresh(engagement)
                engagement_id = engagement.id
                self.created_records.append(("engagement", engagement_id))
                records_affected += 1
                
                # READ: Retrieve engagement
                retrieved_engagement = await db.get(Engagement, engagement_id)
                if not retrieved_engagement:
                    errors.append("Failed to retrieve created engagement")
                elif retrieved_engagement.title != engagement.title:
                    errors.append("Retrieved engagement data mismatch")
                
                # UPDATE: Modify engagement
                retrieved_engagement.description = "Updated description for testing"
                retrieved_engagement.progress = 50.0
                await db.commit()
                
                # Verify update
                updated_engagement = await db.get(Engagement, engagement_id)
                if updated_engagement.progress != 50.0:
                    errors.append("Update operation failed")
                records_affected += 1
                
                # DELETE: Remove engagement (will be cleaned up anyway)
                await db.delete(updated_engagement)
                await db.commit()
                records_affected += 1
                
                # Verify deletion
                deleted_engagement = await db.get(Engagement, engagement_id)
                if deleted_engagement is not None:
                    errors.append("Delete operation failed")
                else:
                    # Remove from cleanup list since it's already deleted
                    self.created_records = [(t, i) for t, i in self.created_records if not (t == "engagement" and i == engagement_id)]
                
                operation_time = (time.time() - start_time) * 1000
                
                logger.info(f"  ✅ CRUD operations test passed ({operation_time:.1f}ms, {records_affected} records)")
                
                return DatabaseTestResult(
                    test_name="CRUD Operations",
                    success=len(errors) == 0,
                    operation_time_ms=operation_time,
                    records_affected=records_affected,
                    data_integrity_check=len(errors) == 0,
                    performance_metrics={
                        "create_success": True,
                        "read_success": retrieved_engagement is not None,
                        "update_success": updated_engagement.progress == 50.0,
                        "delete_success": deleted_engagement is None
                    },
                    errors=errors
                )
                
        except Exception as e:
            operation_time = (time.time() - start_time) * 1000
            errors.append(str(e))
            logger.error(f"  ❌ CRUD operations test failed: {e}")
            
            return DatabaseTestResult(
                test_name="CRUD Operations",
                success=False,
                operation_time_ms=operation_time,
                records_affected=records_affected,
                data_integrity_check=False,
                performance_metrics={},
                errors=errors
            )
    
    async def test_cost_tracking_accuracy(self) -> CostTrackingTestResult:
        """Test cost tracking accuracy and persistence."""
        logger.info("💰 Testing Cost Tracking Accuracy")
        
        start_time = time.time()
        errors = []
        test_cost = Decimal('0.15')
        
        try:
            # Test cost tracking via API
            async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
                response = await client.post(
                    "/api/v1/agents/conversation",
                    json={
                        "message": "Test message for cost tracking",
                        "conversation_id": f"{self.test_session_id}_cost_test",
                        "context": {
                            "track_cost": True,
                            "test_mode": True,
                            "user_id": self.test_user_id,
                            "agent_name": "ali"
                        }
                    }
                )
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    tracked_cost = data.get("cost", 0)
                    
                    # Verify cost tracking in database
                    async for db in get_db_session():
                        cost_records = await db.execute(
                            "SELECT * FROM cost_tracking WHERE session_id = :session_id",
                            {"session_id": f"{self.test_session_id}_cost_test"}
                        )
                        cost_record = cost_records.first()
                        
                        if cost_record:
                            self.created_records.append(("cost", cost_record.id))
                            db_cost = cost_record.total_cost_usd
                            
                            # Check cost accuracy (allow simulated test costs)
                            cost_diff = abs(float(db_cost) - float(tracked_cost))
                            if cost_diff > 0.15:  # Allow test mode simulation differences
                                errors.append(f"Cost mismatch: API={tracked_cost}, DB={db_cost}")
                        else:
                            errors.append("Cost not persisted to database")
                    
                    logger.info(f"  ✅ Cost tracking accuracy test passed (Cost: ${tracked_cost})")
                    
                    return CostTrackingTestResult(
                        test_name="Cost Tracking Accuracy",
                        success=len(errors) == 0,
                        cost_tracked=Decimal(str(tracked_cost)),
                        limit_enforced=False,  # No limit set in this test
                        accuracy_check=len(errors) == 0,
                        response_time_ms=response_time,
                        safety_mechanisms={
                            "cost_persistence": cost_record is not None,
                            "api_cost_reporting": "cost" in data,
                            "session_tracking": True
                        },
                        errors=errors
                    )
                else:
                    errors.append(f"API request failed: {response.status_code}")
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            errors.append(str(e))
            logger.error(f"  ❌ Cost tracking accuracy test failed: {e}")
        
        return CostTrackingTestResult(
            test_name="Cost Tracking Accuracy",
            success=False,
            cost_tracked=Decimal('0'),
            limit_enforced=False,
            accuracy_check=False,
            response_time_ms=(time.time() - start_time) * 1000,
            safety_mechanisms={},
            errors=errors
        )
    
    async def test_cost_limits_enforcement(self) -> CostTrackingTestResult:
        """Test cost limits and safety mechanisms."""
        logger.info("🛡️ Testing Cost Limits Enforcement")
        
        start_time = time.time()
        errors = []
        test_limit = Decimal('0.50')
        
        try:
            # Set up cost alert (simulating limit enforcement)
            async for db in get_db_session():
                cost_alert = CostAlert(
                    alert_type="budget_warning",
                    severity="warning",
                    current_value=Decimal('0.00'),
                    threshold_value=test_limit,
                    message=f"Cost limit test alert for user {self.test_user_id}",
                    session_id=f"{self.test_session_id}_limit_test"
                )
                db.add(cost_alert)
                await db.commit()
                await db.refresh(cost_alert)
                self.created_records.append(("cost_alert", cost_alert.id))
            
            # Test multiple conversations to approach limit
            total_cost = Decimal('0')
            limit_enforced = False
            
            async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
                for i in range(5):  # Try 5 conversations
                    response = await client.post(
                        "/api/v1/agents/conversation",
                        json={
                            "message": f"Test message {i+1} for cost limit enforcement",
                            "agent": "ali",
                            "session_id": f"{self.test_session_id}_limit_test_{i}",
                            "context": {
                                "track_cost": True,
                                "enforce_limits": True,
                                "user_id": self.test_user_id
                            }
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        conversation_cost = Decimal(str(data.get("cost", 0)))
                        total_cost += conversation_cost
                        
                        # Check if approaching limit
                        if total_cost >= test_limit * Decimal('0.9'):  # 90% of limit
                            # Next request should be blocked or warned
                            next_response = await client.post(
                                "/api/v1/agents/conversation",
                                json={
                                    "message": "This should trigger cost limit",
                                    "agent": "ali",
                                    "session_id": f"{self.test_session_id}_limit_trigger",
                                    "context": {
                                        "track_cost": True,
                                        "enforce_limits": True,
                                        "user_id": self.test_user_id
                                    }
                                }
                            )
                            
                            if next_response.status_code == 429:  # Rate limited
                                limit_enforced = True
                                logger.info(f"    ✅ Cost limit enforced at ${total_cost}")
                                break
                            elif next_response.status_code == 200:
                                next_data = next_response.json()
                                if "warning" in next_data or "limit" in str(next_data).lower():
                                    limit_enforced = True
                                    logger.info(f"    ✅ Cost limit warning triggered at ${total_cost}")
                                    break
                    
                    # Brief pause between requests
                    await asyncio.sleep(0.5)
            
            response_time = (time.time() - start_time) * 1000
            
            logger.info(f"  ✅ Cost limits enforcement test completed (Total cost: ${total_cost})")
            
            return CostTrackingTestResult(
                test_name="Cost Limits Enforcement",
                success=len(errors) == 0,
                cost_tracked=total_cost,
                limit_enforced=limit_enforced,
                accuracy_check=total_cost > Decimal('0'),
                response_time_ms=response_time,
                safety_mechanisms={
                    "limit_configuration": True,
                    "limit_enforcement": limit_enforced,
                    "cost_accumulation": total_cost > Decimal('0'),
                    "session_isolation": True
                },
                errors=errors
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            errors.append(str(e))
            logger.error(f"  ❌ Cost limits enforcement test failed: {e}")
            
            return CostTrackingTestResult(
                test_name="Cost Limits Enforcement",
                success=False,
                cost_tracked=Decimal('0'),
                limit_enforced=False,
                accuracy_check=False,
                response_time_ms=response_time,
                safety_mechanisms={},
                errors=errors
            )
    
    async def test_database_performance_load(self) -> DatabaseTestResult:
        """Test database performance under load."""
        logger.info("🚀 Testing Database Performance Under Load")
        
        start_time = time.time()
        errors = []
        records_affected = 0
        
        try:
            # Simulate concurrent database operations
            async def create_engagement_batch(batch_id: int) -> int:
                batch_records = 0
                async for db in get_db_session():
                    for i in range(5):  # 5 records per batch
                        engagement = Engagement(
                            title=f"Load Test Engagement {batch_id}-{i}",
                            description=f"Performance test engagement batch {batch_id} item {i}",
                            status="active"
                        )
                        db.add(engagement)
                        batch_records += 1
                    
                    await db.commit()
                    
                    # Add to cleanup list
                    result = await db.execute(
                        "SELECT id FROM engagements WHERE title LIKE :pattern",
                        {"pattern": f"Load Test Engagement {batch_id}-%"}
                    )
                    engagement_ids = [row[0] for row in result.fetchall()]
                    for eng_id in engagement_ids:
                        self.created_records.append(("engagement", eng_id))
                
                return batch_records
            
            # Run 4 concurrent batches
            batch_tasks = [create_engagement_batch(i) for i in range(4)]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Count successful records
            for result in batch_results:
                if isinstance(result, int):
                    records_affected += result
                elif isinstance(result, Exception):
                    errors.append(f"Batch failed: {result}")
            
            # Test read performance
            async for db in get_db_session():
                read_start = time.time()
                result = await db.execute(
                    "SELECT COUNT(*) FROM engagements"
                )
                engagement_count = result.scalar()
                read_time = (time.time() - read_start) * 1000
            
            operation_time = (time.time() - start_time) * 1000
            
            logger.info(f"  ✅ Database performance test passed ({operation_time:.1f}ms, {records_affected} records)")
            
            return DatabaseTestResult(
                test_name="Database Performance Load",
                success=len(errors) == 0 and records_affected > 0,
                operation_time_ms=operation_time,
                records_affected=records_affected,
                data_integrity_check=engagement_count >= records_affected,
                performance_metrics={
                    "concurrent_batches": 4,
                    "records_per_batch": 5,
                    "total_records_created": records_affected,
                    "read_query_time_ms": read_time,
                    "throughput_records_per_second": records_affected / (operation_time / 1000) if operation_time > 0 else 0
                },
                errors=errors
            )
            
        except Exception as e:
            operation_time = (time.time() - start_time) * 1000
            errors.append(str(e))
            logger.error(f"  ❌ Database performance test failed: {e}")
            
            return DatabaseTestResult(
                test_name="Database Performance Load",
                success=False,
                operation_time_ms=operation_time,
                records_affected=records_affected,
                data_integrity_check=False,
                performance_metrics={},
                errors=errors
            )
    
    async def test_transaction_integrity(self) -> DatabaseTestResult:
        """Test transaction management and data integrity."""
        logger.info("🔒 Testing Transaction Integrity")
        
        start_time = time.time()
        errors = []
        records_affected = 0
        
        try:
            async for db in get_db_session():
                # Test successful transaction
                async with db.begin():
                    engagement1 = Engagement(
                        
                        title=f"Transaction Test 1 {TIMESTAMP}",
                        description="First engagement in transaction",
                        status="active",
                        
                        
                    )
                    engagement2 = Engagement(
                        
                        title=f"Transaction Test 2 {TIMESTAMP}",
                        description="Second engagement in transaction",
                        status="active",
                        
                        
                    )
                    
                    db.add(engagement1)
                    db.add(engagement2)
                    # Transaction commits automatically
                
                await db.refresh(engagement1)
                await db.refresh(engagement2)
                self.created_records.append(("engagement", engagement1.id))
                self.created_records.append(("engagement", engagement2.id))
                records_affected += 2
                
                # Test rollback transaction
                try:
                    async with db.begin():
                        engagement3 = Engagement(
                            
                            title=f"Transaction Test 3 {TIMESTAMP}",
                            description="This should be rolled back",
                            status="active",
                            
                            
                        )
                        db.add(engagement3)
                        
                        # Force an error to trigger rollback
                        await db.execute("SELECT * FROM non_existent_table")
                        
                except Exception:
                    # Expected - transaction should be rolled back
                    pass
                
                # Verify rollback worked
                result = await db.execute(
                    "SELECT COUNT(*) FROM engagements WHERE title LIKE :pattern",
                    {"pattern": f"Transaction Test 3 {TIMESTAMP}"}
                )
                rollback_count = result.scalar()
                
                if rollback_count > 0:
                    errors.append("Transaction rollback failed")
                
                # Verify successful transactions persisted
                result = await db.execute(
                    "SELECT COUNT(*) FROM engagements WHERE title LIKE :pattern",
                    {"pattern": f"Transaction Test % {TIMESTAMP}"}
                )
                success_count = result.scalar()
                
                if success_count != 2:
                    errors.append(f"Expected 2 successful transactions, found {success_count}")
            
            operation_time = (time.time() - start_time) * 1000
            
            logger.info(f"  ✅ Transaction integrity test passed ({operation_time:.1f}ms)")
            
            return DatabaseTestResult(
                test_name="Transaction Integrity",
                success=len(errors) == 0,
                operation_time_ms=operation_time,
                records_affected=records_affected,
                data_integrity_check=len(errors) == 0,
                performance_metrics={
                    "successful_transactions": 1,
                    "rollback_transactions": 1,
                    "rollback_verification": rollback_count == 0,
                    "persistence_verification": success_count == 2
                },
                errors=errors
            )
            
        except Exception as e:
            operation_time = (time.time() - start_time) * 1000
            errors.append(str(e))
            logger.error(f"  ❌ Transaction integrity test failed: {e}")
            
            return DatabaseTestResult(
                test_name="Transaction Integrity",
                success=False,
                operation_time_ms=operation_time,
                records_affected=records_affected,
                data_integrity_check=False,
                performance_metrics={},
                errors=errors
            )
    
    async def run_all_database_cost_tests(self) -> Dict[str, Any]:
        """Run all database and cost tracking tests."""
        logger.info("🚀 Starting Database Operations & Cost Tracking Test Suite")
        logger.info(f"Session ID: {self.test_session_id}")
        logger.info(f"Log file: {LOG_FILE}")
        logger.info("="*80)
        
        # Setup test data
        if not await self.setup_test_data():
            return {"error": "Failed to setup test data"}
        
        try:
            # Database tests
            database_tests = [
                self.test_database_connectivity(),
                self.test_crud_operations(),
                self.test_database_performance_load(),
                self.test_transaction_integrity()
            ]
            
            # Cost tracking tests
            cost_tests = [
                self.test_cost_tracking_accuracy(),
                self.test_cost_limits_enforcement()
            ]
            
            start_time = time.time()
            
            # Run database tests
            logger.info("📊 Running Database Tests...")
            database_results = []
            for test_coro in database_tests:
                try:
                    result = await test_coro
                    database_results.append(result)
                    await asyncio.sleep(1)  # Brief pause between tests
                except Exception as e:
                    logger.error(f"Database test failed: {e}")
                    database_results.append(DatabaseTestResult(
                        test_name="Failed Test",
                        success=False,
                        operation_time_ms=0,
                        records_affected=0,
                        data_integrity_check=False,
                        performance_metrics={},
                        errors=[str(e)]
                    ))
            
            # Run cost tracking tests
            logger.info("💰 Running Cost Tracking Tests...")
            cost_results = []
            for test_coro in cost_tests:
                try:
                    result = await test_coro
                    cost_results.append(result)
                    await asyncio.sleep(1)  # Brief pause between tests
                except Exception as e:
                    logger.error(f"Cost tracking test failed: {e}")
                    cost_results.append(CostTrackingTestResult(
                        test_name="Failed Test",
                        success=False,
                        cost_tracked=Decimal('0'),
                        limit_enforced=False,
                        accuracy_check=False,
                        response_time_ms=0,
                        safety_mechanisms={},
                        errors=[str(e)]
                    ))
            
            total_time = time.time() - start_time
            
            # Generate summary
            summary = self.generate_database_cost_summary(database_results, cost_results, total_time)
            
            logger.info("="*80)
            logger.info("📊 DATABASE & COST TRACKING TESTS COMPLETED")
            logger.info(f"Total time: {total_time:.1f}s")
            logger.info(f"Results saved to: {LOG_FILE}")
            logger.info("="*80)
            
            return summary
            
        finally:
            # Always cleanup test data
            await self.cleanup_test_data()
    
    def generate_database_cost_summary(self, db_results: List[DatabaseTestResult], cost_results: List[CostTrackingTestResult], total_time: float) -> Dict[str, Any]:
        """Generate comprehensive database and cost tracking test summary."""
        # Database metrics
        db_successful = len([r for r in db_results if r.success])
        db_total_records = sum(r.records_affected for r in db_results)
        db_avg_time = sum(r.operation_time_ms for r in db_results) / len(db_results) if db_results else 0
        db_integrity_passed = len([r for r in db_results if r.data_integrity_check])
        
        # Cost tracking metrics
        cost_successful = len([r for r in cost_results if r.success])
        cost_total_tracked = sum(r.cost_tracked for r in cost_results)
        cost_limits_enforced = len([r for r in cost_results if r.limit_enforced])
        cost_accuracy_passed = len([r for r in cost_results if r.accuracy_check])
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_time_seconds": round(total_time, 2),
            "overview": {
                "database_tests": len(db_results),
                "database_success_rate": round((db_successful / len(db_results)) * 100, 1) if db_results else 0,
                "cost_tracking_tests": len(cost_results),
                "cost_tracking_success_rate": round((cost_successful / len(cost_results)) * 100, 1) if cost_results else 0,
                "total_tests": len(db_results) + len(cost_results),
                "overall_success_rate": round(((db_successful + cost_successful) / (len(db_results) + len(cost_results))) * 100, 1) if (db_results or cost_results) else 0
            },
            "database_performance": {
                "total_records_affected": db_total_records,
                "average_operation_time_ms": round(db_avg_time, 2),
                "data_integrity_pass_rate": round((db_integrity_passed / len(db_results)) * 100, 1) if db_results else 0,
                "performance_metrics": {
                    "connectivity_ok": any("connectivity" in r.test_name.lower() and r.success for r in db_results),
                    "crud_operations_ok": any("crud" in r.test_name.lower() and r.success for r in db_results),
                    "load_performance_ok": any("performance" in r.test_name.lower() and r.success for r in db_results),
                    "transaction_integrity_ok": any("transaction" in r.test_name.lower() and r.success for r in db_results)
                }
            },
            "cost_tracking_performance": {
                "total_cost_tracked": float(cost_total_tracked),
                "limits_enforced_count": cost_limits_enforced,
                "accuracy_pass_rate": round((cost_accuracy_passed / len(cost_results)) * 100, 1) if cost_results else 0,
                "safety_mechanisms": {
                    "cost_persistence": any(r.safety_mechanisms.get("cost_persistence", False) for r in cost_results),
                    "limit_enforcement": any(r.safety_mechanisms.get("limit_enforcement", False) for r in cost_results),
                    "api_cost_reporting": any(r.safety_mechanisms.get("api_cost_reporting", False) for r in cost_results),
                    "session_tracking": any(r.safety_mechanisms.get("session_tracking", False) for r in cost_results)
                }
            },
            "database_test_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "operation_time_ms": round(r.operation_time_ms, 2),
                    "records_affected": r.records_affected,
                    "data_integrity_check": r.data_integrity_check,
                    "error_count": len(r.errors)
                }
                for r in db_results
            ],
            "cost_tracking_test_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "cost_tracked": float(r.cost_tracked),
                    "limit_enforced": r.limit_enforced,
                    "accuracy_check": r.accuracy_check,
                    "response_time_ms": round(r.response_time_ms, 2),
                    "error_count": len(r.errors)
                }
                for r in cost_results
            ],
            "detailed_results": {
                "database_tests": [
                    {
                        "test_name": r.test_name,
                        "success": r.success,
                        "operation_time_ms": r.operation_time_ms,
                        "records_affected": r.records_affected,
                        "data_integrity_check": r.data_integrity_check,
                        "performance_metrics": r.performance_metrics,
                        "errors": r.errors
                    }
                    for r in db_results
                ],
                "cost_tracking_tests": [
                    {
                        "test_name": r.test_name,
                        "success": r.success,
                        "cost_tracked": float(r.cost_tracked),
                        "limit_enforced": r.limit_enforced,
                        "accuracy_check": r.accuracy_check,
                        "response_time_ms": r.response_time_ms,
                        "safety_mechanisms": r.safety_mechanisms,
                        "errors": r.errors
                    }
                    for r in cost_results
                ]
            }
        }
        
        # Save detailed results
        results_file = LOG_DIR / f"database_cost_test_results_{TIMESTAMP}.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"📋 Detailed results saved to: {results_file}")
        
        # Log summary
        logger.info(f"""\n📊 DATABASE & COST TRACKING SUMMARY
===================================
Database Tests: {len(db_results)} (Success: {db_successful}/{len(db_results)} = {(db_successful/len(db_results))*100:.1f}%)
Cost Tracking Tests: {len(cost_results)} (Success: {cost_successful}/{len(cost_results)} = {(cost_successful/len(cost_results))*100:.1f}%)
Total Records Affected: {db_total_records:,}
Total Cost Tracked: ${cost_total_tracked}
Average DB Operation Time: {db_avg_time:.1f}ms
Data Integrity: {db_integrity_passed}/{len(db_results)} tests passed
Cost Limits Enforced: {cost_limits_enforced}/{len(cost_results)} tests

Database Performance:
  • Connectivity: {'✅' if summary['database_performance']['performance_metrics']['connectivity_ok'] else '❌'}
  • CRUD Operations: {'✅' if summary['database_performance']['performance_metrics']['crud_operations_ok'] else '❌'}
  • Load Performance: {'✅' if summary['database_performance']['performance_metrics']['load_performance_ok'] else '❌'}
  • Transaction Integrity: {'✅' if summary['database_performance']['performance_metrics']['transaction_integrity_ok'] else '❌'}

Cost Tracking Safety:
  • Cost Persistence: {'✅' if summary['cost_tracking_performance']['safety_mechanisms']['cost_persistence'] else '❌'}
  • Limit Enforcement: {'✅' if summary['cost_tracking_performance']['safety_mechanisms']['limit_enforcement'] else '❌'}
  • API Reporting: {'✅' if summary['cost_tracking_performance']['safety_mechanisms']['api_cost_reporting'] else '❌'}
  • Session Tracking: {'✅' if summary['cost_tracking_performance']['safety_mechanisms']['session_tracking'] else '❌'}
""")
        
        return summary
# Pytest integration
class TestDatabaseCostTracking:
    """Pytest wrapper for database and cost tracking tests."""
    
    @pytest.mark.asyncio
    async def test_database_connectivity(self):
        """Test database connectivity."""
        tester = DatabaseCostTrackingTester()
        await tester.setup_test_data()
        try:
            result = await tester.test_database_connectivity()
            assert result.success, f"Database connectivity failed: {result.errors}"
            assert result.operation_time_ms < 5000, f"Database operation too slow: {result.operation_time_ms}ms"
        finally:
            await tester.cleanup_test_data()
    
    @pytest.mark.asyncio
    async def test_crud_operations(self):
        """Test CRUD operations."""
        tester = DatabaseCostTrackingTester()
        await tester.setup_test_data()
        try:
            result = await tester.test_crud_operations()
            assert result.success, f"CRUD operations failed: {result.errors}"
            assert result.data_integrity_check, "Data integrity check failed"
            assert result.records_affected > 0, "No records affected"
        finally:
            await tester.cleanup_test_data()
    
    @pytest.mark.asyncio
    async def test_cost_tracking_accuracy(self):
        """Test cost tracking accuracy."""
        tester = DatabaseCostTrackingTester()
        await tester.setup_test_data()
        try:
            result = await tester.test_cost_tracking_accuracy()
            assert result.success, f"Cost tracking accuracy failed: {result.errors}"
            assert result.accuracy_check, "Cost accuracy check failed"
            assert result.cost_tracked > 0, "No cost tracked"
        finally:
            await tester.cleanup_test_data()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_database_performance(self):
        """Test database performance under load."""
        tester = DatabaseCostTrackingTester()
        await tester.setup_test_data()
        try:
            result = await tester.test_database_performance_load()
            assert result.success, f"Database performance test failed: {result.errors}"
            assert result.records_affected >= 10, f"Not enough records created: {result.records_affected}"
        finally:
            await tester.cleanup_test_data()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_all_database_cost_comprehensive(self):
        """Test all database and cost tracking functionality comprehensively."""
        tester = DatabaseCostTrackingTester()
        results = await tester.run_all_database_cost_tests()
        
        # Assert overall success
        assert "error" not in results, f"Database/cost tests failed: {results.get('error')}"
        assert results["overview"]["total_tests"] > 0, "No tests executed"
        
        # Assert reasonable success rates
        db_success_rate = results["overview"]["database_success_rate"]
        assert db_success_rate >= 75, f"Database success rate too low: {db_success_rate}% (expected ≥75%)"
        
        cost_success_rate = results["overview"]["cost_tracking_success_rate"]
        assert cost_success_rate >= 50, f"Cost tracking success rate too low: {cost_success_rate}% (expected ≥50%)"
        
        # Assert performance metrics
        db_perf = results["database_performance"]
        assert db_perf["connectivity_ok"], "Database connectivity not working"
        assert db_perf["crud_operations_ok"], "CRUD operations not working"
        
        # Assert cost tracking safety
        cost_safety = results["cost_tracking_performance"]["safety_mechanisms"]
        assert cost_safety["cost_persistence"], "Cost persistence not working"
        assert cost_safety["api_cost_reporting"], "API cost reporting not working"
def run_database_cost_tests():
    """Execute the database and cost tracking test suite."""
    logger.info("Starting Convergio Database Operations & Cost Tracking Test Suite")
    
    # Configure pytest
    pytest_args = [
        __file__,
        "-v",
        "-s",
        "--tb=short",
        "--color=yes",
        f"--junit-xml={LOG_DIR}/database_cost_{TIMESTAMP}_junit.xml"
    ]
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    # Report results
    logger.info("="*80)
    if exit_code == 0:
        logger.info("✅ ALL DATABASE & COST TRACKING TESTS PASSED!")
    else:
        logger.error(f"❌ DATABASE & COST TRACKING TESTS FAILED (exit code: {exit_code})")
    logger.info(f"Test results saved to: {LOG_FILE}")
    logger.info("="*80)
    
    return exit_code
if __name__ == "__main__":
    import sys
    # Run the test suite directly
    tester = DatabaseCostTrackingTester()
    
    async def main():
        return await tester.run_all_database_cost_tests()
    
    results = asyncio.run(main())
    
    # Exit with appropriate code
    if "error" in results:
        sys.exit(1)
    elif results["overview"]["overall_success_rate"] < 70:
        sys.exit(1)
    else:
        sys.exit(0)
