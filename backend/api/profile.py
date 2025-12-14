"""Profile management API endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
import tempfile

from backend.database.db import get_db
from backend.models.user import (
    UserProfile,
    UserProfileDB,
    ProfileCreate,
    ProfileUpdate,
    ExtractedResume
)
from backend.services.resume_extractor import resume_extractor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.post("/upload-resume", response_model=ExtractedResume)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and extract structured data from resume
    
    Accepts PDF or DOCX files
    Returns extracted resume data for user confirmation
    """
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.docx')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload PDF or DOCX file."
        )
    
    try:
        # Save uploaded file temporarily
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        logger.info(f"Processing resume file: {file.filename}")
        
        # Extract data from file
        extracted_data = await resume_extractor.extract_from_file(tmp_path)
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        logger.info(f"Successfully extracted resume for: {extracted_data.name}")
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error processing resume: {e}")
        # Clean up temp file if it exists
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm", response_model=UserProfile)
async def confirm_profile(
    profile: ProfileCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create or update user profile after confirmation/editing
    
    Users can modify the extracted data before saving
    """
    try:
        # Check if user with this email already exists
        if profile.email:
            result = await db.execute(
                select(UserProfileDB).where(UserProfileDB.email == profile.email)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                # Update existing profile
                for key, value in profile.model_dump(exclude_unset=True).items():
                    if value is not None:
                        setattr(existing_user, key, value)
                await db.commit()
                await db.refresh(existing_user)
                logger.info(f"Updated profile for user ID: {existing_user.id}")
                return UserProfile.model_validate(existing_user)
        
        # Create new profile
        db_profile = UserProfileDB(**profile.model_dump())
        db.add(db_profile)
        await db.commit()
        await db.refresh(db_profile)
        
        logger.info(f"Created new profile for: {db_profile.name} (ID: {db_profile.id})")
        return UserProfile.model_validate(db_profile)
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error saving profile: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving profile: {str(e)}")


@router.get("/{user_id}", response_model=UserProfile)
async def get_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user profile by ID"""
    result = await db.execute(
        select(UserProfileDB).where(UserProfileDB.id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return UserProfile.model_validate(profile)


@router.put("/{user_id}", response_model=UserProfile)
async def update_profile(
    user_id: int,
    profile_update: ProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    result = await db.execute(
        select(UserProfileDB).where(UserProfileDB.id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Update fields
    update_data = profile_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(profile, key, value)
    
    await db.commit()
    await db.refresh(profile)
    
    logger.info(f"Updated profile for user ID: {user_id}")
    return UserProfile.model_validate(profile)


@router.get("/", response_model=List[UserProfile])
async def list_profiles(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """List all user profiles (for testing/admin)"""
    result = await db.execute(
        select(UserProfileDB).offset(skip).limit(limit)
    )
    profiles = result.scalars().all()
    
    return [UserProfile.model_validate(p) for p in profiles]


@router.delete("/{user_id}")
async def delete_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    """Delete user profile"""
    result = await db.execute(
        select(UserProfileDB).where(UserProfileDB.id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    await db.delete(profile)
    await db.commit()
    
    logger.info(f"Deleted profile for user ID: {user_id}")
    return {"message": "Profile deleted successfully"}
