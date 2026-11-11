import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any

def semantic_search(query_embedding: List[float], document_embeddings: List[List[float]], documents: List[Any], top_k: int = 3) -> List[Any]:
    if not document_embeddings:
        return []
    
    query_vec = np.array(query_embedding).reshape(1, -1)
    doc_vecs = np.array(document_embeddings)
    
    similarities = cosine_similarity(query_vec, doc_vecs)[0]
    
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        if similarities[idx] > 0.1: # Minimum threshold
            results.append({
                "document": documents[idx],
                "score": float(similarities[idx])
            })
            
    return results
