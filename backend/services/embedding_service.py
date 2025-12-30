"""Embedding service using Gensim Doc2Vec"""
import logging
import os
import re
import random
from typing import List, Dict, Optional
import numpy as np
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from datasets import load_dataset
from backend.config import settings

logger = logging.getLogger(__name__)

# Ensure NLTK resources are available
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    logger.warning(f"Could not download NLTK resources: {e}")


class EmbeddingService:
    """Generate embeddings using a pre-trained Doc2Vec model"""
    
    def __init__(self):
        self.model_path = settings.doc2vec_model_path
        self.vector_size = settings.doc2vec_vector_size
        
        # Ensure NLTK resources are available for preprocessing
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))
        except Exception as e:
            logger.warning(f"Could not download NLTK resources: {e}")
            self.stop_words = set()

        self.model = self._load_model()
    
    def _preprocess(self, text: str) -> List[str]:
        """Tokenize and clean text"""
        if not text:
            return []
        text = re.sub(r'[^\w\s]', '', str(text).lower())
        tokens = word_tokenize(text)
        return [t for t in tokens if t not in self.stop_words]

    def _load_model(self) -> Optional[Doc2Vec]:
        """Load the pre-trained Doc2Vec model"""
        if os.path.exists(self.model_path):
            try:
                logger.info(f"Loading Doc2Vec model from {self.model_path}")
                return Doc2Vec.load(self.model_path)
            except Exception as e:
                logger.error(f"Error loading model from {self.model_path}: {e}")
                return None
        else:
            logger.error(f"Doc2Vec model NOT FOUND at {self.model_path}. "
                         f"Please run 'python scripts/train_evaluate.py' first.")
            return None

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text using pre-trained model"""
        if self.model is None:
            logger.error("Embedding requested but model is not loaded.")
            return []
            
        try:
            tokens = self._preprocess(text)
            vector = self.model.infer_vector(tokens)
            return vector.tolist()
        except Exception as e:
            logger.error(f"Error generating Doc2Vec embedding: {e}")
            return []
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return [await self.generate_embedding(text) for text in texts]
    
    async def embed_user_profile(self, profile_data: dict) -> List[float]:
        """Create embedding for user profile by combining key fields"""
        parts = []
        if profile_data.get('desired_job_titles'):
            parts.append(f"Desired roles: {', '.join(profile_data['desired_job_titles'])}")
        if profile_data.get('skills'):
            parts.append(f"Skills: {', '.join(profile_data['skills'])}")
        if profile_data.get('summary'):
            parts.append(f"Summary: {profile_data['summary']}")
        
        if profile_data.get('experience'):
            exp_texts = []
            for exp in profile_data['experience']:
                exp_text = f"{exp.get('title', '')} {exp.get('description', '')}"
                exp_texts.append(exp_text)
            parts.append(f"Experience: {' '.join(exp_texts)}")
        
        profile_text = " ".join(parts)
        return await self.generate_embedding(profile_text)
    
    async def embed_job_listing(self, job: dict) -> List[float]:
        """Create embedding for job listing"""
        parts = [
            job.get('title', ''),
            job.get('company', ''),
            job.get('description', ''),
        ]
        if job.get('skills'):
            parts.extend(job['skills'])
        
        job_text = " ".join(parts)
        return await self.generate_embedding(job_text)


# Global instance
embedding_service = EmbeddingService()
