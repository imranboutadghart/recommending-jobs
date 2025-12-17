"""User profile data models"""
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from backend.database.db import Base


# Pydantic models for API requests/responses
class Experience(BaseModel):
    """Work experience entry"""
    title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    duration: Optional[str] = Field(None, description="Duration (e.g., '2 years', 'Jan 2020 - Dec 2022')")
    description: Optional[str] = Field(None, description="Job description")


class Education(BaseModel):
    """Education entry"""
    degree: Optional[str] = Field(None, description="Degree name")
    institution: Optional[str] = Field(None, description="School/University name")
    year: Optional[str] = Field(None, description="Graduation year or period")
    field: Optional[str] = Field(None, description="Field of study")


class UserProfile(BaseModel):
    """Complete user profile"""
    id: Optional[int] = None
    name: str = Field(..., description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    experience: List[Experience] = Field(default_factory=list, description="Work experience")
    education: List[Education] = Field(default_factory=list, description="Education history")
    desired_job_titles: List[str] = Field(
        default_factory=list,
        description="Desired job titles/roles"
    )
    summary: Optional[str] = Field(None, description="Professional summary")
    location: Optional[str] = Field(None, description="Current location")
    
    model_config = ConfigDict(from_attributes=True)


class ExtractedResume(BaseModel):
    """Resume data extracted from Gemini API"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    summary: Optional[str] = None
    location: Optional[str] = None


class ProfileCreate(BaseModel):
    """Request model for creating a profile"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    desired_job_titles: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    location: Optional[str] = None


class ProfileUpdate(BaseModel):
    """Request model for updating a profile"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[Experience]] = None
    education: Optional[List[Education]] = None
    desired_job_titles: Optional[List[str]] = None
    summary: Optional[str] = None
    location: Optional[str] = None


# SQLAlchemy ORM models
class UserProfileDB(Base):
    """User profile database table"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, nullable=True)
    skills = Column(JSON, default=[])  # Stored as JSON array
    experience = Column(JSON, default=[])  # Stored as JSON array of objects
    education = Column(JSON, default=[])  # Stored as JSON array of objects
    desired_job_titles = Column(JSON, default=[])  # Stored as JSON array
    summary = Column(String, nullable=True)
    location = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
