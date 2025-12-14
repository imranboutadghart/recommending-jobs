"""Unit tests for job aggregation service"""
import pytest
from backend.services.job_aggregator import JobAggregator
from backend.models.job import JobListing


class TestJobAggregator:
    """Test job aggregation functionality"""
    
    @pytest.fixture
    def aggregator(self):
        """Create aggregator instance"""
        return JobAggregator()
    
    @pytest.mark.asyncio
    async def test_mock_jobs_generation(self, aggregator):
        """Test that mock jobs are generated correctly"""
        jobs = await aggregator._fetch_mock_jobs("software engineer", "Remote", 10)
        
        assert isinstance(jobs, list)
        assert len(jobs) > 0
        assert all(isinstance(job, JobListing) for job in jobs)
        
        # Check first job has required fields
        job = jobs[0]
        assert job.title
        assert job.company
        assert job.description
        assert job.source == "mock"
    
    @pytest.mark.asyncio
    async def test_fetch_jobs_with_query(self, aggregator):
        """Test job fetching with search query"""
        jobs = await aggregator.fetch_jobs("python developer", "San Francisco", 5)
        
        assert isinstance(jobs, list)
        # Should have at least mock jobs
        assert len(jobs) > 0
    
    def test_skill_extraction(self, aggregator):
        """Test skill extraction from job description"""
        description = "We need a developer with Python, React, and AWS experience"
        skills = aggregator._extract_skills(description)
        
        assert "Python" in skills
        assert "React" in skills
        assert "AWS" in skills
    
    @pytest.mark.asyncio
    async def test_multiple_sources(self, aggregator):
        """Test that jobs are aggregated from available sources"""
        jobs = await aggregator.fetch_jobs("data scientist", "New York", 20)
        
        # Should have jobs from at least mock source
        sources = set(job.source for job in jobs)
        assert "mock" in sources
