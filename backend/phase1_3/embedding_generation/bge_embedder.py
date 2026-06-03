"""
Phase 1.3.4 - Embedding Generation
BGE-small-en Embedding Model for Financial Data
"""

import logging
import torch
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BGEConfig:
    """
    Configuration for BGE embedding model.
    """
    model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    max_seq_length: int = 512
    batch_size: int = 32
    device: str = "auto"  # auto, cpu, cuda
    normalize_embeddings: bool = True
    cache_folder: str = "./cache/bge_embeddings"
    
    # Financial-specific settings
    financial_fine_tuned: bool = False
    domain_adaptation: bool = True
    similarity_metric: str = "cosine"

class BGEEmbedder:
    """
    BGE-small-en embedding model optimized for financial data.
    Implements bidirectional gradient encoding for mutual fund information.
    """
    
    def __init__(self, config: BGEConfig = None):
        """
        Initialize BGE embedder with configuration.
        """
        self.config = config or BGEConfig()
        self.model = None
        self.device = None
        self.embedding_stats = {
            'total_chunks': 0,
            'total_embeddings': 0,
            'successful_embeddings': 0,
            'failed_embeddings': 0,
            'average_embedding_time': 0.0,
            'memory_usage': 0.0,
            'batch_stats': {}
        }
        
        logger.info("BGE embedder initialized")
        logger.info(f"Model: {self.config.model_name}")
        logger.info(f"Dimensions: {self.config.embedding_dim}")
        logger.info(f"Device: {self.config.device}")
    
    def initialize_model(self) -> bool:
        """
        Initialize BGE model and setup device.
        """
        logger.info("Initializing BGE embedding model...")
        
        try:
            # Step 1: Setup device
            if self.config.device == "auto":
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                self.device = self.config.device
            
            logger.info(f"Using device: {self.device}")
            
            # Step 2: Load BGE model
            logger.info(f"Loading BGE model: {self.config.model_name}")
            
            self.model = SentenceTransformer(
                self.config.model_name,
                device=self.device,
                cache_folder=self.config.cache_folder
            )
            
            # Step 3: Validate model dimensions
            model_dim = self.model.get_sentence_embedding_dimension()
            if model_dim != self.config.embedding_dim:
                logger.warning(f"Model dimension mismatch: expected {self.config.embedding_dim}, got {model_dim}")
                # Update config to match actual model
                self.config.embedding_dim = model_dim
            
            # Step 4: Test model with sample input
            test_text = "HDFC Large Cap Fund Direct Growth"
            test_embedding = self.model.encode([test_text])
            
            if test_embedding is not None and len(test_embedding) > 0:
                logger.info(f"✅ BGE model initialized successfully")
                logger.info(f"Test embedding shape: {test_embedding.shape}")
                logger.info(f"Embedding dimension: {len(test_embedding[0])}")
                return True
            else:
                logger.error("❌ BGE model test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ BGE model initialization failed: {e}")
            return False
    
    def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate embeddings for financial data chunks using BGE.
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        embedding_result = {
            'embedding_metadata': {
                'model_name': self.config.model_name,
                'model_version': '1.5',
                'embedding_dim': self.config.embedding_dim,
                'device_used': self.device,
                'batch_size': self.config.batch_size,
                'started_at': datetime.now().isoformat()
            },
            'embeddings': [],
            'embedding_stats': {},
            'quality_metrics': {},
            'success': False,
            'errors': []
        }
        
        try:
            # Step 1: Prepare chunk texts
            chunk_texts = []
            chunk_metadata = []
            
            for chunk in chunks:
                # Prepare text with financial context
                enhanced_text = self._prepare_chunk_text(chunk)
                chunk_texts.append(enhanced_text)
                
                # Prepare metadata
                metadata = {
                    'chunk_id': chunk.get('chunk_id', ''),
                    'chunk_type': chunk.get('chunk_type', 'unknown'),
                    'fund_name': chunk.get('fund_metadata', {}).get('fund_name', ''),
                    'token_count': chunk.get('token_count', 0),
                    'priority': chunk.get('priority', 'medium')
                }
                chunk_metadata.append(metadata)
            
            # Step 2: Generate embeddings in batches
            all_embeddings = []
            batch_times = []
            
            for i in range(0, len(chunk_texts), self.config.batch_size):
                batch_start = i
                batch_end = min(i + self.config.batch_size, len(chunk_texts))
                batch_texts = chunk_texts[batch_start:batch_end]
                
                logger.info(f"Processing batch {batch_start//self.config.batch_size + 1}: chunks {batch_start+1}-{batch_end}")
                
                # Generate embeddings for batch
                batch_start_time = datetime.now()
                batch_embeddings = self.model.encode(
                    batch_texts,
                    batch_size=self.config.batch_size,
                    normalize_embeddings=self.config.normalize_embeddings,
                    show_progress_bar=True
                )
                batch_end_time = datetime.now()
                
                batch_time = (batch_end_time - batch_start_time).total_seconds()
                batch_times.append(batch_time)
                
                if batch_embeddings is not None:
                    # Convert to list if needed
                    if isinstance(batch_embeddings, torch.Tensor):
                        batch_embeddings = batch_embeddings.cpu().numpy()
                    
                    all_embeddings.extend(batch_embeddings)
                    
                    # Update stats
                    self.embedding_stats['total_embeddings'] += len(batch_embeddings)
                    self.embedding_stats['successful_embeddings'] += len(batch_embeddings)
                    
                    logger.info(f"✅ Batch completed: {len(batch_embeddings)} embeddings in {batch_time:.2f}s")
                else:
                    logger.error(f"❌ Batch {batch_start//self.config.batch_size + 1} failed")
                    embedding_result['errors'].append(f'Batch {batch_start//self.config.batch_size + 1} failed to generate embeddings')
            
            # Step 3: Create embedding objects with metadata
            embedding_objects = []
            for i, (embedding, metadata) in enumerate(zip(all_embeddings, chunk_metadata)):
                embedding_obj = {
                    'id': f"emb_{i+1:06d}",
                    'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                    'metadata': metadata,
                    'embedding_metadata': {
                        'model_used': self.config.model_name,
                        'embedding_dim': self.config.embedding_dim,
                        'normalized': self.config.normalize_embeddings,
                        'created_at': datetime.now().isoformat()
                    }
                }
                embedding_objects.append(embedding_obj)
            
            embedding_result['embeddings'] = embedding_objects
            
            # Step 4: Calculate statistics
            avg_batch_time = np.mean(batch_times) if batch_times else 0
            self.embedding_stats['average_embedding_time'] = avg_batch_time
            self.embedding_stats['total_chunks'] = len(chunks)
            
            # Step 5: Calculate quality metrics
            embedding_result['quality_metrics'] = self._calculate_embedding_quality_metrics(
                all_embeddings, chunk_texts
            )
            
            # Step 6: Memory usage estimation
            embedding_result['embedding_stats'] = {
                'total_chunks': len(chunks),
                'total_embeddings': len(all_embeddings),
                'successful_embeddings': self.embedding_stats['successful_embeddings'],
                'failed_embeddings': self.embedding_stats['failed_embeddings'],
                'average_embedding_time': avg_batch_time,
                'batches_processed': len(batch_times),
                'memory_usage_mb': self._estimate_memory_usage(all_embeddings)
            }
            
            embedding_result['success'] = len(embedding_result['errors']) == 0
            
            logger.info(f"Embedding generation completed. Success: {embedding_result['success']}")
            logger.info(f"Total embeddings: {len(all_embeddings)}")
            logger.info(f"Average batch time: {avg_batch_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Critical error in embedding generation: {e}")
            embedding_result['success'] = False
            embedding_result['errors'].append(f'Critical error: {str(e)}')
        
        return embedding_result
    
    def _prepare_chunk_text(self, chunk: Dict[str, Any]) -> str:
        """
        Prepare chunk text with financial context enhancement.
        """
        base_text = chunk.get('content', '')
        
        if not base_text:
            return ""
        
        # Add financial context prefix
        fund_metadata = chunk.get('fund_metadata', {})
        fund_name = fund_metadata.get('fund_name', '')
        chunk_type = chunk.get('chunk_type', '')
        
        # Create enhanced text with context
        if fund_name and chunk_type:
            context_prefix = f"Fund: {fund_name} | Type: {chunk_type} | "
            enhanced_text = context_prefix + base_text
        else:
            enhanced_text = base_text
        
        # Apply financial text preprocessing
        enhanced_text = self._apply_financial_preprocessing(enhanced_text)
        
        return enhanced_text
    
    def _apply_financial_preprocessing(self, text: str) -> str:
        """
        Apply financial-specific text preprocessing.
        """
        if not text:
            return ""
        
        # Financial term normalization
        processed_text = text.lower()
        
        # Standardize financial abbreviations
        financial_terms = {
            'nav': 'net asset value',
            'aum': 'assets under management',
            'sip': 'systematic investment plan',
            'elss': 'equity linked savings scheme',
            'nfo': 'new fund offer'
        }
        
        for abbrev, full_term in financial_terms.items():
            processed_text = processed_text.replace(abbrev, full_term)
        
        # Preserve original case for proper nouns
        processed_text = self._preserve_financial_entities(processed_text)
        
        return processed_text
    
    def _preserve_financial_entities(self, text: str) -> str:
        """
        Preserve financial entities (fund names, companies, etc.).
        """
        # Simple heuristic: capitalize words that look like fund names or companies
        words = text.split()
        preserved_words = []
        
        financial_indicators = ['fund', 'hdfc', 'icici', 'sbi', 'axis', 'reliance', 'tata']
        
        for word in words:
            # Check if word contains financial indicators
            if any(indicator in word.lower() for indicator in financial_indicators):
                preserved_words.append(word.title())
            else:
                preserved_words.append(word)
        
        return ' '.join(preserved_words)
    
    def _calculate_embedding_quality_metrics(self, embeddings: List[Any], texts: List[str]) -> Dict[str, Any]:
        """
        Calculate quality metrics for generated embeddings.
        """
        if not embeddings or not texts:
            return {'overall_score': 0.0, 'error': 'No embeddings or texts'}
        
        quality_metrics = {
            'overall_score': 0.0,
            'dimension_consistency': 0.0,
            'embedding_quality': 0.0,
            'text_coverage': 0.0,
            'financial_relevance': 0.0
        }
        
        try:
            # Check dimension consistency
            expected_dim = self.config.embedding_dim
            dimension_consistency = 0
            
            for embedding in embeddings:
                if hasattr(embedding, 'shape'):
                    actual_dim = embedding.shape[-1] if len(embedding.shape) > 1 else len(embedding)
                else:
                    actual_dim = len(embedding)
                
                if actual_dim == expected_dim:
                    dimension_consistency += 1
            
            quality_metrics['dimension_consistency'] = (dimension_consistency / len(embeddings)) * 100
            
            # Calculate embedding quality (norm statistics)
            if hasattr(embeddings[0], 'shape'):
                embedding_array = np.array(embeddings)
                norms = np.linalg.norm(embedding_array, axis=1)
                
                # Good embeddings should have reasonable norms
                norm_mean = np.mean(norms)
                norm_std = np.std(norms)
                
                # Score based on norm distribution
                if 0.5 <= norm_mean <= 2.0 and norm_std <= 0.5:
                    quality_metrics['embedding_quality'] = 85.0
                elif 0.3 <= norm_mean <= 3.0 and norm_std <= 1.0:
                    quality_metrics['embedding_quality'] = 70.0
                else:
                    quality_metrics['embedding_quality'] = 50.0
            
            # Text coverage (embedding should capture text meaning)
            avg_text_length = np.mean([len(text.split()) for text in texts])
            if avg_text_length > 50:  # Reasonable chunk size
                quality_metrics['text_coverage'] = 80.0
            else:
                quality_metrics['text_coverage'] = 60.0
            
            # Financial relevance (check for financial terms)
            financial_terms = ['fund', 'investment', 'return', 'risk', 'nav', 'sip', 'expense', 'allocation']
            financial_relevance_scores = []
            
            for text in texts:
                text_lower = text.lower()
                financial_count = sum(1 for term in financial_terms if term in text_lower)
                relevance_score = (financial_count / len(text.split())) * 100
                financial_relevance_scores.append(relevance_score)
            
            quality_metrics['financial_relevance'] = np.mean(financial_relevance_scores) if financial_relevance_scores else 0.0
            
            # Calculate overall score
            quality_metrics['overall_score'] = (
                quality_metrics['dimension_consistency'] * 0.3 +
                quality_metrics['embedding_quality'] * 0.3 +
                quality_metrics['text_coverage'] * 0.2 +
                quality_metrics['financial_relevance'] * 0.2
            )
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            quality_metrics['overall_score'] = 0.0
            quality_metrics['error'] = str(e)
        
        return quality_metrics
    
    def _estimate_memory_usage(self, embeddings: List[Any]) -> float:
        """
        Estimate memory usage for embeddings.
        """
        if not embeddings:
            return 0.0
        
        try:
            # Calculate memory usage in MB
            total_elements = 0
            for embedding in embeddings:
                if hasattr(embedding, 'shape'):
                    total_elements += np.prod(embedding.shape)
                else:
                    total_elements += len(embedding)
            
            # Float32 = 4 bytes per element
            memory_bytes = total_elements * 4
            memory_mb = memory_bytes / (1024 * 1024)
            
            return round(memory_mb, 2)
            
        except Exception as e:
            logger.error(f"Error estimating memory usage: {e}")
            return 0.0
    
    def validate_embeddings(self, embedding_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate generated embeddings for quality and consistency.
        """
        validation_result = {
            'validation_timestamp': datetime.now().isoformat(),
            'overall_status': 'passed',
            'validation_score': 0.0,
            'dimension_checks': {},
            'quality_checks': {},
            'issues': []
        }
        
        try:
            embeddings = embedding_result.get('embeddings', [])
            
            if not embeddings:
                validation_result['overall_status'] = 'failed'
                validation_result['issues'].append('No embeddings generated')
                return validation_result
            
            # Check dimensions
            expected_dim = self.config.embedding_dim
            dimension_errors = 0
            correct_dimensions = 0
            
            for i, emb_obj in enumerate(embeddings):
                embedding = emb_obj.get('embedding', [])
                actual_dim = len(embedding)
                
                if actual_dim == expected_dim:
                    correct_dimensions += 1
                else:
                    dimension_errors += 1
                    validation_result['issues'].append(f'Embedding {i+1}: wrong dimension {actual_dim} (expected {expected_dim})')
            
            validation_result['dimension_checks'] = {
                'total_embeddings': len(embeddings),
                'correct_dimensions': correct_dimensions,
                'dimension_errors': dimension_errors,
                'consistency_score': (correct_dimensions / len(embeddings)) * 100
            }
            
            # Check quality metrics
            quality_metrics = embedding_result.get('quality_metrics', {})
            overall_quality = quality_metrics.get('overall_score', 0)
            
            validation_result['quality_checks'] = {
                'overall_quality_score': overall_quality,
                'dimension_consistency': quality_metrics.get('dimension_consistency', 0),
                'embedding_quality': quality_metrics.get('embedding_quality', 0),
                'financial_relevance': quality_metrics.get('financial_relevance', 0)
            }
            
            # Calculate validation score
            dimension_score = validation_result['dimension_checks']['consistency_score']
            quality_score = min(100.0, overall_quality)
            
            validation_result['validation_score'] = (dimension_score * 0.6) + (quality_score * 0.4)
            
            # Determine overall status
            if dimension_errors > 0:
                validation_result['overall_status'] = 'failed'
            elif validation_result['validation_score'] < 70.0:
                validation_result['overall_status'] = 'warning'
            
        except Exception as e:
            logger.error(f"Error validating embeddings: {e}")
            validation_result['overall_status'] = 'error'
            validation_result['error'] = str(e)
        
        return validation_result
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get embedding generation statistics.
        """
        stats = self.embedding_stats.copy()
        
        # Calculate additional metrics
        if stats['total_embeddings'] > 0:
            stats['success_rate'] = (stats['successful_embeddings'] / stats['total_embeddings']) * 100
            stats['average_time_per_embedding'] = (
                stats['average_embedding_time'] / self.config.batch_size
            )
        else:
            stats['success_rate'] = 0.0
            stats['average_time_per_embedding'] = 0.0
        
        stats['model_info'] = {
            'model_name': self.config.model_name,
            'embedding_dim': self.config.embedding_dim,
            'device': self.device,
            'batch_size': self.config.batch_size
        }
        
        stats['embedder_version'] = '1.0'
        
        return stats
    
    def reset_stats(self):
        """
        Reset embedding statistics.
        """
        self.embedding_stats = {
            'total_chunks': 0,
            'total_embeddings': 0,
            'successful_embeddings': 0,
            'failed_embeddings': 0,
            'average_embedding_time': 0.0,
            'memory_usage': 0.0,
            'batch_stats': {}
        }
        logger.info("Embedding statistics reset")

# Global BGE embedder instance
bge_embedder = BGEEmbedder()

if __name__ == "__main__":
    # Test BGE embedder
    print("🧠 Testing BGE-small-en Embedder")
    print("=" * 50)
    
    # Test chunks
    test_chunks = [
        {
            'chunk_id': 'primary_001',
            'chunk_type': 'primary',
            'content': 'HDFC Large Cap Fund Direct Growth is a large cap equity fund focusing on established companies with strong market positions',
            'token_count': 25,
            'priority': 'high',
            'fund_metadata': {
                'fund_name': 'HDFC Large Cap Fund Direct Growth',
                'fund_type': 'Direct Growth',
                'category': 'Large Cap'
            }
        },
        {
            'chunk_id': 'metric_001',
            'chunk_type': 'metric',
            'content': 'Expense Ratio: 1.25%, Exit Load: 0%, Minimum SIP: ₹500, Current NAV: ₹125.67',
            'token_count': 18,
            'priority': 'high',
            'fund_metadata': {
                'fund_name': 'HDFC Large Cap Fund Direct Growth',
                'fund_type': 'Direct Growth',
                'category': 'Large Cap'
            }
        },
        {
            'chunk_id': 'performance_001',
            'chunk_type': 'performance',
            'content': '1 Year Return: 12.5%, 3 Year Return: 15.2%, 5 Year Return: 14.8%',
            'token_count': 15,
            'priority': 'medium',
            'fund_metadata': {
                'fund_name': 'HDFC Large Cap Fund Direct Growth',
                'fund_type': 'Direct Growth',
                'category': 'Large Cap'
            }
        }
    ]
    
    try:
        # Initialize model
        if bge_embedder.initialize_model():
            print("✅ BGE model initialization successful")
            
            # Generate embeddings
            print("\n🧠 Generating embeddings...")
            result = bge_embedder.generate_embeddings(test_chunks)
            
            # Display results
            print(f"\nEmbedding Results:")
            print(f"Success: {result.get('success', False)}")
            print(f"Total Embeddings: {result.get('embedding_stats', {}).get('total_embeddings', 0)}")
            print(f"Successful: {result.get('embedding_stats', {}).get('successful_embeddings', 0)}")
            print(f"Average Batch Time: {result.get('embedding_stats', {}).get('average_embedding_time', 0):.2f}s")
            print(f"Memory Usage: {result.get('embedding_stats', {}).get('memory_usage_mb', 0):.2f} MB")
            
            # Show quality metrics
            quality_metrics = result.get('quality_metrics', {})
            print(f"\n📊 Quality Metrics:")
            print(f"Overall Score: {quality_metrics.get('overall_score', 0):.1f}")
            print(f"Dimension Consistency: {quality_metrics.get('dimension_consistency', 0):.1f}%")
            print(f"Embedding Quality: {quality_metrics.get('embedding_quality', 0):.1f}")
            print(f"Financial Relevance: {quality_metrics.get('financial_relevance', 0):.1f}%")
            
            # Show embeddings
            embeddings = result.get('embeddings', [])
            print(f"\n📄 Generated Embeddings:")
            for i, emb_obj in enumerate(embeddings[:3], 1):  # Show first 3
                emb_id = emb_obj.get('id', 'unknown')
                emb_dim = len(emb_obj.get('embedding', []))
                chunk_type = emb_obj.get('metadata', {}).get('chunk_type', 'unknown')
                print(f"  {i}. {emb_id} (Dim: {emb_dim}, Type: {chunk_type})")
            
            if len(embeddings) > 3:
                print(f"  ... and {len(embeddings) - 3} more embeddings")
            
            # Validate embeddings
            print(f"\n🔍 Validating embeddings...")
            validation = bge_embedder.validate_embeddings(result)
            
            print(f"Validation Status: {validation.get('overall_status', 'unknown')}")
            print(f"Validation Score: {validation.get('validation_score', 0):.1f}")
            print(f"Dimension Consistency: {validation.get('dimension_checks', {}).get('consistency_score', 0):.1f}%")
            
            if validation.get('issues'):
                print("Validation Issues:")
                for issue in validation['issues'][:2]:
                    print(f"  • {issue}")
            
            # Show stats
            stats = bge_embedder.get_embedding_stats()
            print(f"\n📈 Embedder Stats:")
            print(f"Success Rate: {stats.get('success_rate', 0):.1f}%")
            print(f"Total Chunks: {stats.get('total_chunks', 0)}")
            print(f"Total Embeddings: {stats.get('total_embeddings', 0)}")
            print(f"Device: {stats.get('model_info', {}).get('device', 'unknown')}")
        
        else:
            print("❌ BGE model initialization failed")
            
    except Exception as e:
        print(f"❌ Error testing BGE embedder: {e}")
    
    print("\n✅ BGE embedder testing completed")
    print("=" * 50)
