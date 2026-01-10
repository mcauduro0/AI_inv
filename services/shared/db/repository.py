# =============================================================================
# Database Repository
# =============================================================================
# Database session management and repository pattern implementation
# =============================================================================

from contextlib import asynccontextmanager
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
import structlog

from shared.config.settings import settings
from shared.db.models import (
    Base, User, ResearchProject, ResearchNote, ResearchDocument,
    Workflow, WorkflowRun, AgentTaskRecord, Watchlist, WatchlistItem,
    ScreenerResult, PromptTemplate, KnowledgeDocument
)

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=Base)


# =============================================================================
# Database Engine and Session
# =============================================================================

def get_async_engine():
    """Create async database engine."""
    # Convert sync URL to async
    url = settings.database.url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    
    return create_async_engine(
        url,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_timeout=settings.database.pool_timeout,
        echo=settings.database.echo
    )


# Global engine instance
_engine = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = get_async_engine()
    return _engine


def get_session_factory():
    """Get async session factory."""
    return async_sessionmaker(
        get_engine(),
        class_=AsyncSession,
        expire_on_commit=False
    )


@asynccontextmanager
async def get_session():
    """Get a database session context manager."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Initialize database tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")


# =============================================================================
# Generic Repository
# =============================================================================

class Repository(Generic[T]):
    """
    Generic repository for database operations.
    
    Provides CRUD operations for any SQLAlchemy model.
    """
    
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session
        self.logger = structlog.get_logger(f"Repository[{model.__name__}]")
    
    async def get(self, id: UUID) -> Optional[T]:
        """Get a single record by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[T]:
        """Get all records with optional filtering."""
        query = select(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(self, **data) -> T:
        """Create a new record."""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        
        self.logger.debug("Created record", id=str(instance.id))
        return instance
    
    async def update(self, id: UUID, **data) -> Optional[T]:
        """Update a record by ID."""
        await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
        )
        return await self.get(id)
    
    async def delete(self, id: UUID) -> bool:
        """Delete a record by ID."""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0
    
    async def count(self, **filters) -> int:
        """Count records with optional filtering."""
        query = select(func.count()).select_from(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def exists(self, id: UUID) -> bool:
        """Check if a record exists."""
        result = await self.session.execute(
            select(func.count())
            .select_from(self.model)
            .where(self.model.id == id)
        )
        return result.scalar_one() > 0


# =============================================================================
# Specialized Repositories
# =============================================================================

class UserRepository(Repository[User]):
    """Repository for User operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


class ResearchProjectRepository(Repository[ResearchProject]):
    """Repository for ResearchProject operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ResearchProject, session)
    
    async def get_by_user(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ResearchProject]:
        """Get projects for a user."""
        query = select(ResearchProject).where(
            ResearchProject.user_id == user_id
        )
        
        if status:
            query = query.where(ResearchProject.status == status)
        
        query = query.order_by(ResearchProject.updated_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_ticker(
        self,
        ticker: str,
        user_id: Optional[UUID] = None
    ) -> List[ResearchProject]:
        """Get projects for a ticker."""
        query = select(ResearchProject).where(
            ResearchProject.ticker == ticker.upper()
        )
        
        if user_id:
            query = query.where(ResearchProject.user_id == user_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_with_notes(self, id: UUID) -> Optional[ResearchProject]:
        """Get project with related notes."""
        result = await self.session.execute(
            select(ResearchProject)
            .options(selectinload(ResearchProject.notes))
            .where(ResearchProject.id == id)
        )
        return result.scalar_one_or_none()


class WorkflowRepository(Repository[Workflow]):
    """Repository for Workflow operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Workflow, session)
    
    async def get_scheduled(self) -> List[Workflow]:
        """Get all scheduled workflows."""
        result = await self.session.execute(
            select(Workflow)
            .where(Workflow.schedule.isnot(None))
            .where(Workflow.status != "cancelled")
        )
        return list(result.scalars().all())
    
    async def get_with_runs(
        self,
        id: UUID,
        run_limit: int = 10
    ) -> Optional[Workflow]:
        """Get workflow with recent runs."""
        result = await self.session.execute(
            select(Workflow)
            .options(selectinload(Workflow.runs))
            .where(Workflow.id == id)
        )
        return result.scalar_one_or_none()


class AgentTaskRepository(Repository[AgentTaskRecord]):
    """Repository for AgentTaskRecord operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AgentTaskRecord, session)
    
    async def get_by_task_id(self, task_id: str) -> Optional[AgentTaskRecord]:
        """Get task by task_id."""
        result = await self.session.execute(
            select(AgentTaskRecord).where(
                AgentTaskRecord.task_id == task_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_pending_by_agent(
        self,
        agent_type: str,
        limit: int = 10
    ) -> List[AgentTaskRecord]:
        """Get pending tasks for an agent type."""
        result = await self.session.execute(
            select(AgentTaskRecord)
            .where(AgentTaskRecord.agent_type == agent_type)
            .where(AgentTaskRecord.status == "pending")
            .order_by(AgentTaskRecord.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_metrics(
        self,
        agent_type: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get task execution metrics."""
        from datetime import datetime, timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            AgentTaskRecord.agent_type,
            func.count().label("total"),
            func.avg(AgentTaskRecord.duration_seconds).label("avg_duration"),
            func.sum(AgentTaskRecord.tokens_used).label("total_tokens")
        ).where(
            AgentTaskRecord.created_at >= cutoff
        ).group_by(AgentTaskRecord.agent_type)
        
        if agent_type:
            query = query.where(AgentTaskRecord.agent_type == agent_type)
        
        result = await self.session.execute(query)
        
        metrics = {}
        for row in result:
            metrics[row.agent_type] = {
                "total_tasks": row.total,
                "avg_duration_seconds": float(row.avg_duration) if row.avg_duration else 0,
                "total_tokens": row.total_tokens or 0
            }
        
        return metrics


class PromptTemplateRepository(Repository[PromptTemplate]):
    """Repository for PromptTemplate operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(PromptTemplate, session)
    
    async def get_by_name(self, name: str) -> Optional[PromptTemplate]:
        """Get prompt by name."""
        result = await self.session.execute(
            select(PromptTemplate).where(
                PromptTemplate.name == name
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_category(
        self,
        category: str,
        active_only: bool = True
    ) -> List[PromptTemplate]:
        """Get prompts by category."""
        query = select(PromptTemplate).where(
            PromptTemplate.category == category
        )
        
        if active_only:
            query = query.where(PromptTemplate.is_active == True)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def increment_usage(self, id: UUID) -> None:
        """Increment usage count for a prompt."""
        await self.session.execute(
            update(PromptTemplate)
            .where(PromptTemplate.id == id)
            .values(usage_count=PromptTemplate.usage_count + 1)
        )


class ScreenerResultRepository(Repository[ScreenerResult]):
    """Repository for ScreenerResult operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ScreenerResult, session)
    
    async def get_top_results(
        self,
        screener_name: str,
        limit: int = 50
    ) -> List[ScreenerResult]:
        """Get top screening results."""
        result = await self.session.execute(
            select(ScreenerResult)
            .where(ScreenerResult.screener_name == screener_name)
            .order_by(ScreenerResult.overall_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_ticker(
        self,
        ticker: str,
        limit: int = 10
    ) -> List[ScreenerResult]:
        """Get screening history for a ticker."""
        result = await self.session.execute(
            select(ScreenerResult)
            .where(ScreenerResult.ticker == ticker.upper())
            .order_by(ScreenerResult.screened_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
