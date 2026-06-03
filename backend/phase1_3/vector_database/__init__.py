"""
Phase 1.3.5 - Vector Database Integration
Package initialization for ChromaDB integration components.
"""

from .chroma_integration import chroma_integration, ChromaDBIntegration, ChromaConfig
from .main_integration import vector_db_integration, VectorDatabaseIntegration

__version__ = "1.0.0"
__all__ = [
    "chroma_integration",
    "ChromaDBIntegration",
    "ChromaConfig",
    "vector_db_integration",
    "VectorDatabaseIntegration"
]
