"""Job recommendation API endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from backend.database.db import get_db
from backend.models.job import (
    JobMatch,
    RecommendationRequest,
    JobSearchFilters
)
from backend.models.user import UserProfile, UserProfileDB
from backend.services.job_aggregator import job_aggregator
from backend.services.recommendation import recommendation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


@router.post("/", response_model=List[JobMatch])
async def get_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get personalized job recommendations for a user
    
    This endpoint:
    1. Fetches the user's profile
    2. Searches for relevant jobs
    3. Ranks jobs using vector similarity and weighted scoring
    4. Returns top matches with explanations
    """
    try:
        # Get user profile
        result = await db.execute(
            select(UserProfileDB).where(UserProfileDB.id == request.user_id)
        )
        user_profile_db = result.scalar_one_or_none()
        
        if not user_profile_db:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user_profile = UserProfile.model_validate(user_profile_db)
        
        logger.info(f"Generating recommendations for user: {user_profile.name} (ID: {request.user_id})")
        
        # Determine search query from user's desired job titles or skills
        if user_profile.desired_job_titles:
            query = " ".join(user_profile.desired_job_titles)
        elif user_profile.skills:
            query = " ".join(user_profile.skills[:3])  # Use top 3 skills
        else:
            query = "software"  # Default fallback
        
        # Get location from filters or user profile
        location = None
        if request.filters and request.filters.location:
            location = request.filters.location
        elif user_profile.location:
            location = user_profile.location
        
        # Fetch jobs
        logger.info(f"Fetching jobs with query: '{query}', location: '{location}'")
        jobs = await job_aggregator.fetch_jobs(
            query=query,
            location=location,
            max_results=100  # Fetch more to rank from
        )
        
        if not jobs:
            logger.warning("No jobs found")
            return []
        
        logger.info(f"Fetched {len(jobs)} jobs, now ranking...")
        
        # Rank jobs
        filters = request.filters or JobSearchFilters()
        ranked_jobs = await recommendation_service.rank_jobs(
            user_profile=user_profile,
            jobs=jobs,
            filters=filters
        )
        
        # Limit results
        limited_results = ranked_jobs[:request.limit]
        
        logger.info(f"Returning top {len(limited_results)} recommendations")
        return limited_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.get("/quick/{user_id}", response_model=List[JobMatch])
async def get_quick_recommendations(
    user_id: int,
    limit: int = 10,
    remote_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Quick recommendations endpoint with simple parameters
    
    Useful for quick testing or simpler UI flows
    """
    filters = JobSearchFilters(remote_only=remote_only) if remote_only else None
    
    request = RecommendationRequest(
        user_id=user_id,
        filters=filters,
        limit=limit
    )
    
    return await get_recommendations(request, db)
