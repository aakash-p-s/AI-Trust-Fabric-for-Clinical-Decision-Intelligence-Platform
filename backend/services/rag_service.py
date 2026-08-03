"""
backend/services/rag_service.py
Vector storage: FAISS (IndexFlatIP, brute-force exact search over
L2-normalized embeddings, which is mathematically equivalent to cosine
similarity). Chosen over a hosted vector DB (Pinecone/Weaviate/pgvector)
because the knowledge base is small (a handful of curated entries) --
FAISS runs entirely in-process, with no external service, no network
call, and no persistence layer needed. The index is rebuilt from
data/knowledge_base.json once at FastAPI startup and held in memory for
the life of the process.

If the knowledge base grows large enough that brute-force search becomes
a bottleneck, IndexFlatIP can be swapped for an approximate index (e.g.
IndexIVFFlat or IndexHNSWFlat) without changing retrieve()'s signature or
any calling code -- this is the specific benefit of using FAISS's index
abstraction here instead of a hand-rolled NumPy similarity loop.

Embedding model: sentence-transformers/all-MiniLM-L6-v2, local, no
external embedding API call.

Used exclusively by backend/agents/explainability_agent.py.
"""
import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

LOW_GROUNDING_THRESHOLD = 0.40
DEFAULT_KB_PATH = Path(__file__).resolve().parents[2] / "data" / "knowledge_base.json"

_embedder: SentenceTransformer | None = None
_knowledge_base: list[dict] = []
_index: faiss.IndexFlatIP | None = None


def load_knowledge_base(path: Path | str = DEFAULT_KB_PATH) -> None:
    global _embedder, _knowledge_base, _index

    with open(path) as f:
        _knowledge_base = json.load(f)

    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")

    embeddings = _embedder.encode([entry["text"] for entry in _knowledge_base]).astype("float32")
    faiss.normalize_L2(embeddings)  # so inner product == cosine similarity

    dim = embeddings.shape[1]
    _index = faiss.IndexFlatIP(dim)
    _index.add(embeddings)


def is_loaded() -> bool:
    return _index is not None and _index.ntotal > 0


def retrieve(prediction_label: str, symptoms: list[str], top_k: int = 2) -> list[dict]:
    """Returns up to top_k KB entries ranked by cosine similarity to the query,
    each annotated with a similarity_score float."""
    if not is_loaded():
        load_knowledge_base()

    query = f"{prediction_label}: {', '.join(symptoms)}"
    query_vec = _embedder.encode([query]).astype("float32")
    faiss.normalize_L2(query_vec)

    k = min(top_k, _index.ntotal)
    scores, indices = _index.search(query_vec, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:  # FAISS pads with -1 if fewer than k results exist
            continue
        entry = _knowledge_base[idx]
        results.append(
            {
                "id": entry["id"],
                "source": entry["source"],
                "text": entry["text"],
                "similarity_score": float(score),
            }
        )
    return results

