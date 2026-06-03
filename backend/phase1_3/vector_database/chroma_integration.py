"""
Phase 1.3.5 - Vector Database Integration
Uses pure Python vector store instead of ChromaDB.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import sys
from pathlib import Path

# Add backend root to path
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database.vector_store import VectorStore, _text_to_vector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ChromaConfig:
    """Configuration for vector store integration (keeps legacy name for compatibility)."""
    persist_directory: str = "./vector_store"
    collection_name: str = "mutual_funds"
    embedding_function: str = "cosine"
    embedding_dim: int = 384
    batch_size: int = 100
    max_results: int = 10
    similarity_threshold: float = 0.7


class ChromaDBIntegration:
    """
    Vector database integration using pure Python vector store.
    Replaces ChromaDB with a lightweight, crash-free implementation.
    """

    def __init__(self, config: ChromaConfig = None):
        self.config = config or ChromaConfig()
        self._store: Optional[VectorStore] = None

        self.integration_stats = {
            'total_documents': 0,
            'total_embeddings': 0,
            'successful_insertions': 0,
            'failed_insertions': 0,
            'query_count': 0,
            'average_query_time': 0.0,
            'collection_stats': {}
        }

        logger.info("Vector DB integration initialized")
        logger.info(f"Config: collection={self.config.collection_name}, dim={self.config.embedding_dim}")

    def initialize_chromadb(self) -> bool:
        """Initialize the vector store (legacy method name for orchestrator compatibility)."""
        logger.info("Initializing vector store...")
        try:
            self._store = VectorStore(persist_directory=self.config.persist_directory)
            logger.info("Vector store initialized successfully")
            logger.info(f"Collection: {self.config.collection_name}, dim={self.config.embedding_dim}")
            return True
        except Exception as e:
            logger.error(f"Vector store initialization failed: {e}")
            return False

    def _validate_collection_setup(self) -> Dict[str, Any]:
        """Validate vector store setup."""
        result = {'valid': False, 'error': None, 'collection_info': {}}
        try:
            if not self._store:
                result['error'] = "Vector store not initialized"
                return result

            count = self._store.collection.count()
            result['collection_info'] = {
                'name': self.config.collection_name,
                'count': count,
            }
            result['valid'] = True
        except Exception as e:
            result['error'] = f"Validation error: {e}"
        return result

    def add_embeddings(self, embeddings_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add embeddings to the vector store."""
        logger.info(f"Adding {len(embeddings_data)} embeddings to vector store")

        insertion_result = {
            'insertion_metadata': {
                'started_at': datetime.now().isoformat(),
                'total_embeddings': len(embeddings_data),
                'batch_size': self.config.batch_size,
                'collection_name': self.config.collection_name
            },
            'insertion_results': [],
            'insertion_stats': {},
            'success': False,
            'errors': []
        }

        try:
            if not self._store:
                insertion_result['errors'].append("Vector store not initialized")
                return insertion_result

            documents = []
            metadatas = []
            ids = []
            embeddings = []

            for emb_data in embeddings_data:
                embedding = emb_data.get('embedding', [])
                metadata = emb_data.get('metadata', {})

                if not embedding or not metadata:
                    logger.warning(f"Skipping invalid embedding data: {emb_data.get('id', 'unknown')}")
                    continue

                document_content = self._prepare_document_content(emb_data, metadata)
                enhanced_metadata = self._enhance_metadata(metadata, emb_data)

                documents.append(document_content)
                metadatas.append(enhanced_metadata)
                ids.append(emb_data.get('id', f"doc_{len(documents)+1:06d}"))
                embeddings.append(embedding)

            if not documents:
                logger.warning("No valid embeddings to insert")
                insertion_result['success'] = True
                return insertion_result

            # Insert all at once (our vector store handles this efficiently)
            self._store.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings,
            )

            total_inserted = len(documents)
            self.integration_stats['successful_insertions'] += total_inserted
            self.integration_stats['total_embeddings'] += total_inserted

            insertion_result['insertion_stats'] = {
                'total_embeddings': len(embeddings_data),
                'successful_insertions': total_inserted,
                'failed_insertions': len(embeddings_data) - total_inserted,
                'batches_processed': 1,
                'batch_errors': []
            }
            insertion_result['success'] = True

            logger.info(f"Successfully added {total_inserted} embeddings")

        except Exception as e:
            logger.error(f"Critical error in embedding insertion: {e}")
            insertion_result['success'] = False
            insertion_result['errors'].append({'error': str(e), 'stage': 'insertion'})

        return insertion_result

    def _prepare_document_content(self, emb_data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Prepare document content for storage."""
        parts = []
        fund_name = metadata.get('fund_name', '')
        chunk_type = metadata.get('chunk_type', '')
        priority = metadata.get('priority', 'medium')

        if fund_name:
            parts.append(f"Fund: {fund_name}")
        if chunk_type:
            parts.append(f"Type: {chunk_type}")
        if priority:
            parts.append(f"Priority: {priority}")

        original_content = emb_data.get('content', '')
        if original_content:
            parts.append(f"Content: {original_content}")

        return " | ".join(parts)

    def _enhance_metadata(self, metadata: Dict[str, Any], emb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata for storage."""
        enhanced = metadata.copy()
        fund_metadata = metadata.get('fund_metadata', {})
        if fund_metadata:
            enhanced.update({
                'fund_name': fund_metadata.get('fund_name', ''),
                'fund_type': fund_metadata.get('fund_type', ''),
                'fund_category': fund_metadata.get('category', ''),
                'risk_level': fund_metadata.get('risk_level', ''),
                'chunk_type': metadata.get('chunk_type', ''),
                'priority': metadata.get('priority', 'medium'),
                'token_count': metadata.get('token_count', 0),
                'embedding_model': emb_data.get('embedding_metadata', {}).get('model_used', 'BGE-small-en-v1.5'),
                'embedding_dim': emb_data.get('embedding_metadata', {}).get('embedding_dim', 384),
                'financial_data': True,
            })
        return enhanced

    def query_embeddings(self, query_text: str, n_results: int = None) -> Dict[str, Any]:
        """Query the vector store."""
        logger.info(f"Querying vector store: '{query_text}' (n_results={n_results})")

        query_result = {
            'query_metadata': {
                'query_text': query_text,
                'query_time': datetime.now().isoformat(),
                'max_results': n_results or self.config.max_results,
            },
            'query_results': [],
            'query_stats': {},
            'success': False,
            'errors': []
        }

        try:
            if not self._store:
                query_result['errors'].append("Vector store not initialized")
                return query_result

            n_results = n_results or self.config.max_results
            results = self._store.collection.query(
                query_texts=[query_text],
                n_results=n_results,
            )

            processed = []
            for i, (doc, meta, dist) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                processed.append({
                    'id': results.get('ids', [[]])[0][i] if 'ids' in results else f"r_{i}",
                    'document': doc,
                    'metadata': meta,
                    'distance': dist,
                    'similarity_score': max(0.0, 1.0 - dist),
                    'rank': i + 1,
                    'financial_context': {
                        'fund_name': meta.get('fund_name', ''),
                        'chunk_type': meta.get('chunk_type', ''),
                    }
                })

            query_result['query_results'] = processed
            query_result['success'] = True
            self.integration_stats['query_count'] += 1

            logger.info(f"Query returned {len(processed)} results")

        except Exception as e:
            logger.error(f"Query failed: {e}")
            query_result['errors'].append(str(e))

        return query_result

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            if not self._store:
                return {'error': 'Vector store not initialized'}
            count = self._store.collection.count()
            return {
                'total_documents': count,
                'collection_name': self.config.collection_name,
                'embedding_dim': self.config.embedding_dim,
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}

    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        stats = self.integration_stats.copy()
        if stats['total_embeddings'] > 0:
            stats['success_rate'] = (stats['successful_insertions'] / stats['total_embeddings']) * 100
        else:
            stats['success_rate'] = 0.0
        return stats

    def reset_stats(self):
        """Reset integration statistics."""
        self.integration_stats = {
            'total_documents': 0,
            'total_embeddings': 0,
            'successful_insertions': 0,
            'failed_insertions': 0,
            'query_count': 0,
            'average_query_time': 0.0,
            'collection_stats': {}
        }
        logger.info("Integration statistics reset")


# Global instance
chroma_integration = ChromaDBIntegration()
