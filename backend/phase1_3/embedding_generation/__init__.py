"""
Phase 1.3.4 - Embedding Generation
Package initialization for BGE embedding components.
"""

from .bge_embedder import bge_embedder, BGEEmbedder, BGEConfig
from .main_embedder import embedding_generation_impl, EmbeddingGenerationImplementation

__version__ = "1.0.0"
__all__ = [
    "bge_embedder",
    "BGEEmbedder",
    "BGEConfig",
    "embedding_generation_impl",
    "EmbeddingGenerationImplementation"
]
