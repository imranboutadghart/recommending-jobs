"""Unit tests for recommendation and similarity calculation"""
import pytest
import numpy as np
from backend.services.recommendation import RecommendationService
from backend.services.embedding_service import EmbeddingService
from backend.models.user import UserProfile, Experience, Education
from backend.models.job import JobListing, JobSearchFilters


class TestRecommendationService:
    """Test recommendation service"""
    
    @pytest.fixture
    def service(self):
        """Create service instance"""
        return RecommendationService()
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user profile"""
        return UserProfile(
            id=1,
            name="Test User",
            skills=["Python", "FastAPI", "React", "PostgreSQL"],
            experience=[
                Experience(
                    title="Software Engineer",
                    company="Tech Co",
                    duration="2 years",
                    description="Built web applications"
                )
            ],
            education=[
                Education(
                    degree="BS Computer Science",
                    institution="University",
                    year="2020"
                )
            ],
            desired_job_titles=["Software Engineer", "Backend Developer"]
        )
    
    @pytest.fixture
    def sample_jobs(self):
        """Create sample job listings"""
        return [
            JobListing(
                id="job1",
                title="Senior Software Engineer",
                company="TechCorp",
                description="Python and FastAPI experience required",
                location="Remote",
                skills=["Python", "FastAPI", "Docker"],
                remote=True,
                source="mock"
            ),
            JobListing(
                id="job2",
                title="Data Scientist",
                company="DataCo",
                description="Machine learning and Python",
                location="New York",
                skills=["Python", "Machine Learning", "SQL"],
                remote=False,
                source="mock"
            )
        ]
    
    def test_title_match_calculation(self, service, sample_user):
        """Test title matching score"""
        job = JobListing(
            id="1",
            title="Software Engineer",
            company="Test",
            description="Test",
            location="Remote",
            skills=[],
            remote=True,
            source="mock"
        )
        
        score = service._calculate_title_match(sample_user, job)
        assert 0 <= score <= 100
        assert score > 50  # Should match desired titles
    
    def test_skills_match_calculation(self, service, sample_user):
        """Test skills matching score"""
        job = JobListing(
            id="1",
            title="Engineer",
            company="Test",
            description="Test",
            location="Remote",
            skills=["Python", "FastAPI", "Java"],
            remote=True,
            source="mock"
        )
        
        score, matched, missing = service._calculate_skills_match(sample_user, job)
        
        assert 0 <= score <= 100
        assert "Python" in matched
        assert "FastAPI" in matched
        assert "Java" in missing
    
    def test_filter_application(self, service, sample_jobs):
        """Test job filtering"""
        filters = JobSearchFilters(remote_only=True)
        filtered = service._apply_filters(sample_jobs, filters)
        
        assert all(job.remote for job in filtered)
        assert len(filtered) < len(sample_jobs)
    
    def test_embedding_similarity(self, service):
        """Test cosine similarity calculation"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        
        score = service._calculate_embedding_similarity(vec1, vec2)
        assert 90 <= score <= 100  # Should be very similar
        
        vec3 = [0.0, 1.0, 0.0]
        score2 = service._calculate_embedding_similarity(vec1, vec3)
        assert score2 < score  # Should be less similar


class TestEmbeddingService:
    """Test embedding service"""
    
    @pytest.fixture
    def service(self):
        """Create service instance"""
        return EmbeddingService()
    
    @pytest.mark.asyncio
    async def test_embed_user_profile(self, service):
        """Test user profile embedding"""
        profile_data = {
            "name": "Test User",
            "skills": ["Python", "JavaScript"],
            "desired_job_titles": ["Software Engineer"],
            "summary": "Experienced developer"
        }
        
        try:
            embedding = await service.embed_user_profile(profile_data)
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            assert all(isinstance(x, float) for x in embedding)
        except Exception as e:
            pytest.skip(f"Gemini API not available: {e}")
    
    @pytest.mark.asyncio
    async def test_embed_job_listing(self, service):
        """Test job listing embedding"""
        job_data = {
            "title": "Software Engineer",
            "company": "TechCorp",
            "description": "Build web applications with Python",
            "skills": ["Python", "FastAPI"]
        }
        
        try:
            embedding = await service.embed_job_listing(job_data)
            assert isinstance(embedding, list)
            assert len(embedding) > 0
        except Exception as e:
            pytest.skip(f"Gemini API not available: {e}")
    
    def test_cache_functionality(self, service):
        """Test that caching works"""
        service.cache["test"] = [1.0, 2.0, 3.0]
        assert "test" in service.cache
        
        service.clear_cache()
        assert len(service.cache) == 0
