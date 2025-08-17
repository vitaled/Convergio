"""
📋 Convergio - Engagement/Project Model  
SQLAlchemy 2.0 Engagement model matching existing database schema
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import Integer, String, DateTime, func, Text, Float
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Engagement(Base):
    """Engagement/Project model matching the existing Convergio database schema"""
    
    __tablename__ = "engagements"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Engagement info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Vector embeddings - existing in DB
    content_embedding: Mapped[Optional[bytes]] = mapped_column(nullable=True)  # vector type
    objectives_embedding: Mapped[Optional[bytes]] = mapped_column(nullable=True)  # vector type
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engagement to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.get_status(),
            "progress": self.calculate_progress()
        }
    
    def get_status(self) -> str:
        """Calculate engagement status based on dates"""
        now = datetime.utcnow()
        if self.created_at:
            days_old = (now - self.created_at.replace(tzinfo=None)).days
            if days_old < 7:
                return "planning"
            elif days_old < 30:
                return "in-progress"
            elif days_old < 60:
                return "review"
            else:
                return "completed"
        return "planning"
    
    def calculate_progress(self) -> float:
        """Calculate progress percentage based on age"""
        now = datetime.utcnow()
        if self.created_at:
            days_old = (now - self.created_at.replace(tzinfo=None)).days
            # Simple progress calculation: newer projects have lower progress
            if days_old < 30:
                return min(days_old * 3.33, 100.0)  # 3.33% per day for first 30 days
            else:
                return 100.0
        return 0.0
    
    @classmethod
    async def get_all(cls, db: AsyncSession, skip: int = 0, limit: int = 100) -> List["Engagement"]:
        """Get all engagements"""
        result = await db.execute(
            select(cls)
            .offset(skip)
            .limit(limit)
            .order_by(cls.created_at.desc())
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, engagement_id: int) -> Optional["Engagement"]:
        """Get engagement by ID"""
        result = await db.execute(
            select(cls).where(cls.id == engagement_id)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_total_count(cls, db: AsyncSession) -> int:
        """Get total count of engagements"""
        result = await db.execute(
            select(func.count(cls.id))
        )
        return result.scalar() or 0
    
    @classmethod
    async def get_recent(cls, db: AsyncSession, limit: int = 10) -> List["Engagement"]:
        """Get recent engagements"""
        result = await db.execute(
            select(cls)
            .order_by(cls.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())