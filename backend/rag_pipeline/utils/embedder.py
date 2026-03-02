"""
utils/embedder.py
──────────────────
FAISS-based vector store for FSSAI additive knowledge base.

Behaviour:
  - On first call, builds a flat FAISS index from fssai_additives.json and
    persists it to vector_store/index.faiss + vector_store/id_map.json.
  - On subsequent calls, loads the cached index (fast).
  - Provides retrieve_context() to find the top-k most similar additive
    entries for a given ingredient or query string.

Design note:
  For 100-200 additive entries, FAISS is used for extensibility (future
  upload of full FSSAI regulation PDFs). For the current knowledge base,
  a linear scan would also be fast enough. The FAISS index is rebuilt
  when the knowledge base JSON is newer than the cached index file.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent.parent          # rag_pipeline/
_KB_PATH = _HERE / "knowledge_base" / "fssai_additives.json"
_VS_DIR = _HERE / "vector_store"
_INDEX_PATH = _VS_DIR / "index.faiss"
_ID_MAP_PATH = _VS_DIR / "id_map.json"

# ── Module-level cache ────────────────────────────────────────────────────────
_faiss_index = None
_id_map: Optional[List[Dict[str, Any]]] = None
_model = None

# ── Text representation for an additive entry ─────────────────────────────────

def _entry_to_text(entry: Dict[str, Any]) -> str:
    """Convert an additive JSON entry to a single sentence for embedding."""
    parts = [
        entry.get("code", ""),
        entry.get("name", ""),
        " ".join(entry.get("aliases", [])),
        entry.get("category", ""),
        entry.get("health_risks", ""),
    ]
    return " | ".join(p for p in parts if p).strip()


# ── Model loader (lazy) ────────────────────────────────────────────────────────

def _get_model():
    """Load SentenceTransformer model (cached in module scope)."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("RAG Embedder: loading sentence-transformers model…")
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("RAG Embedder: model loaded.")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "RAG retrieval will fall back to keyword matching."
            )
            _model = None
    return _model


# ── FAISS index builder ────────────────────────────────────────────────────────

def _build_index(entries: List[Dict[str, Any]]):
    """Build and persist a FAISS Flat L2 index from the additive entries."""
    try:
        import faiss
        import numpy as np
    except ImportError as e:
        logger.warning("FAISS not available: %s. Vector retrieval disabled.", e)
        return None, entries

    model = _get_model()
    if model is None:
        return None, entries

    texts = [_entry_to_text(e) for e in entries]
    logger.info("RAG Embedder: encoding %d additive entries…", len(texts))
    t0 = time.time()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    embeddings = embeddings.astype("float32")
    logger.info("RAG Embedder: encoded in %.2fs", time.time() - t0)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Persist
    _VS_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(_INDEX_PATH))
    with open(_ID_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    logger.info("RAG Embedder: FAISS index saved (%d vectors, dim=%d)", len(texts), dim)
    return index, entries


# ── Index loader ───────────────────────────────────────────────────────────────

def _load_or_build_index() -> Tuple[Any, List[Dict[str, Any]]]:
    """Return (faiss_index, id_map). Build from JSON if cache is stale."""
    global _faiss_index, _id_map

    if _faiss_index is not None and _id_map is not None:
        return _faiss_index, _id_map

    with open(_KB_PATH, encoding="utf-8") as f:
        entries: List[Dict[str, Any]] = json.load(f)

    # Check if cached index is up-to-date
    kb_mtime = os.path.getmtime(_KB_PATH)
    index_mtime = os.path.getmtime(_INDEX_PATH) if _INDEX_PATH.exists() else 0

    if _INDEX_PATH.exists() and _ID_MAP_PATH.exists() and index_mtime >= kb_mtime:
        try:
            import faiss
            logger.info("RAG Embedder: loading cached FAISS index…")
            _faiss_index = faiss.read_index(str(_INDEX_PATH))
            with open(_ID_MAP_PATH, encoding="utf-8") as f:
                _id_map = json.load(f)
            logger.info("RAG Embedder: cached index loaded (%d vectors).", _faiss_index.ntotal)
            return _faiss_index, _id_map
        except Exception as exc:
            logger.warning("Failed to load cached index: %s — rebuilding.", exc)

    # Build fresh
    _faiss_index, _id_map = _build_index(entries)
    if _faiss_index is None:
        # Fall back: id_map only (keyword retrieval still works)
        _id_map = entries
    return _faiss_index, _id_map


# ── Public retrieval API ───────────────────────────────────────────────────────

def retrieve_context(
    query: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Retrieve the top-k most semantically similar FSSAI additive entries
    for a given query string (ingredient name, code, etc.).

    Falls back to simple substring/keyword matching if FAISS/SentenceTransformers
    are not installed.

    Args:
        query: Ingredient name or additive code to search for.
        top_k: Number of results to return.

    Returns:
        List of up to top_k additive dicts from fssai_additives.json.
    """
    if not query or not query.strip():
        return []

    index, id_map = _load_or_build_index()
    model = _get_model()

    # ── Vector retrieval path ──────────────────────────────────────────────────
    if index is not None and model is not None:
        try:
            import numpy as np
            q_vec = model.encode([query.lower()], convert_to_numpy=True).astype("float32")
            distances, indices = index.search(q_vec, min(top_k, index.ntotal))
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(id_map):
                    entry = dict(id_map[idx])
                    entry["_similarity_score"] = round(float(1 / (1 + dist)), 4)
                    results.append(entry)
            return results
        except Exception as exc:
            logger.warning("FAISS retrieval failed: %s — falling back to keyword match.", exc)

    # ── Keyword fallback ───────────────────────────────────────────────────────
    query_lower = query.lower().strip()
    hits = []
    for entry in (id_map or []):
        searchable = _entry_to_text(entry).lower()
        if query_lower in searchable:
            hits.append(entry)
        if len(hits) >= top_k:
            break
    return hits
