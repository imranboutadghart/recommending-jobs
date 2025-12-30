import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.embedding_service import embedding_service

async def test_embeddings():
    print("Testing Doc2Vec Embeddings...")
    
    # Test single embedding
    text = "Software engineer with python and fastapi experience"
    vector = await embedding_service.generate_embedding(text)
    
    if vector:
        print(f"✅ Generated vector of size: {len(vector)}")
        print(f"Sample values: {vector[:5]}")
    else:
        print("❌ Failed to generate vector")
        return

    # Test profile embedding
    profile = {
        "desired_job_titles": ["Python Developer"],
        "skills": ["Python", "FastAPI", "Doc2Vec"],
        "summary": "Experienced backend developer",
        "experience": [
            {"title": "Senior Dev", "description": "Worked on AI systems"}
        ]
    }
    profile_vector = await embedding_service.embed_user_profile(profile)
    if profile_vector:
        print(f"✅ Generated profile vector of size: {len(profile_vector)}")
    else:
        print("❌ Failed to generate profile vector")

    # Test job embedding
    job = {
        "title": "Backend Engineer",
        "company": "AI Corp",
        "description": "Building next gen AI tools with Python",
        "skills": ["Python", "NLTK"]
    }
    job_vector = await embedding_service.embed_job_listing(job)
    if job_vector:
        print(f"✅ Generated job vector of size: {len(job_vector)}")
    else:
        print("❌ Failed to generate job vector")

if __name__ == "__main__":
    asyncio.run(test_embeddings())
