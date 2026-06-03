"""
Retrieval layer (Phase 2.1).

Implements metadata-aware vector retrieval over the Phase 1.3 ChromaDB corpus.
"""

from .retriever import RetrievalResult, Retriever

__all__ = ["Retriever", "RetrievalResult"]

