# =============================================================================
# Database Models
# =============================================================================
# SQLAlchemy models for the investment agent system
# =============================================================================

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, JSON, String, Text, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


# =============================================================================
# Enums
# =============================================================================

class TaskStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStatus(str, PyEnum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchStatus(str, PyEnum):
    IDEA = "idea"
    SCREENING = "screening"
    DEEP_DIVE = "deep_dive"
    THESIS_DEVELOPMENT = "thesis_development"
    MONITORING = "monitoring"
    ARCHIVED = "archived"


class ConvictionLevel(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# =============================================================================
# User Models
# =============================================================================

class User(Base):
    """User account."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    research_projects = relationship("ResearchProject", back_populates="user")
    workflows = relationship("Workflow", back_populates="user")
    watchlists = relationship("Watchlist", back_populates="user")


# =============================================================================
# Research Models
# =============================================================================

class ResearchProject(Base):
    """Investment research project."""
    __tablename__ = "research_projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(ResearchStatus), default=ResearchStatus.IDEA)
    
    # Investment thesis
    ticker = Column(String(20), index=True)
    company_name = Column(String(255))
    sector = Column(String(100))
    industry = Column(String(100))
    
    # Thesis details
    thesis_summary = Column(Text)
    bull_case = Column(Text)
    bear_case = Column(Text)
    key_catalysts = Column(JSONB, default=list)
    key_risks = Column(JSONB, default=list)
    
    # Valuation
    target_price = Column(Float)
    current_price = Column(Float)
    conviction_level = Column(Enum(ConvictionLevel))
    position_size_recommendation = Column(Float)
    
    # Metadata
    tags = Column(JSONB, default=list)
    sources = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="research_projects")
    notes = relationship("ResearchNote", back_populates="project")
    documents = relationship("ResearchDocument", back_populates="project")
    
    __table_args__ = (
        Index("ix_research_projects_user_ticker", "user_id", "ticker"),
    )


class ResearchNote(Base):
    """Research note within a project."""
    __tablename__ = "research_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    note_type = Column(String(50))  # analysis, meeting, news, etc.
    
    # AI-generated metadata
    summary = Column(Text)
    key_points = Column(JSONB, default=list)
    sentiment = Column(String(20))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("ResearchProject", back_populates="notes")


class ResearchDocument(Base):
    """Document attached to a research project."""
    __tablename__ = "research_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    extracted_text = Column(Text)
    embedding_id = Column(String(100))  # Reference to vector DB
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("ResearchProject", back_populates="documents")


# =============================================================================
# Workflow Models
# =============================================================================

class Workflow(Base):
    """Workflow definition and execution."""
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    workflow_type = Column(String(100), nullable=False)  # screening, due_diligence, etc.
    
    # Configuration
    config = Column(JSONB, default=dict)
    schedule = Column(String(100))  # Cron expression for scheduled workflows
    
    # Status
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="workflows")
    runs = relationship("WorkflowRun", back_populates="workflow")


class WorkflowRun(Base):
    """Individual workflow execution run."""
    __tablename__ = "workflow_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Input/Output
    input_data = Column(JSONB, default=dict)
    output_data = Column(JSONB, default=dict)
    error_message = Column(Text)
    
    # Metrics
    duration_seconds = Column(Float)
    tokens_used = Column(Integer, default=0)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="runs")
    tasks = relationship("AgentTaskRecord", back_populates="workflow_run")


class AgentTaskRecord(Base):
    """Record of an agent task execution."""
    __tablename__ = "agent_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"))
    
    task_id = Column(String(100), unique=True, nullable=False)
    agent_type = Column(String(100), nullable=False, index=True)
    prompt_name = Column(String(100), nullable=False)
    
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(String(20), default="normal")
    
    # Execution details
    input_data = Column(JSONB, default=dict)
    output_data = Column(JSONB, default=dict)
    error_message = Column(Text)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Metrics
    duration_seconds = Column(Float)
    tokens_used = Column(Integer, default=0)
    model_used = Column(String(100))
    
    # Relationships
    workflow_run = relationship("WorkflowRun", back_populates="tasks")
    
    __table_args__ = (
        Index("ix_agent_tasks_agent_type_status", "agent_type", "status"),
    )


# =============================================================================
# Market Data Models
# =============================================================================

class Watchlist(Base):
    """User watchlist."""
    __tablename__ = "watchlists"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist")


class WatchlistItem(Base):
    """Item in a watchlist."""
    __tablename__ = "watchlist_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watchlist_id = Column(UUID(as_uuid=True), ForeignKey("watchlists.id"), nullable=False)
    
    ticker = Column(String(20), nullable=False)
    company_name = Column(String(255))
    notes = Column(Text)
    
    # Alerts
    price_alert_above = Column(Float)
    price_alert_below = Column(Float)
    
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="items")
    
    __table_args__ = (
        UniqueConstraint("watchlist_id", "ticker", name="uq_watchlist_ticker"),
    )


class ScreenerResult(Base):
    """Results from stock screening."""
    __tablename__ = "screener_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    screener_name = Column(String(255), nullable=False)
    screener_config = Column(JSONB, default=dict)
    
    ticker = Column(String(20), nullable=False, index=True)
    company_name = Column(String(255))
    sector = Column(String(100))
    industry = Column(String(100))
    
    # Screening scores
    overall_score = Column(Float)
    scores_breakdown = Column(JSONB, default=dict)
    
    # Key metrics at time of screening
    market_cap = Column(Float)
    price = Column(Float)
    pe_ratio = Column(Float)
    revenue_growth = Column(Float)
    
    # AI analysis
    ai_summary = Column(Text)
    ai_recommendation = Column(String(50))
    
    screened_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_screener_results_screener_score", "screener_name", "overall_score"),
    )


# =============================================================================
# Prompt Management Models
# =============================================================================

class PromptTemplate(Base):
    """Prompt template storage."""
    __tablename__ = "prompt_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(255), unique=True, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100))
    
    description = Column(Text)
    template = Column(Text, nullable=False)
    
    # Variables in the template
    variables = Column(JSONB, default=list)
    
    # Metadata
    source = Column(String(100))  # wall_street_prompts, notion, custom
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    avg_tokens = Column(Integer)
    avg_latency_ms = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_prompt_templates_category_active", "category", "is_active"),
    )


# =============================================================================
# Knowledge Base Models
# =============================================================================

class KnowledgeDocument(Base):
    """Document in the knowledge base."""
    __tablename__ = "knowledge_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(1000))
    source_type = Column(String(100))  # sec_filing, news, research, etc.
    
    # Associated entities
    tickers = Column(JSONB, default=list)
    sectors = Column(JSONB, default=list)
    topics = Column(JSONB, default=list)
    
    # Vector embedding reference
    embedding_id = Column(String(100))
    embedding_model = Column(String(100))
    
    # Metadata
    published_at = Column(DateTime)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_knowledge_documents_source_type", "source_type"),
    )
