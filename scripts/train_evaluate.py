import os
import re
import random
import logging
from typing import List
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from datasets import load_dataset
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Configuration (mirrored from backend.config for standalone use)
MODEL_PATH = "./data/doc2vec.model"
VECTOR_SIZE = 100
TRAIN_SPLIT = 0.8
SEED = 42

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_nltk():
    """Ensure NLTK resources are available"""
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        nltk.download('stopwords', quiet=True)
        return set(stopwords.words('english'))
    except Exception as e:
        logger.warning(f"Could not download NLTK resources: {e}")
        return set()

def preprocess(text: str, stop_words: set) -> List[str]:
    """Tokenize and clean text"""
    if not text:
        return []
    text = re.sub(r'[^\w\s]', '', str(text).lower())
    tokens = word_tokenize(text)
    return [t for t in tokens if t not in stop_words]

def train_and_evaluate():
    stop_words = setup_nltk()
    
    logger.info(f"Loading dataset 'jacob-hugging-face/job-descriptions'...")
    try:
        full_dataset = load_dataset("jacob-hugging-face/job-descriptions", split="train")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return

    # 1. Split Data
    num_docs = len(full_dataset)
    num_train = int(num_docs * TRAIN_SPLIT)
    indices = list(range(num_docs))
    random.Random(SEED).shuffle(indices)
    
    train_indices = set(indices[:num_train])
    test_indices = indices[num_train:]
    
    # 2. Prepare Training Data
    logger.info(f"Preparing {num_train} documents for training...")
    tagged_data = []
    for i, row in enumerate(full_dataset):
        if i in train_indices:
            text = f"{row.get('position_title', '')} {row.get('job_description', '')}"
            tokens = preprocess(text, stop_words)
            if tokens:
                tagged_data.append(TaggedDocument(words=tokens, tags=[str(i)]))
    
    # 3. Train Model
    logger.info("Starting Doc2Vec training (this may take a minute)...")
    model = Doc2Vec(
        vector_size=VECTOR_SIZE,
        min_count=2,
        epochs=40,
        seed=SEED
    )
    model.build_vocab(tagged_data)
    model.train(tagged_data, total_examples=model.corpus_count, epochs=model.epochs)
    
    # Save Model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save(MODEL_PATH)
    logger.info(f"✅ Model saved to {MODEL_PATH}")
    
    # 4. Evaluate on Test Split
    logger.info(f"Evaluating on {len(test_indices)} unseen test documents...")
    test_samples = random.Random(SEED).sample(test_indices, min(50, len(test_indices)))
    
    success_count = 0
    for idx in test_samples:
        row = full_dataset[idx]
        text = f"{row.get('position_title', '')} {row.get('job_description', '')}"
        
        # Stability check
        tokens = preprocess(text, stop_words)
        v1 = model.infer_vector(tokens)
        v2 = model.infer_vector(tokens)
        
        sim = cosine_similarity([v1], [v2])[0][0]
        if sim > 0.8:
            success_count += 1
            
    logger.info(f"📊 Stability Score on Unseen Data: {success_count}/{len(test_samples)} ({success_count/len(test_samples)*100:.1f}%)")

    # Semantic Test
    query = "Backend developer familiar with cloud and APIs"
    query_tokens = preprocess(query, stop_words)
    query_vec = model.infer_vector(query_tokens)
    
    results = []
    for idx in test_samples:
        row = full_dataset[idx]
        text = f"{row.get('position_title', '')} {row.get('job_description', '')}"
        tokens = preprocess(text, stop_words)
        doc_vec = model.infer_vector(tokens)
        sim = cosine_similarity([query_vec], [doc_vec])[0][0]
        results.append((row.get('position_title', 'Unknown'), sim))
    
    results.sort(key=lambda x: x[1], reverse=True)
    logger.info(f"\n🏆 Top Matches in Test Set for: '{query}'")
    for i, (title, score) in enumerate(results[:5]):
        logger.info(f"  {i+1}. [{score:.4f}] {title}")

if __name__ == "__main__":
    train_and_evaluate()
