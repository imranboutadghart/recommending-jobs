"""Job listing data models"""
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.database.db import Base


# Pydantic models for API requests/responses
class JobListing(BaseModel):
    """Standardized job listing"""
    id: Optional[str] = Field(None, description="Unique job ID")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description")
    location: str = Field(..., description="Job location")
    skills: List[str] = Field(default_factory=list, description="Required skills")
    remote: bool = Field(default=False, description="Remote work flag")
    salary_min: Optional[float] = Field(None, description="Minimum salary")
    salary_max: Optional[float] = Field(None, description="Maximum salary")
    url: Optional[str] = Field(None, description="Job posting URL")
    source: str = Field(..., description="Data source (adzuna, jooble, mock)")
    posted_date: Optional[str] = Field(None, description="When job was posted")
    
    class Config:
        from_attributes = True


class MatchExplanation(BaseModel):
    """Explanation of job match score"""
    overall_score: float = Field(..., description="Overall match score (0-100)")
    title_score: float = Field(..., description="Title match score (0-100)")
    skills_score: float = Field(..., description="Skills match score (0-100)")
    experience_score: float = Field(..., description="Experience match score (0-100)")
    embedding_score: float = Field(..., description="Semantic similarity score (0-100)")
    matched_skills: List[str] = Field(default_factory=list, description="Skills that match")
    missing_skills: List[str] = Field(default_factory=list, description="Skills user lacks")
    explanation: str = Field(..., description="Human-readable explanation")


class JobMatch(BaseModel):
    """Job listing with match information"""
    job: JobListing
    match_score: float = Field(..., description="Overall match score (0-100)")
    explanation: MatchExplanation


class JobSearchFilters(BaseModel):
    """Filters for job search"""
    location: Optional[str] = Field(None, description="Filter by location")
    remote_only: bool = Field(default=False, description="Only remote jobs")
    min_salary: Optional[float] = Field(None, description="Minimum salary")
    max_salary: Optional[float] = Field(None, description="Maximum salary")
    keywords: Optional[str] = Field(None, description="Search keywords")


class RecommendationRequest(BaseModel):
    """Request model for getting recommendations"""
    user_id: int = Field(..., description="User profile ID")
    filters: Optional[JobSearchFilters] = Field(default=None, description="Search filters")
    limit: int = Field(default=20, description="Number of results to return")


# SQLAlchemy ORM models
class SavedJobDB(Base):
    """Saved jobs database table"""
    __tablename__ = "saved_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    job_id = Column(String, nullable=False)
    job_data = Column(JSON, nullable=False)  # Store complete job listing
    match_score = Column(Float, nullable=True)
    saved_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Composite unique constraint to prevent duplicate saves
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class JobCacheDB(Base):
    """Cache for job listings to reduce API calls"""
    __tablename__ = "job_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)
    query = Column(String, nullable=False)
    location = Column(String, nullable=True)
    jobs_data = Column(JSON, nullable=False)  # Cached job listings
    cached_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
