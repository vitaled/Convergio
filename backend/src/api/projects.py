"""
📋 Convergio - Projects & Clients API
Real project management with clients and engagements from database
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.models.client import Client
from src.models.engagement import Engagement
from src.models.activity import Activity

logger = structlog.get_logger()
router = APIRouter(tags=["Projects & Clients"])


# Response models
class ClientResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: Optional[str]
    updated_at: Optional[str]


class ActivityResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    progress: float
    created_at: Optional[str]
    updated_at: Optional[str]


class EngagementResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    progress: float
    created_at: Optional[str]
    updated_at: Optional[str]


class EngagementDetailResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    progress: float
    created_at: Optional[str]
    updated_at: Optional[str]
    activities: List[ActivityResponse]


class ProjectOverviewResponse(BaseModel):
    total_clients: int
    total_engagements: int
    active_engagements: int
    completed_engagements: int
    clients: List[ClientResponse]
    recent_engagements: List[EngagementResponse]


@router.get("/clients", response_model=List[ClientResponse])
async def get_clients(
    skip: int = Query(0, ge=0, description="Number of clients to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of clients to return"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    🏢 Get all clients from database
    """
    try:
        clients = await Client.get_all(db, skip=skip, limit=limit)
        
        return [
            ClientResponse(
                id=client.id,
                name=client.name,
                email=client.email,
                created_at=client.created_at.isoformat() if client.created_at else None,
                updated_at=client.updated_at.isoformat() if client.updated_at else None
            )
            for client in clients
        ]
    except Exception as e:
        logger.error(f"❌ Failed to get clients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get clients: {str(e)}")


@router.get("/engagements", response_model=List[EngagementResponse]) 
async def get_engagements(
    skip: int = Query(0, ge=0, description="Number of engagements to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of engagements to return"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    📋 Get all engagements/projects from database
    """
    try:
        engagements = await Engagement.get_all(db, skip=skip, limit=limit)
        
        return [
            EngagementResponse(
                id=engagement.id,
                title=engagement.title,
                description=engagement.description,
                status=engagement.get_status(),
                progress=engagement.calculate_progress(),
                created_at=engagement.created_at.isoformat() if engagement.created_at else None,
                updated_at=engagement.updated_at.isoformat() if engagement.updated_at else None
            )
            for engagement in engagements
        ]
    except Exception as e:
        logger.error(f"❌ Failed to get engagements: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get engagements: {str(e)}")


@router.get("/overview", response_model=ProjectOverviewResponse)
async def get_project_overview(
    db: AsyncSession = Depends(get_db_session)
):
    """
    📊 Get complete project management overview with real data
    """
    try:
        # Get counts
        total_clients = await Client.get_total_count(db)
        total_engagements = await Engagement.get_total_count(db)
        
        # Get recent data
        clients = await Client.get_all(db, limit=10)
        recent_engagements = await Engagement.get_recent(db, limit=10)
        
        # Calculate status counts
        all_engagements = await Engagement.get_all(db, limit=1000)  # Get more for accurate counts
        active_count = len([e for e in all_engagements if e.get_status() in ['planning', 'in-progress', 'review']])
        completed_count = len([e for e in all_engagements if e.get_status() == 'completed'])
        
        return ProjectOverviewResponse(
            total_clients=total_clients,
            total_engagements=total_engagements,
            active_engagements=active_count,
            completed_engagements=completed_count,
            clients=[
                ClientResponse(
                    id=client.id,
                    name=client.name,
                    email=client.email,
                    created_at=client.created_at.isoformat() if client.created_at else None,
                    updated_at=client.updated_at.isoformat() if client.updated_at else None
                )
                for client in clients
            ],
            recent_engagements=[
                EngagementResponse(
                    id=engagement.id,
                    title=engagement.title,
                    description=engagement.description,
                    status=engagement.get_status(),
                    progress=engagement.calculate_progress(),
                    created_at=engagement.created_at.isoformat() if engagement.created_at else None,
                    updated_at=engagement.updated_at.isoformat() if engagement.updated_at else None
                )
                for engagement in recent_engagements
            ]
        )
    except Exception as e:
        logger.error(f"❌ Failed to get project overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project overview: {str(e)}")


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    🏢 Get specific client by ID
    """
    try:
        client = await Client.get_by_id(db, client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return ClientResponse(
            id=client.id,
            name=client.name,
            email=client.email,
            created_at=client.created_at.isoformat() if client.created_at else None,
            updated_at=client.updated_at.isoformat() if client.updated_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get client: {str(e)}")


@router.get("/engagements/{engagement_id}", response_model=EngagementResponse)
async def get_engagement(
    engagement_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📋 Get specific engagement/project by ID
    """
    try:
        engagement = await Engagement.get_by_id(db, engagement_id)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        return EngagementResponse(
            id=engagement.id,
            title=engagement.title,
            description=engagement.description,
            status=engagement.get_status(),
            progress=engagement.calculate_progress(),
            created_at=engagement.created_at.isoformat() if engagement.created_at else None,
            updated_at=engagement.updated_at.isoformat() if engagement.updated_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get engagement {engagement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get engagement: {str(e)}")


@router.get("/engagements/{engagement_id}/details", response_model=EngagementDetailResponse)
async def get_engagement_details(
    engagement_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📋 Get detailed engagement/project with activities
    """
    try:
        engagement = await Engagement.get_by_id(db, engagement_id)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        # Get activities for this engagement
        activities = await Activity.get_for_engagement(db, engagement_id, limit=10)
        
        return EngagementDetailResponse(
            id=engagement.id,
            title=engagement.title,
            description=engagement.description,
            status=engagement.get_status(),
            progress=engagement.calculate_progress(),
            created_at=engagement.created_at.isoformat() if engagement.created_at else None,
            updated_at=engagement.updated_at.isoformat() if engagement.updated_at else None,
            activities=[
                ActivityResponse(
                    id=activity.id,
                    title=activity.title,
                    description=activity.description,
                    status=activity.get_status(),
                    progress=activity.calculate_progress(),
                    created_at=activity.created_at.isoformat() if activity.created_at else None,
                    updated_at=activity.updated_at.isoformat() if activity.updated_at else None
                )
                for activity in activities
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get engagement details {engagement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get engagement details: {str(e)}")


@router.get("/activities", response_model=List[ActivityResponse])
async def get_activities(
    skip: int = Query(0, ge=0, description="Number of activities to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of activities to return"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    📋 Get all activities from database
    """
    try:
        activities = await Activity.get_all(db, skip=skip, limit=limit)
        
        return [
            ActivityResponse(
                id=activity.id,
                title=activity.title,
                description=activity.description,
                status=activity.get_status(),
                progress=activity.calculate_progress(),
                created_at=activity.created_at.isoformat() if activity.created_at else None,
                updated_at=activity.updated_at.isoformat() if activity.updated_at else None
            )
            for activity in activities
        ]
    except Exception as e:
        logger.error(f"❌ Failed to get activities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get activities: {str(e)}")