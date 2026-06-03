"""
Phase 1.3.3 - Text Chunking Strategy
Package initialization for financial data-specific chunking components.
"""

from .financial_chunker import financial_chunker, FinancialDataChunker, ChunkConfig
from .main_chunker import text_chunking_impl, TextChunkingImplementation

__version__ = "1.0.0"
__all__ = [
    "financial_chunker",
    "FinancialDataChunker",
    "ChunkConfig",
    "text_chunking_impl",
    "TextChunkingImplementation"
]
