"""Job aggregation service - fetch jobs from multiple platforms"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import aiohttp
import asyncio
from backend.config import settings
from backend.models.job import JobListing

logger = logging.getLogger(__name__)


class JobAggregator:
    """Aggregate job listings from multiple sources"""
    
    def __init__(self):
        self.sources = []
        
        # Add sources based on available API keys
        if settings.adzuna_api_key and settings.adzuna_app_id:
            self.sources.append('adzuna')
        if settings.jooble_api_key:
            self.sources.append('jooble')
        
        # Always include mock fallback
        self.sources.append('mock')
        
        logger.info(f"Initialized JobAggregator with sources: {self.sources}")
    
    async def fetch_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        max_results: int = 50
    ) -> List[JobListing]:
        """
        Fetch jobs from all available sources
        
        Args:
            query: Search query (job title, keywords)
            location: Location filter
            max_results: Maximum results per source
        
        Returns:
            List of standardized job listings
        """
        location = location or settings.default_location
        
        # Fetch from all sources concurrently
        tasks = []
        
        if 'adzuna' in self.sources:
            tasks.append(self._fetch_adzuna(query, location, max_results))
        if 'jooble' in self.sources:
            tasks.append(self._fetch_jooble(query, location, max_results))
        if 'mock' in self.sources:
            tasks.append(self._fetch_mock_jobs(query, location, max_results))
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_jobs = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching jobs: {result}")
                continue
            all_jobs.extend(result)
        
        logger.info(f"Fetched {len(all_jobs)} total jobs for query: {query}")
        return all_jobs
    
    async def _fetch_adzuna(
        self,
        query: str,
        location: str,
        max_results: int
    ) -> List[JobListing]:
        """Fetch jobs from Adzuna API"""
        try:
            # Adzuna API endpoint
            country = "us"  # Default to US, could be made configurable
            url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
            
            params = {
                'app_id': settings.adzuna_app_id,
                'app_key': settings.adzuna_api_key,
                'what': query,
                'where': location,
                'results_per_page': min(max_results, 50),
                'content-type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        jobs = []
                        
                        for job in data.get('results', []):
                            jobs.append(JobListing(
                                id=f"adzuna_{job.get('id', '')}",
                                title=job.get('title', ''),
                                company=job.get('company', {}).get('display_name', 'Unknown'),
                                description=job.get('description', ''),
                                location=job.get('location', {}).get('display_name', location),
                                skills=self._extract_skills(job.get('description', '')),
                                remote='remote' in job.get('description', '').lower(),
                                salary_min=job.get('salary_min'),
                                salary_max=job.get('salary_max'),
                                url=job.get('redirect_url', ''),
                                source='adzuna',
                                posted_date=job.get('created', '')
                            ))
                        
                        logger.info(f"Fetched {len(jobs)} jobs from Adzuna")
                        return jobs
                    else:
                        logger.error(f"Adzuna API error: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error fetching from Adzuna: {e}")
            return []
    
    async def _fetch_jooble(
        self,
        query: str,
        location: str,
        max_results: int
    ) -> List[JobListing]:
        """Fetch jobs from Jooble API"""
        try:
            url = "https://jooble.org/api/" + settings.jooble_api_key
            
            payload = {
                "keywords": query,
                "location": location,
                "page": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        jobs = []
                        
                        for job in data.get('jobs', [])[:max_results]:
                            jobs.append(JobListing(
                                id=f"jooble_{job.get('id', '')}",
                                title=job.get('title', ''),
                                company=job.get('company', 'Unknown'),
                                description=job.get('snippet', ''),
                                location=job.get('location', location),
                                skills=self._extract_skills(job.get('snippet', '')),
                                remote='remote' in job.get('snippet', '').lower(),
                                salary_min=None,
                                salary_max=None,
                                url=job.get('link', ''),
                                source='jooble',
                                posted_date=job.get('updated', '')
                            ))
                        
                        logger.info(f"Fetched {len(jobs)} jobs from Jooble")
                        return jobs
                    else:
                        logger.error(f"Jooble API error: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error fetching from Jooble: {e}")
            return []
    
    async def _fetch_mock_jobs(
        self,
        query: str,
        location: str,
        max_results: int
    ) -> List[JobListing]:
        """Generate mock job listings for testing"""
        # This provides fallback data when no real APIs are available
        mock_jobs = [
            JobListing(
                id="mock_1",
                title="Senior Software Engineer",
                company="TechCorp Inc",
                description="We are looking for a senior software engineer with experience in Python, FastAPI, and React. You will work on building scalable web applications and APIs. Requirements: 5+ years of experience, strong knowledge of Python, experience with cloud platforms (AWS/GCP), RESTful API design.",
                location="San Francisco, CA",
                skills=["Python", "FastAPI", "React", "AWS", "REST APIs", "Docker"],
                remote=True,
                salary_min=120000,
                salary_max=180000,
                url="https://example.com/job/1",
                source="mock",
                posted_date="2025-12-10"
            ),
            JobListing(
                id="mock_2",
                title="Data Scientist",
                company="DataAnalytics Co",
                description="Join our data science team to build ML models and analyze large datasets. Requirements: Python, machine learning, SQL, pandas, scikit-learn. Experience with deep learning is a plus.",
                location="New York, NY",
                skills=["Python", "Machine Learning", "SQL", "Pandas", "Scikit-learn", "TensorFlow"],
                remote=False,
                salary_min=100000,
                salary_max=150000,
                url="https://example.com/job/2",
                source="mock",
                posted_date="2025-12-11"
            ),
            JobListing(
                id="mock_3",
                title="Full Stack Developer",
                company="WebDev Solutions",
                description="Looking for a full stack developer proficient in JavaScript, Node.js, React, and MongoDB. You will build modern web applications from frontend to backend.",
                location="Remote",
                skills=["JavaScript", "Node.js", "React", "MongoDB", "Express", "HTML", "CSS"],
                remote=True,
                salary_min=90000,
                salary_max=130000,
                url="https://example.com/job/3",
                source="mock",
                posted_date="2025-12-09"
            ),
            JobListing(
                id="mock_4",
                title="DevOps Engineer",
                company="CloudTech Inc",
                description="We need a DevOps engineer to manage our cloud infrastructure. Experience with Kubernetes, Docker, CI/CD, and AWS required. You will automate deployments and ensure system reliability.",
                location="Austin, TX",
                skills=["Kubernetes", "Docker", "AWS", "CI/CD", "Python", "Terraform", "Jenkins"],
                remote=True,
                salary_min=110000,
                salary_max=160000,
                url="https://example.com/job/4",
                source="mock",
                posted_date="2025-12-08"
            ),
            JobListing(
                id="mock_5",
                title="Machine Learning Engineer",
                company="AI Innovations",
                description="Build and deploy ML models at scale. Requirements: Python, PyTorch/TensorFlow, MLOps, cloud platforms. Experience with NLP or computer vision is preferred.",
                location="Seattle, WA",
                skills=["Python", "PyTorch", "TensorFlow", "MLOps", "Docker", "Kubernetes", "NLP"],
                remote=True,
                salary_min=130000,
                salary_max=190000,
                url="https://example.com/job/5",
                source="mock",
                posted_date="2025-12-12"
            ),
        ]
        
        # Filter by query keywords
        query_lower = query.lower()
        filtered_jobs = [
            job for job in mock_jobs
            if query_lower in job.title.lower() or query_lower in job.description.lower()
        ]
        
        # If no matches, return all mock jobs
        if not filtered_jobs:
            filtered_jobs = mock_jobs
        
        logger.info(f"Generated {len(filtered_jobs[:max_results])} mock jobs")
        return filtered_jobs[:max_results]
    
    def _extract_skills(self, description: str) -> List[str]:
        """
        Extract skills from job description using keyword matching
        This is a simple implementation - could be enhanced with NLP
        """
        # Common technical skills to look for
        skill_keywords = [
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'Go', 'Rust',
            'React', 'Angular', 'Vue', 'Node.js', 'Express', 'Django', 'Flask', 'FastAPI',
            'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
            'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision',
            'TensorFlow', 'PyTorch', 'Scikit-learn',
            'Git', 'CI/CD', 'REST API', 'GraphQL',
            'HTML', 'CSS', 'TypeScript'
        ]
        
        found_skills = []
        description_lower = description.lower()
        
        for skill in skill_keywords:
            if skill.lower() in description_lower:
                found_skills.append(skill)
        
        return found_skills


# Global instance
job_aggregator = JobAggregator()
