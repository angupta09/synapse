"""Local sentence embeddings for the pgvector similarity index.

Uses all-MiniLM-L6-v2 (384-dim) so the embedding pipeline runs fully offline
with no external API key.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    if not text or not text.strip():
        return [0.0] * 384
    vec = _model().encode(text, normalize_embeddings=True)
    return vec.tolist()
