"""Job search and saved jobs API endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from backend.database.db import get_db
from backend.models.job import JobListing, SavedJobDB
from backend.models.user import UserProfileDB
from backend.services.job_aggregator import job_aggregator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.get("/search", response_model=List[JobListing])
async def search_jobs(
    query: str = Query(..., description="Search query (job title, keywords)"),
    location: Optional[str] = Query(None, description="Location filter"),
    max_results: int = Query(50, description="Maximum results per source")
):
    """
    Search for jobs across all available platforms
    
    Aggregates results from multiple sources:
    - Adzuna (if API key configured)
    - Jooble (if API key configured)
    - Mock data (always available as fallback)
    """
    try:
        logger.info(f"Searching jobs: query='{query}', location='{location}'")
        
        jobs = await job_aggregator.fetch_jobs(
            query=query,
            location=location,
            max_results=max_results
        )
        
        logger.info(f"Found {len(jobs)} jobs")
        return jobs
        
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")


@router.get("/saved/{user_id}", response_model=List[JobListing])
async def get_saved_jobs(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all saved jobs for a user"""
    # Verify user exists
    result = await db.execute(
        select(UserProfileDB).where(UserProfileDB.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get saved jobs
    result = await db.execute(
        select(SavedJobDB).where(SavedJobDB.user_id == user_id)
    )
    saved_jobs = result.scalars().all()
    
    # Convert to JobListing objects
    jobs = [JobListing(**job.job_data) for job in saved_jobs]
    
    logger.info(f"Retrieved {len(jobs)} saved jobs for user {user_id}")
    return jobs


@router.post("/save")
async def save_job(
    user_id: int,
    job: JobListing,
    match_score: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    """Save a job to user's favorites"""
    # Verify user exists
    result = await db.execute(
        select(UserProfileDB).where(UserProfileDB.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already saved
    result = await db.execute(
        select(SavedJobDB).where(
            and_(
                SavedJobDB.user_id == user_id,
                SavedJobDB.job_id == job.id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return {"message": "Job already saved", "id": existing.id}
    
    # Save job
    saved_job = SavedJobDB(
        user_id=user_id,
        job_id=job.id,
        job_data=job.model_dump(),
        match_score=match_score
    )
    db.add(saved_job)
    await db.commit()
    await db.refresh(saved_job)
    
    logger.info(f"User {user_id} saved job {job.id}")
    return {"message": "Job saved successfully", "id": saved_job.id}


@router.delete("/save/{user_id}/{job_id}")
async def unsave_job(
    user_id: int,
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a job from saved jobs"""
    result = await db.execute(
        select(SavedJobDB).where(
            and_(
                SavedJobDB.user_id == user_id,
                SavedJobDB.job_id == job_id
            )
        )
    )
    saved_job = result.scalar_one_or_none()
    
    if not saved_job:
        raise HTTPException(status_code=404, detail="Saved job not found")
    
    await db.delete(saved_job)
    await db.commit()
    
    logger.info(f"User {user_id} removed saved job {job_id}")
    return {"message": "Job removed from saved jobs"}
