import sys
import os
import random
import numpy as np
from datasets import load_dataset
from sklearn.metrics.pairwise import cosine_similarity

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.services.embedding_service import embedding_service

async def run_evaluation():
    print("🚀 Starting Doc2Vec Evaluation (Test Split Only)...\n")
    
    # Load the full HF dataset
    print("📥 Loading full dataset...")
    try:
        full_dataset = load_dataset("jacob-hugging-face/job-descriptions", split="train")
        
        # Identify the 20% test split (using same seed 42 as in training)
        num_docs = len(full_dataset)
        num_train = int(num_docs * 0.8)
        indices = list(range(num_docs))
        import random
        random.Random(42).shuffle(indices)
        test_indices = indices[num_train:]
        
        # Take a sample of the test set for evaluation
        test_sample_indices = test_indices[:50]
        test_dataset = [full_dataset[i] for i in test_sample_indices]
        print(f"✅ Success: Evaluating on {len(test_dataset)} unseen test documents.")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return
    
    # 1. Test Self-Consistency on Unseen Data
    print("\n📊 Testing Self-Consistency on Unseen Data (Stability Check)...")
    success_count = 0
    
    for row in test_dataset[:20]:
        text = f"{row.get('position_title', '')} {row.get('job_description', '')}"
        
        v1 = await embedding_service.generate_embedding(text)
        v2 = await embedding_service.generate_embedding(text)
        
        if v1 and v2:
            sim = cosine_similarity([v1], [v2])[0][0]
            if sim > 0.8:
                success_count += 1
            
    print(f"✅ Test Consistency Score: {success_count}/20 ({success_count/20*100}%)")

    # 2. Semantic Search Test against Train Split
    print("\n🔍 Testing Generalization (Query vs Test Segment)...")
    query = "Backend developer familiar with cloud and APIs"
    print(f"Query: '{query}'")
    
    query_vec = await embedding_service.generate_embedding(query)
    results = []
    
    for row in test_dataset:
        doc_text = f"{row.get('position_title', '')} {row.get('job_description', '')}"
        doc_vec = await embedding_service.generate_embedding(doc_text)
        if doc_vec:
            sim = cosine_similarity([query_vec], [doc_vec])[0][0]
            results.append((row.get('position_title', 'Unknown'), sim))
    
    results.sort(key=lambda x: x[1], reverse=True)
    print("\n🏆 Top 5 Semantic Matches from Test Set:")
    for i, (title, score) in enumerate(results[:5]):
        print(f"  {i+1}. [{score:.4f}] {title}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_evaluation())
