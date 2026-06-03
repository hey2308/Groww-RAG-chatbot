"""
Phase 1.3.5 - Vector Database Integration
Main implementation script for ChromaDB integration with BGE embeddings
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from chroma_integration import chroma_integration, ChromaConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VectorDatabaseIntegration:
    """
    Main implementation of Phase 1.3.5 Vector Database Integration.
    Integrates BGE embeddings with ChromaDB for mutual fund data.
    """
    
    def __init__(self, config: ChromaConfig = None):
        """
        Initialize vector database integration.
        """
        self.chroma_integration = chroma_integration
        self.config = config or ChromaConfig()
        
        self.integration_stats = {
            'started_at': None,
            'completed_at': None,
            'total_documents': 0,
            'total_embeddings': 0,
            'successful_insertions': 0,
            'failed_insertions': 0,
            'query_count': 0,
            'integration_results': {},
            'collection_stats': {},
            'errors': []
        }
        
        logger.info("Vector database integration initialized")
        logger.info(f"Config: collection={self.config.collection_name}, dim={self.config.embedding_dim}")
    
    def initialize_vector_db(self) -> bool:
        """
        Initialize ChromaDB for BGE embeddings.
        """
        logger.info("Initializing ChromaDB for BGE embeddings...")
        
        try:
            # Step 1: Validate configuration
            if not self._validate_config():
                logger.error("❌ Invalid vector database configuration")
                return False
            
            # Step 2: Initialize ChromaDB
            if not self.chroma_integration.initialize_chromadb():
                logger.error("❌ ChromaDB initialization failed")
                return False
            
            # Step 3: Validate collection setup
            collection_info = self.chroma_integration._validate_collection_setup()
            if not collection_info.get('valid', False):
                logger.error(f"❌ Collection validation failed: {collection_info.get('error', 'Unknown')}")
                return False
            
            # Step 4: Reset statistics
            self._reset_integration_stats()
            
            logger.info("✅ Vector database initialized successfully")
            logger.info(f"Collection: {self.config.collection_name}")
            logger.info(f"Embedding dimension: {self.config.embedding_dim}")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    def store_embeddings(self, embedding_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store BGE embeddings in ChromaDB.
        """
        logger.info(f"Storing {len(embedding_results)} embedding results in ChromaDB")
        
        self.integration_stats['started_at'] = datetime.now().isoformat()
        self.integration_stats['total_documents'] = len(embedding_results)
        
        storage_result = {
            'storage_metadata': {
                'phase': '1.3.5',
                'version': '1.0',
                'started_at': self.integration_stats['started_at'],
                'input_documents': len(embedding_results),
                'embedding_model': 'BGE-small-en-v1.5'
            },
            'storage_results': [],
            'storage_summary': {},
            'collection_stats': {},
            'success': False,
            'errors': []
        }
        
        try:
            # Process each embedding result
            for i, embedding_result in enumerate(embedding_results):
                logger.info(f"Processing document {i+1}/{len(embedding_results)}")
                
                try:
                    # Step 1: Extract embeddings from result
                    embeddings = embedding_result.get('embeddings', [])
                    
                    if not embeddings:
                        logger.warning(f"⚠️ No embeddings found in document {i+1}")
                        self.integration_stats['failed_insertions'] += 1
                        continue
                    
                    # Step 2: Store embeddings in ChromaDB
                    insertion_result = self.chroma_integration.add_embeddings(embeddings)
                    
                    if not insertion_result.get('success', False):
                        logger.error(f"❌ ChromaDB insertion failed: {insertion_result.get('error', 'Unknown')}")
                        self.integration_stats['failed_insertions'] += 1
                        storage_result['errors'].append({
                            'document_index': i,
                            'error': insertion_result.get('error', 'Unknown'),
                            'fund_name': embedding_result.get('embedding_metadata', {}).get('fund_name', 'Unknown')
                        })
                        continue
                    
                    # Step 3: Enhance storage result
                    enhanced_result = self._enhance_storage_result(
                        embedding_result, insertion_result, i
                    )
                    
                    # Step 4: Validate storage result
                    validation_result = self._validate_storage_result(enhanced_result)
                    
                    # Step 5: Create final storage data
                    final_result = self._create_final_storage_data(
                        embedding_result, enhanced_result, validation_result
                    )
                    
                    storage_result['storage_results'].append(final_result)
                    self.integration_stats['successful_insertions'] += 1
                    self.integration_stats['total_embeddings'] += len(embeddings)
                    
                    logger.info(f"✅ Successfully stored document {i+1}")
                    logger.info(f"   Embeddings stored: {len(embeddings)}")
                    logger.info(f"   Storage time: {insertion_result.get('insertion_stats', {}).get('average_time_per_embedding', 0):.3f}s")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing document {i+1}: {e}")
                    self.integration_stats['failed_insertions'] += 1
                    storage_result['errors'].append({
                        'document_index': i,
                        'error': str(e),
                        'fund_name': embedding_result.get('embedding_metadata', {}).get('fund_name', 'Unknown')
                    })
            
            # Calculate summary statistics
            storage_result['storage_summary'] = self._calculate_storage_summary()
            storage_result['collection_stats'] = self.chroma_integration.get_collection_stats()
            
            # Determine overall success
            success_rate = (self.integration_stats['successful_insertions'] / 
                          self.integration_stats['total_documents']) * 100 if self.integration_stats['total_documents'] > 0 else 0
            
            storage_result['success'] = (
                success_rate >= 90.0 and  # At least 90% success rate
                len(storage_result['errors']) == 0
            )
            
            self.integration_stats['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"Vector storage completed. Success rate: {success_rate:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Critical error in storage pipeline: {e}")
            storage_result['success'] = False
            storage_result['errors'].append({
                'error': str(e),
                'stage': 'pipeline'
            })
        
        return storage_result
    
    def _validate_config(self) -> bool:
        """
        Validate vector database configuration.
        """
        if not self.config.collection_name:
            logger.error("No collection name specified")
            return False
        
        if self.config.embedding_dim <= 0:
            logger.error(f"Invalid embedding dimension: {self.config.embedding_dim}")
            return False
        
        if self.config.batch_size <= 0:
            logger.error(f"Invalid batch size: {self.config.batch_size}")
            return False
        
        return True
    
    def _enhance_storage_result(self, embedding_result: Dict[str, Any], 
                             insertion_result: Dict[str, Any], 
                             document_index: int) -> Dict[str, Any]:
        """
        Enhance storage result with additional metadata.
        """
        enhanced_result = insertion_result.copy()
        
        # Add document metadata
        enhanced_result['document_metadata'] = {
            'document_index': document_index,
            'fund_name': embedding_result.get('embedding_metadata', {}).get('fund_name', 'Unknown'),
            'total_embeddings': len(embedding_result.get('embeddings', [])),
            'embedding_success': embedding_result.get('success', False),
            'model_used': embedding_result.get('embedding_metadata', {}).get('model_used', 'BGE-small-en-v1.5'),
            'embedding_dim': embedding_result.get('embedding_metadata', {}).get('embedding_dim', 384)
        }
        
        # Add storage enhancement metadata
        enhanced_result['storage_enhancements'] = {
            'chromadb_collection': self.config.collection_name,
            'batch_processing': True,
            'financial_data_optimized': True,
            'bge_embeddings': True,
            'similarity_metric': self.config.embedding_function,
            'storage_timestamp': datetime.now().isoformat()
        }
        
        return enhanced_result
    
    def _validate_storage_result(self, enhanced_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate storage result for quality.
        """
        validation_result = {
            'validation_timestamp': datetime.now().isoformat(),
            'overall_status': 'passed',
            'storage_validations': {},
            'validation_score': 0.0,
            'issues': []
        }
        
        try:
            # Validate insertion success
            if not enhanced_result.get('success', False):
                validation_result['overall_status'] = 'failed'
                validation_result['issues'].append('Storage insertion failed')
                return validation_result
            
            # Validate embedding consistency
            embeddings = enhanced_result.get('embeddings', [])
            if embeddings:
                dimension_validation = self._validate_embedding_dimensions(embeddings)
                validation_result['storage_validations']['dimension_consistency'] = dimension_validation
                validation_result['validation_score'] += dimension_validation.get('score', 0) * 0.4
                
                if not dimension_validation.get('valid', True):
                    validation_result['overall_status'] = 'failed'
                    validation_result['issues'].append(dimension_validation.get('error', 'Dimension validation failed'))
            
            # Validate metadata completeness
            metadata_validation = self._validate_metadata_completeness(enhanced_result)
            validation_result['storage_validations']['metadata_completeness'] = metadata_validation
            validation_result['validation_score'] += metadata_validation.get('score', 0) * 0.3
            if not metadata_validation.get('valid', True):
                validation_result['overall_status'] = 'warning'
                validation_result['issues'].append(metadata_validation.get('error', 'Metadata validation failed'))
            
            # Validate financial data quality
            financial_validation = self._validate_financial_data_quality(enhanced_result)
            validation_result['storage_validations']['financial_quality'] = financial_validation
            validation_result['validation_score'] += financial_validation.get('score', 0) * 0.3
            
            # Determine overall status
            if validation_result['validation_score'] >= 80.0:
                validation_result['overall_status'] = 'passed'
            elif validation_result['validation_score'] >= 60.0:
                validation_result['overall_status'] = 'warning'
            else:
                validation_result['overall_status'] = 'failed'
            
        except Exception as e:
            logger.error(f"Error validating storage result: {e}")
            validation_result['overall_status'] = 'error'
            validation_result['error'] = str(e)
        
        return validation_result
    
    def _validate_embedding_dimensions(self, embeddings: List[Any]) -> Dict[str, Any]:
        """
        Validate embedding dimensions consistency.
        """
        validation = {
            'valid': True,
            'score': 100.0,
            'error': None,
            'dimensions_found': set(),
            'inconsistent_count': 0
        }
        
        expected_dim = self.config.embedding_dim
        
        for embedding in embeddings:
            if hasattr(embedding, 'shape'):
                actual_dim = embedding.shape[-1] if len(embedding.shape) > 1 else len(embedding)
                validation['dimensions_found'].add(actual_dim)
                
                if actual_dim != expected_dim:
                    validation['inconsistent_count'] += 1
        
        # Calculate score
        if validation['inconsistent_count'] > 0:
            validation['score'] = max(0, 100 - (validation['inconsistent_count'] * 20))
            validation['error'] = f"Found {len(validation['dimensions_found'])} different dimensions: {list(validation['dimensions_found'])}"
            validation['valid'] = False
        
        return validation
    
    def _validate_metadata_completeness(self, enhanced_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate metadata completeness.
        """
        validation = {
            'valid': True,
            'score': 100.0,
            'error': None,
            'missing_fields': [],
            'present_fields': []
        }
        
        # Check required metadata fields
        required_fields = ['fund_name', 'model_used', 'embedding_dim']
        metadata = enhanced_result.get('document_metadata', {})
        
        for field in required_fields:
            if field in metadata and metadata[field]:
                validation['present_fields'].append(field)
            else:
                validation['missing_fields'].append(field)
                validation['valid'] = False
        
        # Calculate score
        if validation['missing_fields']:
            validation['score'] = max(0, 100 - (len(validation['missing_fields']) * 25))
            validation['error'] = f"Missing required fields: {validation['missing_fields']}"
        
        return validation
    
    def _validate_financial_data_quality(self, enhanced_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate financial data quality in storage.
        """
        validation = {
            'valid': True,
            'score': 100.0,
            'error': None,
            'financial_indicators': {},
            'quality_issues': []
        }
        
        # Check financial data indicators
        metadata = enhanced_result.get('document_metadata', {})
        fund_name = metadata.get('fund_name', '')
        
        # Fund name validation
        if fund_name and len(fund_name) < 5:
            validation['financial_indicators']['fund_name_quality'] = 'poor'
            validation['quality_issues'].append('Fund name too short')
            validation['valid'] = False
        elif fund_name:
            validation['financial_indicators']['fund_name_quality'] = 'good'
        else:
            validation['financial_indicators']['fund_name_quality'] = 'excellent'
        
        # Model validation
        model_used = metadata.get('model_used', '')
        if 'BGE' not in model_used:
            validation['financial_indicators']['model_compliance'] = 'poor'
            validation['quality_issues'].append('Non-BGE model detected')
            validation['valid'] = False
        elif 'BGE-small-en' in model_used:
            validation['financial_indicators']['model_compliance'] = 'excellent'
        else:
            validation['financial_indicators']['model_compliance'] = 'good'
        
        # Calculate score
        if validation['quality_issues']:
            validation['score'] = max(0, 100 - (len(validation['quality_issues']) * 15))
        else:
            validation['score'] = 100.0
        
        validation['financial_indicators']['overall_quality'] = (
            'excellent' if validation['score'] >= 90.0 else
            'good' if validation['score'] >= 80.0 else
            'fair' if validation['score'] >= 60.0 else
            'poor'
        )
        
        return validation
    
    def _create_final_storage_data(self, embedding_result: Dict[str, Any], 
                               enhanced_result: Dict[str, Any], 
                               validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create final storage data structure.
        """
        final_data = {
            # Original embedding result
            'original_embedding_result': embedding_result,
            
            # Enhanced storage result
            'storage_metadata': enhanced_result.get('document_metadata', {}),
            'storage_enhancements': enhanced_result.get('storage_enhancements', {}),
            
            # Validation results
            'validation_result': validation_result,
            
            # Quality metrics
            'quality_metrics': {
                'overall_score': validation_result.get('validation_score', 0),
                'dimension_consistency': validation_result.get('storage_validations', {}).get('dimension_consistency', {}).get('score', 0),
                'metadata_completeness': validation_result.get('storage_validations', {}).get('metadata_completeness', {}).get('score', 0),
                'financial_quality': validation_result.get('storage_validations', {}).get('financial_quality', {}).get('score', 0)
            },
            
            # Processing metadata
            'processing_metadata': {
                'processed_at': datetime.now().isoformat(),
                'processing_phase': '1.3.5',
                'document_index': enhanced_result.get('document_metadata', {}).get('document_index', 0),
                'storage_strategy': 'bge_chromadb',
                'source_url': embedding_result.get('document_metadata', {}).get('source_url', '')
            }
        }
        
        return final_data
    
    def _calculate_storage_summary(self) -> Dict[str, Any]:
        """
        Calculate storage summary statistics.
        """
        total = self.integration_stats['total_documents']
        successful = self.integration_stats['successful_insertions']
        failed = self.integration_stats['failed_insertions']
        total_embeddings = self.integration_stats['total_embeddings']
        
        return {
            'total_documents': total,
            'successful_insertions': successful,
            'failed_insertions': failed,
            'total_embeddings': total_embeddings,
            'success_rate': (successful / total) * 100 if total > 0 else 0,
            'average_embeddings_per_document': total_embeddings / successful if successful > 0 else 0,
            'storage_duration': self._calculate_duration()
        }
    
    def _calculate_duration(self) -> str:
        """
        Calculate storage duration.
        """
        if not self.integration_stats.get('started_at') or not self.integration_stats.get('completed_at'):
            return "unknown"
        
        try:
            start = datetime.fromisoformat(self.integration_stats['started_at'].replace(' ', 'T'))
            end = datetime.fromisoformat(self.integration_stats['completed_at'].replace(' ', 'T'))
            duration = end - start
            
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "error"
    
    def _reset_integration_stats(self):
        """
        Reset integration statistics.
        """
        self.integration_stats = {
            'started_at': None,
            'completed_at': None,
            'total_documents': 0,
            'total_embeddings': 0,
            'successful_insertions': 0,
            'failed_insertions': 0,
            'query_count': 0,
            'integration_results': {},
            'collection_stats': {},
            'errors': []
        }
        self.chroma_integration.reset_stats()
        logger.info("Integration statistics reset")
    
    def generate_integration_report(self, output_file: str = None) -> str:
        """
        Generate comprehensive integration report.
        """
        logger.info("Generating vector database integration report...")
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'vector_database_integration',
                'phase': '1.3.5',
                'version': '1.0'
            },
            'integration_stats': self.integration_stats,
            'system_info': {
                'chroma_config': {
                    'collection_name': self.config.collection_name,
                    'persist_directory': self.config.persist_directory,
                    'embedding_function': self.config.embedding_function,
                    'embedding_dim': self.config.embedding_dim
                },
                'chroma_integration_stats': self.chroma_integration.get_collection_stats()
            },
            'recommendations': self._generate_recommendations()
        }
        
        report_json = json.dumps(report, indent=2, default=str)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_json)
            logger.info(f"Integration report saved to {output_file}")
        
        return report_json
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on integration results.
        """
        recommendations = []
        
        success_rate = (self.integration_stats['successful_insertions'] / 
                      self.integration_stats['total_documents']) * 100 if self.integration_stats['total_documents'] > 0 else 0
        
        # Success rate recommendations
        if success_rate < 100.0:
            recommendations.append(f"Improve success rate from {success_rate:.1f}% to 100%")
        
        # Performance recommendations
        total_embeddings = self.integration_stats['total_embeddings']
        if total_embeddings > 10000:
            recommendations.append("Consider implementing vector indexing for better scalability")
        
        # General recommendations
        recommendations.extend([
            "Monitor vector database performance regularly",
            "Implement query result caching for common queries",
            "Set up automated backup for vector database",
            "Consider vector quantization for storage optimization"
        ])
        
        return recommendations

# Global integration instance
vector_db_integration = VectorDatabaseIntegration()

if __name__ == "__main__":
    # Test vector database integration
    print("🗄️ Testing Phase 1.3.5 Vector Database Integration")
    print("=" * 60)
    
    # Test embeddings data
    test_embeddings = [
        {
            'embedding_metadata': {
                'fund_name': 'HDFC Large Cap Fund Direct Growth',
                'model_used': 'BGE-small-en-v1.5',
                'embedding_dim': 384,
                'created_at': '2024-01-01 12:00:00'
            },
            'embeddings': [
                {
                    'id': 'emb_001',
                    'embedding': [0.1, 0.2, 0.3] * 128,  # 384 dimensions
                    'metadata': {
                        'chunk_id': 'primary_001',
                        'chunk_type': 'primary',
                        'fund_name': 'HDFC Large Cap Fund Direct Growth',
                        'fund_type': 'Direct Growth',
                        'fund_category': 'Large Cap',
                        'priority': 'high',
                        'token_count': 25,
                        'embedding_metadata': {
                            'model_used': 'BGE-small-en-v1.5',
                            'embedding_dim': 384,
                            'normalized': True,
                            'created_at': '2024-01-01 12:00:00'
                        }
                    }
                },
                {
                    'id': 'emb_002',
                    'embedding': [0.4, 0.5, 0.6] * 128,  # 384 dimensions
                    'metadata': {
                        'chunk_id': 'metric_001',
                        'chunk_type': 'metric',
                        'fund_name': 'HDFC Large Cap Fund Direct Growth',
                        'fund_type': 'Direct Growth',
                        'fund_category': 'Large Cap',
                        'priority': 'high',
                        'token_count': 18,
                        'embedding_metadata': {
                            'model_used': 'BGE-small-en-v1.5',
                            'embedding_dim': 384,
                            'normalized': True,
                            'created_at': '2024-01-01 12:00:00'
                        }
                    }
                }
            ],
            'success': True
        }
    ]
    
    try:
        # Initialize system
        if vector_db_integration.initialize_vector_db():
            print("✅ Vector database initialization successful")
            
            # Store embeddings
            print("\n📄 Storing embeddings...")
            storage_result = vector_db_integration.store_embeddings(test_embeddings)
            
            # Display results
            print(f"Storage Success: {storage_result.get('success', False)}")
            print(f"Total Documents: {storage_result.get('storage_summary', {}).get('total_documents', 0)}")
            print(f"Successful: {storage_result.get('storage_summary', {}).get('successful_insertions', 0)}")
            print(f"Total Embeddings: {storage_result.get('storage_summary', {}).get('total_embeddings', 0)}")
            
            # Test query functionality
            print("\n🔍 Testing query functionality...")
            query_result = vector_db_integration.query_vector_db("HDFC Large Cap Fund", n_results=3)
            
            print(f"Query Success: {query_result.get('success', False)}")
            print(f"Results: {len(query_result.get('query_results', []))}")
            
            # Show query results
            query_results = query_result.get('query_results', [])
            print(f"\n📋 Query Results:")
            for i, result in enumerate(query_results[:3], 1):
                fund_name = result.get('financial_context', {}).get('fund_name', 'Unknown')
                similarity = result.get('similarity_score', 0)
                rank = result.get('rank', 0)
                print(f"  {i}. {fund_name} (Similarity: {similarity:.3f}, Rank: {rank})")
            
            if len(query_results) > 3:
                print(f"  ... and {len(query_results) - 3} more results")
            
            # Generate report
            report_file = f"vector_db_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            vector_db_integration.generate_integration_report(report_file)
            print(f"\n📄 Detailed report saved to: {report_file}")
            
            # Show recommendations
            recommendations = storage_result.get('storage_metadata', {}).get('recommendations', [])
            if recommendations:
                print(f"\n💡 Recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"  {i}. {rec}")
        
        else:
            print("❌ Vector database initialization failed")
            
    except Exception as e:
        print(f"❌ Error testing vector database integration: {e}")
    
    print("\n✅ Vector database integration testing completed")
    print("=" * 60)
