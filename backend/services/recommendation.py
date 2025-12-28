"""Recommendation service - rank jobs based on user profile"""
import logging
from typing import List, Dict, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from backend.models.job import JobListing, JobMatch, MatchExplanation, JobSearchFilters
from backend.models.user import UserProfile
from backend.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class RecommendationService:
    """Generate job recommendations using vector similarity and weighted scoring"""
    
    def __init__(self):
        # Weights for different matching components
        self.weights = {
            'title': 0.25,
            'skills': 0.40,
            'experience': 0.15,
            'embedding': 0.20
        }
    
    async def rank_jobs(
        self,
        user_profile: UserProfile,
        jobs: List[JobListing],
        filters: JobSearchFilters = None
    ) -> List[JobMatch]:
        """
        Rank jobs for a user based on multiple criteria
        
        Args:
            user_profile: User's profile
            jobs: List of job listings
            filters: Optional filters to apply
        
        Returns:
            List of JobMatch objects sorted by match score (highest first)
        """
        if not jobs:
            return []
        
        # Apply filters first
        filtered_jobs = self._apply_filters(jobs, filters)
        
        if not filtered_jobs:
            logger.warning("No jobs after applying filters")
            return []
        
        logger.info(f"Ranking {len(filtered_jobs)} jobs for user {user_profile.name}")
        
        # Generate embeddings
        user_embedding = await embedding_service.embed_user_profile(
            user_profile.model_dump()
        )
        
        job_embeddings = []
        for job in filtered_jobs:
            embedding = await embedding_service.embed_job_listing(
                job.model_dump()
            )
            job_embeddings.append(embedding)
        
        # Calculate scores for each job
        job_matches = []
        for i, job in enumerate(filtered_jobs):
            match = self._calculate_match(
                user_profile,
                job,
                user_embedding,
                job_embeddings[i]
            )
            job_matches.append(match)
        
        # Sort by match score (highest first)
        job_matches.sort(key=lambda x: x.match_score, reverse=True)
        
        logger.info(f"Ranked {len(job_matches)} jobs. Top score: {job_matches[0].match_score:.2f}")
        return job_matches
    
    def _apply_filters(
        self,
        jobs: List[JobListing],
        filters: JobSearchFilters
    ) -> List[JobListing]:
        """Apply search filters to job listings"""
        if not filters:
            return jobs
        
        filtered = jobs
        
        # Location filter
        if filters.location:
            filtered = [
                job for job in filtered
                if filters.location.lower() in job.location.lower()
            ]
        
        # Remote filter
        if filters.remote_only:
            filtered = [job for job in filtered if job.remote]
        
        # Salary filters
        if filters.min_salary is not None:
            filtered = [
                job for job in filtered
                if job.salary_max and job.salary_max >= filters.min_salary
            ]
        
        if filters.max_salary is not None:
            filtered = [
                job for job in filtered
                if job.salary_min and job.salary_min <= filters.max_salary
            ]
        
        # Keywords filter
        if filters.keywords:
            keywords_lower = filters.keywords.lower()
            filtered = [
                job for job in filtered
                if keywords_lower in job.title.lower() or keywords_lower in job.description.lower()
            ]
        
        logger.info(f"Filters applied: {len(jobs)} -> {len(filtered)} jobs")
        return filtered
    
    def _calculate_match(
        self,
        user_profile: UserProfile,
        job: JobListing,
        user_embedding: List[float],
        job_embedding: List[float]
    ) -> JobMatch:
        """Calculate match score and explanation for a single job"""
        
        # 1. Title Match Score
        title_score = self._calculate_title_match(user_profile, job)
        
        # 2. Skills Match Score
        skills_score, matched_skills, missing_skills = self._calculate_skills_match(
            user_profile, job
        )
        
        # 3. Experience Score (simplified - could be enhanced)
        experience_score = self._calculate_experience_match(user_profile, job)
        
        # 4. Embedding Similarity Score
        embedding_score = 0.0
        embedding_available = user_embedding is not None and job_embedding is not None
        
        if embedding_available:
            embedding_score = self._calculate_embedding_similarity(
                user_embedding, job_embedding
            )
            overall_score = (
                self.weights['title'] * title_score +
                self.weights['skills'] * skills_score +
                self.weights['experience'] * experience_score +
                self.weights['embedding'] * embedding_score
            )
        else:
            # Re-distribute weights if embedding is not available
            other_weights_sum = self.weights['title'] + self.weights['skills'] + self.weights['experience']
            overall_score = (
                (self.weights['title'] * title_score +
                 self.weights['skills'] * skills_score +
                 self.weights['experience'] * experience_score) / other_weights_sum
            )
        
        # Generate explanation
        explanation = self._generate_explanation(
            overall_score,
            title_score,
            skills_score,
            experience_score,
            embedding_score,
            matched_skills,
            missing_skills,
            user_profile,
            job,
            embedding_available
        )
        
        return JobMatch(
            job=job,
            match_score=round(overall_score, 2),
            explanation=explanation
        )
    
    def _calculate_title_match(
        self,
        user_profile: UserProfile,
        job: JobListing
    ) -> float:
        """Calculate how well job title matches desired roles"""
        if not user_profile.desired_job_titles:
            return 50.0  # Neutral score if no preferences
        
        job_title_lower = job.title.lower()
        
        # Check for exact or partial matches
        for desired_title in user_profile.desired_job_titles:
            desired_lower = desired_title.lower()
            
            # Exact match
            if desired_lower == job_title_lower:
                return 100.0
            
            # Partial match (either direction)
            if desired_lower in job_title_lower or job_title_lower in desired_lower:
                return 80.0
            
            # Word overlap
            desired_words = set(desired_lower.split())
            job_words = set(job_title_lower.split())
            overlap = desired_words & job_words
            if overlap:
                return 60.0 * (len(overlap) / max(len(desired_words), len(job_words)))
        
        return 20.0  # Low score if no match
    
    def _calculate_skills_match(
        self,
        user_profile: UserProfile,
        job: JobListing
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate skills match score
        
        Returns:
            Tuple of (score, matched_skills, missing_skills)
        """
        if not job.skills:
            return 50.0, [], []  # Neutral if job has no skill requirements
        
        user_skills_lower = {skill.lower() for skill in user_profile.skills}
        job_skills_lower = {skill.lower() for skill in job.skills}
        
        # Find matches and missing skills
        matched = user_skills_lower & job_skills_lower
        missing = job_skills_lower - user_skills_lower
        
        # Get original case for display
        matched_skills = [
            skill for skill in job.skills
            if skill.lower() in matched
        ]
        missing_skills = [
            skill for skill in job.skills
            if skill.lower() in missing
        ]
        
        # Calculate score based on match percentage
        if len(job_skills_lower) == 0:
            score = 50.0
        else:
            match_ratio = len(matched) / len(job_skills_lower)
            score = match_ratio * 100
        
        return score, matched_skills, missing_skills
    
    def _calculate_experience_match(
        self,
        user_profile: UserProfile,
        job: JobListing
    ) -> float:
        """
        Calculate experience relevance score
        Simple implementation based on experience count and keywords
        """
        if not user_profile.experience:
            return 30.0  # Low score for no experience
        
        # Award points for having experience
        base_score = 50.0
        
        # Check if job description mentions years of experience
        description_lower = job.description.lower()
        
        # Simple heuristic: more experience entries = higher score
        experience_count = len(user_profile.experience)
        if experience_count >= 3:
            base_score += 30.0
        elif experience_count >= 2:
            base_score += 20.0
        else:
            base_score += 10.0
        
        # Bonus if experience titles match job title keywords
        job_keywords = set(job.title.lower().split())
        for exp in user_profile.experience:
            exp_keywords = set(exp.title.lower().split())
            if job_keywords & exp_keywords:
                base_score += 10.0
                break
        
        return min(base_score, 100.0)
    
    def _calculate_embedding_similarity(
        self,
        user_embedding: List[float],
        job_embedding: List[float]
    ) -> float:
        """Calculate cosine similarity between embeddings"""
        user_vec = np.array(user_embedding).reshape(1, -1)
        job_vec = np.array(job_embedding).reshape(1, -1)
        
        similarity = cosine_similarity(user_vec, job_vec)[0][0]
        
        # Convert from [-1, 1] to [0, 100]
        score = (similarity + 1) / 2 * 100
        
        return score
    
    def _generate_explanation(
        self,
        overall_score: float,
        title_score: float,
        skills_score: float,
        experience_score: float,
        embedding_score: float,
        matched_skills: List[str],
        missing_skills: List[str],
        user_profile: UserProfile,
        job: JobListing,
        embedding_available: bool = True
    ) -> MatchExplanation:
        """Generate human-readable match explanation"""
        
        # Determine overall match quality
        if overall_score >= 80:
            quality = "Excellent"
        elif overall_score >= 60:
            quality = "Good"
        elif overall_score >= 40:
            quality = "Fair"
        else:
            quality = "Limited"
        
        # Build explanation text
        parts = [f"{quality} match ({overall_score:.0f}%)."]
        
        # Title match
        if title_score >= 70:
            parts.append("Job title aligns well with your desired roles.")
        elif title_score >= 40:
            parts.append("Job title partially matches your interests.")
        else:
            parts.append("Job title differs from your stated preferences.")
        
        # Skills match
        if matched_skills:
            parts.append(f"You have {len(matched_skills)} of the required skills.")
        if missing_skills and len(missing_skills) <= 3:
            parts.append(f"Consider developing: {', '.join(missing_skills[:3])}.")
        elif missing_skills:
            parts.append(f"You may need to develop {len(missing_skills)} additional skills.")
        
        # Semantic similarity
        if embedding_available:
            if embedding_score >= 70:
                parts.append("Strong semantic match between your profile and job description.")
        else:
            parts.append("Deep AI Match (Embeddings) currently unavailable, falling back to basic matching.")
        
        explanation_text = " ".join(parts)
        
        return MatchExplanation(
            overall_score=round(overall_score, 2),
            title_score=round(title_score, 2),
            skills_score=round(skills_score, 2),
            experience_score=round(experience_score, 2),
            embedding_score=round(embedding_score, 2),
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            explanation=explanation_text
        )


# Global instance
recommendation_service = RecommendationService()
