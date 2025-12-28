"""Embedding service using Google Gemini API"""
import logging
from typing import List, Dict
import asyncio
import google.generativeai as genai
from google.api_core import exceptions
from backend.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.gemini_api_key)


class EmbeddingService:
    """Generate embeddings using Gemini embedding model"""
    
    def __init__(self):
        self.model_name = settings.embedding_model
        self.cache: Dict[str, List[float]] = {}  # Simple in-memory cache
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        # Check cache
        if text in self.cache:
            logger.debug(f"Cache hit for text: {text[:50]}...")
            return self.cache[text]
        
        try:
            # Genai doesn't have async API, so we run in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document"
                )
            )
            
            embedding = result['embedding']
            
            # Cache the result
            self.cache[text] = embedding
            
            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            return embedding
            
        except exceptions.ResourceExhausted as e:
            logger.warning(f"API quota exceeded for embeddings: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        # Process in batches to avoid rate limits
        batch_size = settings.max_embedding_batch_size
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Generate embeddings concurrently within batch
            tasks = [self.generate_embedding(text) for text in batch]
            batch_embeddings = await asyncio.gather(*tasks)
            all_embeddings.extend(batch_embeddings)
            
            logger.info(f"Processed batch {i//batch_size + 1}: {len(batch)} texts")
        
        return all_embeddings
    
    async def embed_user_profile(self, profile_data: dict) -> List[float]:
        """
        Create embedding for user profile by combining key fields
        
        Args:
            profile_data: Dictionary with user profile information
        
        Returns:
            Embedding vector for the user profile
        """
        # Combine relevant profile fields into a single text
        parts = []
        
        # Add desired job titles
        if profile_data.get('desired_job_titles'):
            parts.append(f"Desired roles: {', '.join(profile_data['desired_job_titles'])}")
        
        # Add skills
        if profile_data.get('skills'):
            parts.append(f"Skills: {', '.join(profile_data['skills'])}")
        
        # Add summary
        if profile_data.get('summary'):
            parts.append(f"Summary: {profile_data['summary']}")
        
        # Add experience descriptions
        if profile_data.get('experience'):
            exp_texts = []
            for exp in profile_data['experience']:
                exp_text = f"{exp.get('title', '')} at {exp.get('company', '')}"
                if exp.get('description'):
                    exp_text += f": {exp['description']}"
                exp_texts.append(exp_text)
            parts.append(f"Experience: {' '.join(exp_texts)}")
        
        # Combine all parts
        profile_text = ". ".join(parts)
        
        logger.info(f"Creating embedding for user profile (length: {len(profile_text)} chars)")
        return await self.generate_embedding(profile_text)
    
    async def embed_job_listing(self, job: dict) -> List[float]:
        """
        Create embedding for job listing
        
        Args:
            job: Dictionary with job information
        
        Returns:
            Embedding vector for the job listing
        """
        # Combine job fields
        parts = [
            f"Title: {job.get('title', '')}",
            f"Company: {job.get('company', '')}",
            f"Description: {job.get('description', '')}",
        ]
        
        if job.get('skills'):
            parts.append(f"Required skills: {', '.join(job['skills'])}")
        
        job_text = ". ".join(parts)
        
        return await self.generate_embedding(job_text)
    
    def clear_cache(self):
        """Clear the embedding cache"""
        self.cache.clear()
        logger.info("Embedding cache cleared")


# Global instance
embedding_service = EmbeddingService()
