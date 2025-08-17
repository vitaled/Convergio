"""
Admin API endpoints for database maintenance and monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import structlog

from core.database import get_db_session
from core.db_maintenance import get_db_maintenance

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/db-stats")
async def get_database_statistics(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get database statistics including table sizes and bloat.
    """
    try:
        db_maintenance = get_db_maintenance()
        table_stats = await db_maintenance.get_table_statistics(db)
        
        return {
            "status": "success",
            "tables": table_stats,
            "total_tables": len(table_stats)
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/slow-queries")
async def get_slow_queries(
    threshold_ms: int = 100,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get slow queries from pg_stat_statements.
    
    Args:
        threshold_ms: Minimum query time in milliseconds
    """
    try:
        db_maintenance = get_db_maintenance()
        slow_queries = await db_maintenance.analyze_slow_queries(db, threshold_ms)
        
        return {
            "status": "success",
            "threshold_ms": threshold_ms,
            "queries": slow_queries,
            "total": len(slow_queries)
        }
    except Exception as e:
        logger.error(f"Failed to get slow queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/vacuum")
async def run_vacuum_analyze(
    tables: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Manually run VACUUM ANALYZE on specified tables or all tables.
    
    Args:
        tables: List of table names (all if not specified)
    """
    try:
        db_maintenance = get_db_maintenance()
        results = await db_maintenance.vacuum_analyze_tables(db, tables)
        
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        logger.error(f"Failed to run VACUUM ANALYZE: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/index-suggestions")
async def get_index_optimization_suggestions(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get index optimization suggestions including unused and duplicate indexes.
    """
    try:
        db_maintenance = get_db_maintenance()
        suggestions = await db_maintenance.optimize_indexes(db)
        
        return {
            "status": "success",
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Failed to get index suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/maintenance-status")
async def get_maintenance_status() -> Dict[str, Any]:
    """
    Get current maintenance scheduler status and history.
    """
    try:
        db_maintenance = get_db_maintenance()
        status = db_maintenance.get_maintenance_status()
        
        return {
            "status": "success",
            "maintenance": status
        }
    except Exception as e:
        logger.error(f"Failed to get maintenance status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/maintenance/schedule")
async def update_maintenance_schedule(
    vacuum_hour: int = 3,
    vacuum_minute: int = 0
) -> Dict[str, Any]:
    """
    Update the maintenance schedule.
    
    Args:
        vacuum_hour: Hour to run VACUUM (0-23)
        vacuum_minute: Minute to run VACUUM (0-59)
    """
    try:
        if not (0 <= vacuum_hour <= 23):
            raise ValueError("vacuum_hour must be between 0 and 23")
        if not (0 <= vacuum_minute <= 59):
            raise ValueError("vacuum_minute must be between 0 and 59")
        
        db_maintenance = get_db_maintenance()
        
        # Stop current scheduler if running
        if db_maintenance.is_running:
            db_maintenance.stop_maintenance()
        
        # Start with new schedule
        db_maintenance.schedule_maintenance(vacuum_hour, vacuum_minute)
        
        return {
            "status": "success",
            "message": f"Maintenance scheduled for {vacuum_hour:02d}:{vacuum_minute:02d} UTC daily"
        }
    except Exception as e:
        logger.error(f"Failed to update maintenance schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )