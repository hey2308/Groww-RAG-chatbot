"""
Phase 1.3.4 - Embedding Generation
Main implementation script for BGE-small-en embedding generation
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from bge_embedder import bge_embedder, BGEConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmbeddingGenerationImplementation:
    """
    Main implementation of Phase 1.3.4 Embedding Generation.
    Implements BGE-small-en for financial data embeddings.
    """
    
    def __init__(self, config: BGEConfig = None):
        """
        Initialize embedding generation implementation.
        """
        self.bge_embedder = bge_embedder
        self.config = config or BGEConfig()
        
        self.embedding_stats = {
            'started_at': None,
            'completed_at': None,
            'total_chunks': 0,
            'total_embeddings': 0,
            'successful_embeddings': 0,
            'failed_embeddings': 0,
            'embedding_results': {},
            'quality_summary': {},
            'errors': []
        }
        
        logger.info("Embedding generation implementation initialized")
        logger.info(f"Config: model={self.config.model_name}, dim={self.config.embedding_dim}")
    
    def initialize_embedding_system(self) -> bool:
        """
        Initialize all embedding components.
        """
        logger.info("Initializing BGE embedding system...")
        
        try:
            # Step 1: Validate configuration
            if not self._validate_config():
                logger.error("❌ Invalid embedding configuration")
                return False
            
            # Step 2: Initialize BGE model
            if not self.bge_embedder.initialize_model():
                logger.error("❌ BGE model initialization failed")
                return False
            
            # Step 3: Reset statistics
            self._reset_embedding_stats()
            
            logger.info("✅ BGE embedding system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    def generate_embeddings_for_chunks(self, chunked_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate embeddings for chunked data using BGE.
        """
        logger.info(f"Starting BGE embedding generation for {len(chunked_data_list)} documents")
        
        self.embedding_stats['started_at'] = datetime.now().isoformat()
        self.embedding_stats['total_chunks'] = sum(
            len(doc.get('chunks', [])) for doc in chunked_data_list
        )
        
        embedding_results = {
            'implementation_metadata': {
                'phase': '1.3.4',
                'version': '1.0',
                'started_at': self.embedding_stats['started_at'],
                'input_documents': len(chunked_data_list),
                'total_input_chunks': self.embedding_stats['total_chunks'],
                'embedding_model': 'BGE-small-en-v1.5'
            },
            'embedding_results': [],
            'generation_summary': {},
            'quality_summary': {},
            'success': False,
            'errors': []
        }
        
        try:
            # Process each chunked document
            for i, chunked_data in enumerate(chunked_data_list):
                logger.info(f"Processing document {i+1}/{len(chunked_data_list)}")
                
                try:
                    # Step 1: Extract chunks from document
                    chunks = chunked_data.get('chunks', [])
                    
                    if not chunks:
                        logger.warning(f"⚠️ No chunks found in document {i+1}")
                        self.embedding_stats['failed_embeddings'] += 1
                        continue
                    
                    # Step 2: Generate embeddings for chunks
                    embedding_result = self.bge_embedder.generate_embeddings(chunks)
                    
                    if not embedding_result.get('embeddings'):
                        logger.error(f"❌ Embedding generation failed: {embedding_result.get('error', 'Unknown')}")
                        self.embedding_stats['failed_embeddings'] += 1
                        embedding_results['errors'].append({
                            'document_index': i,
                            'error': embedding_result.get('error', 'Unknown'),
                            'fund_name': chunked_data.get('processing_metadata', {}).get('fund_name', 'Unknown')
                        })
                        continue
                    
                    # Step 3: Enhance embedding result with metadata
                    enhanced_result = self._enhance_embedding_result(
                        chunked_data, embedding_result, i
                    )
                    
                    # Step 4: Validate embedding result
                    validation_result = self.bge_embedder.validate_embeddings(enhanced_result)
                    
                    # Step 5: Create final embedding data
                    final_result = self._create_final_embedding_data(
                        chunked_data, enhanced_result, validation_result
                    )
                    
                    embedding_results['embedding_results'].append(final_result)
                    self.embedding_stats['successful_embeddings'] += len(enhanced_result.get('embeddings', []))
                    
                    logger.info(f"✅ Successfully processed document {i+1}")
                    logger.info(f"   Embeddings generated: {len(enhanced_result.get('embeddings', []))}")
                    logger.info(f"   Quality score: {enhanced_result.get('quality_metrics', {}).get('overall_score', 0):.1f}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing document {i+1}: {e}")
                    self.embedding_stats['failed_embeddings'] += 1
                    embedding_results['errors'].append({
                        'document_index': i,
                        'error': str(e),
                        'fund_name': chunked_data.get('processing_metadata', {}).get('fund_name', 'Unknown')
                    })
            
            # Calculate summary statistics
            embedding_results['generation_summary'] = self._calculate_generation_summary()
            embedding_results['quality_summary'] = self._calculate_quality_summary()
            
            # Determine overall success
            total_documents = len(chunked_data_list)
            successful_documents = len([
                result for result in embedding_results['embedding_results']
                if result.get('success', False)
            ])
            
            success_rate = (successful_documents / total_documents) * 100 if total_documents > 0 else 0
            
            embedding_results['success'] = (
                success_rate >= 80.0 and  # At least 80% success rate
                len(embedding_results['errors']) == 0
            )
            
            self.embedding_stats['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"BGE embedding generation completed. Success rate: {success_rate:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Critical error in embedding pipeline: {e}")
            embedding_results['success'] = False
            embedding_results['errors'].append({
                'error': str(e),
                'stage': 'pipeline'
            })
        
        return embedding_results
    
    def _validate_config(self) -> bool:
        """
        Validate embedding configuration.
        """
        if not self.config.model_name:
            logger.error("No model name specified")
            return False
        
        if self.config.embedding_dim <= 0:
            logger.error(f"Invalid embedding dimension: {self.config.embedding_dim}")
            return False
        
        if self.config.batch_size <= 0:
            logger.error(f"Invalid batch size: {self.config.batch_size}")
            return False
        
        return True
    
    def _enhance_embedding_result(self, chunked_data: Dict[str, Any], 
                                embedding_result: Dict[str, Any], 
                                document_index: int) -> Dict[str, Any]:
        """
        Enhance embedding result with additional metadata.
        """
        enhanced_result = embedding_result.copy()
        
        # Add document metadata
        enhanced_result['document_metadata'] = {
            'document_index': document_index,
            'fund_name': chunked_data.get('processing_metadata', {}).get('fund_name', 'Unknown'),
            'chunk_count': len(chunked_data.get('chunks', [])),
            'processing_status': chunked_data.get('processing_metadata', {}).get('processing_status', 'unknown'),
            'processed_at': chunked_data.get('processing_metadata', {}).get('processed_at', '')
        }
        
        # Add embedding enhancement metadata
        enhanced_result['embedding_enhancements'] = {
            'bge_model': self.config.model_name,
            'financial_preprocessing': True,
            'domain_optimized': self.config.domain_adaptation,
            'batch_processing': self.config.batch_size,
            'normalization_applied': self.config.normalize_embeddings
        }
        
        return enhanced_result
    
    def _create_final_embedding_data(self, chunked_data: Dict[str, Any], 
                                   enhanced_result: Dict[str, Any], 
                                   validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create final embedding data structure.
        """
        final_data = {
            # Original chunked data
            'original_chunked_data': chunked_data,
            
            # Embedding results
            'embedding_metadata': {
                'fund_name': enhanced_result.get('document_metadata', {}).get('fund_name', 'Unknown'),
                'total_embeddings': len(enhanced_result.get('embeddings', [])),
                'embedding_success': enhanced_result.get('embeddings') is not None,
                'model_used': self.config.model_name,
                'embedding_dim': self.config.embedding_dim
            },
            
            # Generated embeddings
            'embeddings': enhanced_result.get('embeddings', []),
            
            # Validation results
            'validation_result': validation_result,
            
            # Quality metrics
            'quality_metrics': enhanced_result.get('quality_metrics', {}),
            
            # Processing metadata
            'processing_metadata': {
                'processed_at': datetime.now().isoformat(),
                'processing_phase': '1.3.4',
                'document_index': enhanced_result.get('document_metadata', {}).get('document_index', 0),
                'embedding_strategy': 'bge_financial_aware',
                'source_url': chunked_data.get('processing_metadata', {}).get('source_url', '')
            }
        }
        
        return final_data
    
    def _calculate_generation_summary(self) -> Dict[str, Any]:
        """
        Calculate generation summary statistics.
        """
        total = self.embedding_stats['total_chunks']
        successful = self.embedding_stats['successful_embeddings']
        failed = self.embedding_stats['failed_embeddings']
        
        return {
            'total_input_chunks': total,
            'successful_embeddings': successful,
            'failed_embeddings': failed,
            'success_rate': (successful / total) * 100 if total > 0 else 0,
            'generation_duration': self._calculate_duration(),
            'average_embedding_time': self.bge_embedder.get_embedding_stats().get('average_time_per_embedding', 0),
            'memory_usage_mb': self.bge_embedder.get_embedding_stats().get('memory_usage_mb', 0)
        }
    
    def _calculate_quality_summary(self) -> Dict[str, Any]:
        """
        Calculate quality summary from all results.
        """
        embedder_stats = self.bge_embedder.get_embedding_stats()
        
        return {
            'average_quality_score': embedder_stats.get('average_quality_score', 0),
            'dimension_consistency': embedder_stats.get('dimension_consistency', 0),
            'embedding_quality': embedder_stats.get('embedding_quality', 0),
            'financial_relevance': embedder_stats.get('financial_relevance', 0),
            'quality_status': 'excellent' if embedder_stats.get('average_quality_score', 0) >= 85.0 else 'good'
        }
    
    def _calculate_duration(self) -> str:
        """
        Calculate generation duration.
        """
        if not self.embedding_stats.get('started_at') or not self.embedding_stats.get('completed_at'):
            return "unknown"
        
        try:
            start = datetime.fromisoformat(self.embedding_stats['started_at'].replace(' ', 'T'))
            end = datetime.fromisoformat(self.embedding_stats['completed_at'].replace(' ', 'T'))
            duration = end - start
            
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "error"
    
    def _reset_embedding_stats(self):
        """
        Reset embedding statistics.
        """
        self.embedding_stats = {
            'started_at': None,
            'completed_at': None,
            'total_chunks': 0,
            'total_embeddings': 0,
            'successful_embeddings': 0,
            'failed_embeddings': 0,
            'embedding_results': {},
            'quality_summary': {},
            'errors': []
        }
        self.bge_embedder.reset_stats()
        logger.info("Embedding statistics reset")
    
    def generate_embedding_report(self, output_file: str = None) -> str:
        """
        Generate comprehensive embedding report.
        """
        logger.info("Generating embedding report...")
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'bge_embedding_generation',
                'phase': '1.3.4',
                'version': '1.0'
            },
            'embedding_stats': self.embedding_stats,
            'system_info': {
                'bge_config': {
                    'model_name': self.config.model_name,
                    'embedding_dim': self.config.embedding_dim,
                    'batch_size': self.config.batch_size,
                    'device': self.config.device,
                    'normalize_embeddings': self.config.normalize_embeddings
                },
                'bge_embedder_stats': self.bge_embedder.get_embedding_stats()
            },
            'recommendations': self._generate_recommendations()
        }
        
        report_json = json.dumps(report, indent=2, default=str)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_json)
            logger.info(f"Embedding report saved to {output_file}")
        
        return report_json
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on embedding results.
        """
        recommendations = []
        
        success_rate = (self.embedding_stats['successful_embeddings'] / 
                      self.embedding_stats['total_chunks']) * 100 if self.embedding_stats['total_chunks'] > 0 else 0
        
        # Success rate recommendations
        if success_rate < 100.0:
            recommendations.append(f"Improve success rate from {success_rate:.1f}% to 100%")
        
        # Quality score recommendations
        avg_quality = self.bge_embedder.get_embedding_stats().get('average_quality_score', 0)
        if avg_quality < 90.0:
            recommendations.append(f"Improve average quality score from {avg_quality:.1f}% to 90%+")
        
        # Performance recommendations
        avg_time = self.bge_embedder.get_embedding_stats().get('average_time_per_embedding', 0)
        if avg_time > 0.1:  # 100ms threshold
            recommendations.append(f"Optimize embedding speed (current: {avg_time:.3f}s per embedding)")
        
        # Memory recommendations
        memory_usage = self.bge_embedder.get_embedding_stats().get('memory_usage_mb', 0)
        if memory_usage > 4.0:  # 4GB threshold
            recommendations.append(f"Optimize memory usage (current: {memory_usage:.1f} MB)")
        
        # General recommendations
        recommendations.extend([
            "Monitor embedding performance regularly",
            "Consider fine-tuning BGE on financial domain",
            "Optimize batch size for better throughput",
            "Implement embedding caching for repeated chunks",
            "Monitor GPU utilization for efficiency"
        ])
        
        return recommendations

# Global implementation instance
embedding_generation_impl = EmbeddingGenerationImplementation()

if __name__ == "__main__":
    # Test embedding generation implementation
    print("🧠 Testing Phase 1.3.4 BGE Embedding Generation")
    print("=" * 60)
    
    try:
        # Initialize system
        if embedding_generation_impl.initialize_embedding_system():
            print("✅ System initialization successful")
            
            # Create test chunked data
            test_chunked_data = [
                {
                    'chunks': [
                        {
                            'chunk_id': 'primary_001',
                            'chunk_type': 'primary',
                            'content': 'HDFC Large Cap Fund Direct Growth is a large cap equity fund focusing on established companies',
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
                    ],
                    'processing_metadata': {
                        'fund_name': 'HDFC Large Cap Fund Direct Growth',
                        'source_url': 'https://groww.in/test',
                        'processing_status': 'excellent',
                        'processed_at': '2024-01-01 12:30:00'
                    }
                }
            ]
            
            # Run embedding generation
            print("\n🧠 Starting BGE embedding generation...")
            results = embedding_generation_impl.generate_embeddings_for_chunks(test_chunked_data)
            
            # Display results
            print(f"\n📊 Embedding Results:")
            print(f"Success: {results.get('success', False)}")
            print(f"Total Documents: {results.get('generation_summary', {}).get('total_input_chunks', 0)}")
            print(f"Successful Embeddings: {results.get('generation_summary', {}).get('successful_embeddings', 0)}")
            print(f"Success Rate: {results.get('generation_summary', {}).get('success_rate', 0):.1f}%")
            
            # Quality summary
            quality_summary = results.get('quality_summary', {})
            print(f"\n🎯 Quality Summary:")
            print(f"Avg Quality Score: {quality_summary.get('average_quality_score', 0):.1f}")
            print(f"Dimension Consistency: {quality_summary.get('dimension_consistency', 0):.1f}%")
            print(f"Financial Relevance: {quality_summary.get('financial_relevance', 0):.1f}%")
            print(f"Quality Status: {quality_summary.get('quality_status', 'unknown')}")
            
            # Show embedding results
            embedding_results = results.get('embedding_results', [])
            print(f"\n📄 Generated Embeddings:")
            for i, result in enumerate(embedding_results[:2], 1):  # Show first 2
                fund_name = result.get('embedding_metadata', {}).get('fund_name', 'Unknown')
                embedding_count = result.get('embedding_metadata', {}).get('total_embeddings', 0)
                quality_score = result.get('quality_metrics', {}).get('overall_score', 0)
                print(f"  {i}. {fund_name} (Embeddings: {embedding_count}, Quality: {quality_score:.1f})")
            
            if len(embedding_results) > 2:
                print(f"  ... and {len(embedding_results) - 2} more documents")
            
            # Errors
            errors = results.get('errors', [])
            if errors:
                print(f"\n❌ Errors:")
                for error in errors[:2]:
                    print(f"  • {error}")
            
            # Generate report
            report_file = f"bge_embedding_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            embedding_generation_impl.generate_embedding_report(report_file)
            print(f"\n📄 Detailed report saved to: {report_file}")
            
            # Recommendations
            recommendations = results.get('implementation_metadata', {}).get('recommendations', [])
            if recommendations:
                print(f"\n💡 Recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"  {i}. {rec}")
        
        else:
            print("❌ System initialization failed")
            
    finally:
        print("\n🏁 Testing completed")
        print("=" * 60)
