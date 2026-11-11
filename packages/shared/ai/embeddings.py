from sentence_transformers import SentenceTransformer
import os

# Load model once
model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model

class LocalEmbeddingProvider:
    def embed_text(self, text: str) -> list[float]:
        if not text.strip():
            return [0.0] * 384
        model = get_model()
        return model.encode(text).tolist()
