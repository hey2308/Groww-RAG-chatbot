"""
Phase 1.3.3 - Text Chunking Strategy
Main implementation script for financial data-specific chunking
"""

import logging
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from financial_chunker import financial_chunker, ChunkConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TextChunkingImplementation:
    """
    Main implementation of Phase 1.3.3 Text Chunking Strategy.
    Implements financial data-specific chunking with multiple chunk types.
    """
    
    def __init__(self, config: ChunkConfig = None):
        """
        Initialize text chunking implementation.
        """
        self.financial_chunker = financial_chunker
        self.config = config or ChunkConfig()
        
        self.chunking_stats = {
            'started_at': None,
            'completed_at': None,
            'total_documents': 0,
            'total_chunks': 0,
            'successful_chunkings': 0,
            'failed_chunkings': 0,
            'chunking_results': {},
            'quality_summary': {},
            'errors': []
        }
        
        logger.info("Text chunking implementation initialized")
        logger.info(f"Config: primary={self.config.primary_chunk_size}, overlap={self.config.overlap_tokens}")
    
    def initialize_chunking_system(self) -> bool:
        """
        Initialize all chunking components.
        """
        logger.info("Initializing text chunking system...")
        
        try:
            # Step 1: Validate configuration
            if not self._validate_config():
                logger.error("❌ Invalid chunking configuration")
                return False
            
            # Step 2: Initialize financial chunker
            chunker_stats = self.financial_chunker.get_chunking_stats()
            logger.info(f"Financial chunker ready: {chunker_stats['chunker_version']}")
            
            # Step 3: Reset statistics
            self._reset_chunking_stats()
            
            logger.info("✅ Text chunking system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    def chunk_cleaned_data(self, cleaned_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Chunk cleaned data from Phase 1.3.2 using financial-aware strategy.
        """
        logger.info(f"Starting financial chunking for {len(cleaned_data_list)} documents")
        
        self.chunking_stats['started_at'] = datetime.now().isoformat()
        self.chunking_stats['total_documents'] = len(cleaned_data_list)
        
        chunking_results = {
            'implementation_metadata': {
                'phase': '1.3.3',
                'version': '1.0',
                'started_at': self.chunking_stats['started_at'],
                'input_documents': len(cleaned_data_list),
                'chunking_strategy': 'financial_aware'
            },
            'chunking_results': [],
            'chunking_summary': {},
            'quality_summary': {},
            'success': False,
            'errors': []
        }
        
        try:
            # Process each cleaned document
            for i, cleaned_data in enumerate(cleaned_data_list):
                logger.info(f"Chunking document {i+1}/{len(cleaned_data_list)}")
                
                try:
                    # Step 1: Extract fund data from cleaned data
                    fund_data = self._extract_fund_data_from_cleaned(cleaned_data)
                    
                    if not fund_data:
                        logger.warning(f"⚠️ No fund data found in document {i+1}")
                        self.chunking_stats['failed_chunkings'] += 1
                        continue
                    
                    # Step 2: Apply financial chunking
                    chunking_result = self.financial_chunker.chunk_fund_data(fund_data)
                    
                    if not chunking_result.get('chunking_success', False):
                        logger.error(f"❌ Financial chunking failed: {chunking_result.get('error', 'Unknown')}")
                        self.chunking_stats['failed_chunkings'] += 1
                        chunking_results['errors'].append({
                            'document_index': i,
                            'error': chunking_result.get('error', 'Unknown'),
                            'fund_name': fund_data.get('fund_name', 'Unknown')
                        })
                        continue
                    
                    # Step 3: Enhance chunking result with metadata
                    enhanced_result = self._enhance_chunking_result(
                        cleaned_data, chunking_result, i
                    )
                    
                    # Step 4: Validate chunking result
                    validation_result = self._validate_chunking_result(enhanced_result)
                    
                    # Step 5: Create final chunked data
                    final_result = self._create_final_chunked_data(
                        cleaned_data, enhanced_result, validation_result
                    )
                    
                    chunking_results['chunking_results'].append(final_result)
                    self.chunking_stats['successful_chunkings'] += 1
                    self.chunking_stats['total_chunks'] += len(enhanced_result.get('chunks', []))
                    
                    logger.info(f"✅ Successfully chunked document {i+1}")
                    logger.info(f"   Chunks created: {len(enhanced_result.get('chunks', []))}")
                    logger.info(f"   Quality score: {enhanced_result.get('quality_metrics', {}).get('overall_score', 0):.1f}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing document {i+1}: {e}")
                    self.chunking_stats['failed_chunkings'] += 1
                    chunking_results['errors'].append({
                        'document_index': i,
                        'error': str(e),
                        'fund_name': cleaned_data.get('processing_metadata', {}).get('fund_name', 'Unknown')
                    })
            
            # Calculate summary statistics
            chunking_results['chunking_summary'] = self._calculate_chunking_summary()
            chunking_results['quality_summary'] = self._calculate_quality_summary()
            
            # Determine overall success
            success_rate = (self.chunking_stats['successful_chunkings'] / 
                          self.chunking_stats['total_documents']) * 100 if self.chunking_stats['total_documents'] > 0 else 0
            
            chunking_results['success'] = (
                success_rate >= 80.0 and  # At least 80% success rate
                len(chunking_results['errors']) == 0
            )
            
            self.chunking_stats['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"Financial chunking completed. Success rate: {success_rate:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Critical error in chunking pipeline: {e}")
            chunking_results['success'] = False
            chunking_results['errors'].append({
                'error': str(e),
                'stage': 'pipeline'
            })
        
        return chunking_results
    
    def _validate_config(self) -> bool:
        """
        Validate chunking configuration.
        """
        if self.config.primary_chunk_size < 200 or self.config.primary_chunk_size > 800:
            logger.error(f"Invalid primary chunk size: {self.config.primary_chunk_size}")
            return False
        
        if self.config.overlap_tokens < 50 or self.config.overlap_tokens > 200:
            logger.error(f"Invalid overlap tokens: {self.config.overlap_tokens}")
            return False
        
        if not self.config.financial_boundary_patterns:
            logger.error("No financial boundary patterns configured")
            return False
        
        return True
    
    def _extract_fund_data_from_cleaned(self, cleaned_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract fund data from cleaned data structure.
        """
        # Try to get fund data from different possible locations
        if 'fund_data' in cleaned_data:
            return cleaned_data['fund_data']
        
        # Try to reconstruct from processing metadata
        fund_data = {
            'fund_name': cleaned_data.get('processing_metadata', {}).get('fund_name'),
            'source_url': cleaned_data.get('processing_metadata', {}).get('source_url'),
            'scraped_at': cleaned_data.get('original_data', {}).get('scraped_at')
        }
        
        # Add fund details if available
        if 'fund_data' in cleaned_data and isinstance(cleaned_data['fund_data'], dict):
            fund_data.update(cleaned_data['fund_data'])
        
        # Validate essential fields
        if not fund_data.get('fund_name'):
            return None
        
        return fund_data
    
    def _enhance_chunking_result(self, cleaned_data: Dict[str, Any], 
                                chunking_result: Dict[str, Any], 
                                document_index: int) -> Dict[str, Any]:
        """
        Enhance chunking result with additional metadata.
        """
        enhanced_result = chunking_result.copy()
        
        # Add document metadata
        enhanced_result['document_metadata'] = {
            'document_index': document_index,
            'cleaning_score': cleaned_data.get('quality_metrics', {}).get('overall_quality_score', 0),
            'processing_status': cleaned_data.get('processing_metadata', {}).get('processing_status', 'unknown'),
            'cleaned_at': cleaned_data.get('processing_metadata', {}).get('processed_at', '')
        }
        
        # Add chunking enhancement metadata
        enhanced_result['chunking_enhancements'] = {
            'financial_aware': True,
            'boundary_patterns_used': len(self.config.financial_boundary_patterns),
            'overlap_applied': self.config.overlap_tokens > 0,
            'specialized_chunks_created': len(set(
                chunk.get('chunk_type', 'unknown') for chunk in chunking_result.get('chunks', [])
            ))
        }
        
        return enhanced_result
    
    def _validate_chunking_result(self, enhanced_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate chunking result for quality and completeness.
        """
        validation_result = {
            'validation_timestamp': datetime.now().isoformat(),
            'overall_status': 'passed',
            'chunk_validations': {},
            'validation_score': 0.0,
            'issues': []
        }
        
        try:
            chunks = enhanced_result.get('chunks', [])
            
            if not chunks:
                validation_result['overall_status'] = 'failed'
                validation_result['issues'].append('No chunks created')
                return validation_result
            
            # Validate each chunk
            for i, chunk in enumerate(chunks):
                chunk_validation = self._validate_individual_chunk(chunk, i)
                validation_result['chunk_validations'][f'chunk_{i+1}'] = chunk_validation
                
                if chunk_validation.get('status') == 'failed':
                    validation_result['overall_status'] = 'failed'
                    validation_result['issues'].append(f'Chunk {i+1} validation failed')
            
            # Validate overall chunking quality
            quality_metrics = enhanced_result.get('quality_metrics', {})
            overall_score = quality_metrics.get('overall_score', 0)
            
            if overall_score < 70.0:
                validation_result['overall_status'] = 'warning'
                validation_result['issues'].append(f'Low overall quality score: {overall_score}')
            
            validation_result['validation_score'] = overall_score
            
        except Exception as e:
            logger.error(f"Error validating chunking result: {e}")
            validation_result['overall_status'] = 'error'
            validation_result['error'] = str(e)
        
        return validation_result
    
    def _validate_individual_chunk(self, chunk: Dict[str, Any], chunk_index: int) -> Dict[str, Any]:
        """
        Validate individual chunk for quality.
        """
        validation = {
            'chunk_index': chunk_index,
            'status': 'passed',
            'issues': [],
            'quality_score': 0.0
        }
        
        # Check required fields
        required_fields = ['chunk_id', 'chunk_type', 'content', 'token_count']
        for field in required_fields:
            if field not in chunk:
                validation['status'] = 'failed'
                validation['issues'].append(f'Missing required field: {field}')
        
        # Check content quality
        content = chunk.get('content', '')
        if not content or len(content.strip()) < 10:
            validation['status'] = 'warning'
            validation['issues'].append('Content too short or empty')
        
        # Check token count
        token_count = chunk.get('token_count', 0)
        if token_count < 50 or token_count > 800:
            validation['status'] = 'warning'
            validation['issues'].append(f'Token count outside optimal range: {token_count}')
        
        # Calculate quality score
        quality_metadata = chunk.get('quality_metadata', {})
        completeness = quality_metadata.get('completeness_score', 0)
        relevance = quality_metadata.get('relevance_score', 0)
        
        validation['quality_score'] = (completeness * 0.6) + (relevance * 0.4)
        
        return validation
    
    def _create_final_chunked_data(self, cleaned_data: Dict[str, Any], 
                                   enhanced_result: Dict[str, Any], 
                                   validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create final chunked data structure.
        """
        final_data = {
            # Original cleaned data
            'original_cleaned_data': cleaned_data,
            
            # Chunking results
            'chunking_metadata': {
                'fund_name': enhanced_result.get('fund_name', 'Unknown'),
                'chunking_confidence': enhanced_result.get('quality_metrics', {}).get('overall_score', 0),
                'chunking_status': enhanced_result.get('chunking_success', False),
                'total_chunks': len(enhanced_result.get('chunks', [])),
                'chunking_enhancements': enhanced_result.get('chunking_enhancements', {})
            },
            
            # Chunked content
            'chunks': enhanced_result.get('chunks', []),
            
            # Validation results
            'validation_result': validation_result,
            
            # Quality metrics
            'quality_metrics': enhanced_result.get('quality_metrics', {}),
            
            # Processing metadata
            'processing_metadata': {
                'processed_at': datetime.now().isoformat(),
                'processing_phase': '1.3.3',
                'document_index': enhanced_result.get('document_metadata', {}).get('document_index', 0),
                'chunking_strategy': 'financial_aware',
                'source_url': cleaned_data.get('processing_metadata', {}).get('source_url', '')
            }
        }
        
        return final_data
    
    def _calculate_chunking_summary(self) -> Dict[str, Any]:
        """
        Calculate chunking summary statistics.
        """
        total = self.chunking_stats['total_documents']
        successful = self.chunking_stats['successful_chunkings']
        failed = self.chunking_stats['failed_chunkings']
        total_chunks = self.chunking_stats['total_chunks']
        
        return {
            'total_documents': total,
            'successful_chunkings': successful,
            'failed_chunkings': failed,
            'total_chunks_created': total_chunks,
            'success_rate': (successful / total) * 100 if total > 0 else 0,
            'average_chunks_per_document': total_chunks / successful if successful > 0 else 0,
            'chunking_duration': self._calculate_duration(),
            'chunk_types_used': self._get_chunk_types_used()
        }
    
    def _calculate_quality_summary(self) -> Dict[str, Any]:
        """
        Calculate quality summary from all results.
        """
        chunker_stats = self.financial_chunker.get_chunking_stats()
        
        return {
            'average_chunk_size': chunker_stats.get('average_chunk_size', 0),
            'chunk_type_distribution': chunker_stats.get('chunk_types', {}),
            'average_chunks_per_document': chunker_stats.get('average_chunks_per_document', 0),
            'quality_status': 'excellent' if chunker_stats.get('average_chunk_size', 0) >= 350 else 'good',
            'chunking_efficiency': self._calculate_chunking_efficiency()
        }
    
    def _get_chunk_types_used(self) -> Dict[str, int]:
        """
        Get distribution of chunk types used.
        """
        return self.financial_chunker.get_chunking_stats().get('chunk_types', {})
    
    def _calculate_chunking_efficiency(self) -> str:
        """
        Calculate chunking efficiency.
        """
        stats = self.financial_chunker.get_chunking_stats()
        avg_chunks = stats.get('average_chunks_per_document', 0)
        
        if avg_chunks >= 5:
            return 'high'
        elif avg_chunks >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_duration(self) -> str:
        """
        Calculate chunking duration.
        """
        if not self.chunking_stats.get('started_at') or not self.chunking_stats.get('completed_at'):
            return "unknown"
        
        try:
            start = datetime.fromisoformat(self.chunking_stats['started_at'].replace(' ', 'T'))
            end = datetime.fromisoformat(self.chunking_stats['completed_at'].replace(' ', 'T'))
            duration = end - start
            
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "error"
    
    def _reset_chunking_stats(self):
        """
        Reset chunking statistics.
        """
        self.chunking_stats = {
            'started_at': None,
            'completed_at': None,
            'total_documents': 0,
            'total_chunks': 0,
            'successful_chunkings': 0,
            'failed_chunkings': 0,
            'chunking_results': {},
            'quality_summary': {},
            'errors': []
        }
        self.financial_chunker.reset_stats()
        logger.info("Chunking statistics reset")
    
    def generate_chunking_report(self, output_file: str = None) -> str:
        """
        Generate comprehensive chunking report.
        """
        logger.info("Generating chunking report...")
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'text_chunking_implementation',
                'phase': '1.3.3',
                'version': '1.0'
            },
            'chunking_stats': self.chunking_stats,
            'system_info': {
                'financial_chunker_stats': self.financial_chunker.get_chunking_stats(),
                'config_used': {
                    'primary_chunk_size': self.config.primary_chunk_size,
                    'metric_chunk_size': self.config.metric_chunk_size,
                    'overview_chunk_size': self.config.overview_chunk_size,
                    'performance_chunk_size': self.config.performance_chunk_size,
                    'overlap_tokens': self.config.overlap_tokens,
                    'financial_boundary_patterns_count': len(self.config.financial_boundary_patterns)
                }
            },
            'recommendations': self._generate_recommendations()
        }
        
        report_json = json.dumps(report, indent=2, default=str)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_json)
            logger.info(f"Chunking report saved to {output_file}")
        
        return report_json
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on chunking results.
        """
        recommendations = []
        
        success_rate = (self.chunking_stats['successful_chunkings'] / 
                      self.chunking_stats['total_documents']) * 100 if self.chunking_stats['total_documents'] > 0 else 0
        
        # Success rate recommendations
        if success_rate < 100.0:
            recommendations.append(f"Improve success rate from {success_rate:.1f}% to 100%")
        
        # Chunk size recommendations
        stats = self.financial_chunker.get_chunking_stats()
        avg_chunk_size = stats.get('average_chunk_size', 0)
        if avg_chunk_size < 350 or avg_chunk_size > 500:
            recommendations.append(f"Optimize chunk sizes (current avg: {avg_chunk_size:.1f} tokens)")
        
        # Chunk type distribution recommendations
        chunk_types = stats.get('chunk_types', {})
        if len(chunk_types) < 4:  # Should have primary, metric, overview, performance
            recommendations.append("Ensure all chunk types are created (primary, metric, overview, performance)")
        
        # General recommendations
        recommendations.extend([
            "Monitor chunking performance regularly",
            "Adjust overlap tokens based on retrieval performance",
            "Fine-tune financial boundary patterns",
            "Consider fund category-specific chunking rules",
            "Validate chunk quality against retrieval results"
        ])
        
        return recommendations

# Global implementation instance
text_chunking_impl = TextChunkingImplementation()

if __name__ == "__main__":
    # Test text chunking implementation
    print("🧩 Testing Phase 1.3.3 Text Chunking Implementation")
    print("=" * 60)
    
    try:
        # Initialize system
        if text_chunking_impl.initialize_chunking_system():
            print("✅ System initialization successful")
            
            # Create test cleaned data
            test_cleaned_data = [
                {
                    'fund_data': {
                        'fund_name': 'HDFC Large Cap Fund Direct Growth',
                        'fund_type': 'Direct Growth',
                        'category': 'Large Cap',
                        'riskometer': 'Moderately High',
                        'benchmark': 'Nifty 50 TRI',
                        'expense_ratio': '1.25%',
                        'exit_load': '0%',
                        'min_sip': '₹500',
                        'nav': '₹125.67',
                        'returns': {
                            '1Y': '12.5%',
                            '3Y': '15.2%',
                            '5Y': '14.8%'
                        },
                        'asset_allocation': {
                            'equity': '85.2%',
                            'debt': '10.5%',
                            'cash': '4.3%'
                        },
                        'fund_details': {
                            'description': 'Large cap equity fund focusing on established companies',
                            'aum': '₹15,000 crore'
                        },
                        'source_url': 'https://groww.in/test',
                        'scraped_at': '2024-01-01 12:00:00'
                    },
                    'processing_metadata': {
                        'fund_name': 'HDFC Large Cap Fund Direct Growth',
                        'source_url': 'https://groww.in/test',
                        'processing_status': 'excellent',
                        'processed_at': '2024-01-01 12:30:00'
                    },
                    'quality_metrics': {
                        'overall_quality_score': 85.0
                    }
                }
            ]
            
            # Run chunking
            print("\n🧩 Starting financial chunking...")
            results = text_chunking_impl.chunk_cleaned_data(test_cleaned_data)
            
            # Display results
            print(f"\n📊 Chunking Results:")
            print(f"Success: {results.get('success', False)}")
            print(f"Total Documents: {results.get('chunking_summary', {}).get('total_documents', 0)}")
            print(f"Successful: {results.get('chunking_summary', {}).get('successful_chunkings', 0)}")
            print(f"Success Rate: {results.get('chunking_summary', {}).get('success_rate', 0):.1f}%")
            print(f"Total Chunks: {results.get('chunking_summary', {}).get('total_chunks_created', 0)}")
            
            # Quality summary
            quality_summary = results.get('quality_summary', {})
            print(f"\n🎯 Quality Summary:")
            print(f"Avg Chunk Size: {quality_summary.get('average_chunk_size', 0):.1f}")
            print(f"Chunking Efficiency: {quality_summary.get('chunking_efficiency', 'unknown')}")
            print(f"Quality Status: {quality_summary.get('quality_status', 'unknown')}")
            
            # Show chunk type distribution
            chunk_types = quality_summary.get('chunk_type_distribution', {})
            print(f"\n📋 Chunk Type Distribution:")
            for chunk_type, count in chunk_types.items():
                print(f"  {chunk_type}: {count}")
            
            # Show chunked results
            chunking_results = results.get('chunking_results', [])
            print(f"\n📄 Chunked Results:")
            for i, result in enumerate(chunking_results[:2], 1):  # Show first 2
                fund_name = result.get('chunking_metadata', {}).get('fund_name', 'Unknown')
                chunk_count = result.get('chunking_metadata', {}).get('total_chunks', 0)
                quality_score = result.get('quality_metrics', {}).get('overall_score', 0)
                print(f"  {i}. {fund_name} (Chunks: {chunk_count}, Quality: {quality_score:.1f})")
            
            if len(chunking_results) > 2:
                print(f"  ... and {len(chunking_results) - 2} more documents")
            
            # Errors
            errors = results.get('errors', [])
            if errors:
                print(f"\n❌ Errors:")
                for error in errors[:2]:
                    print(f"  • {error}")
            
            # Generate report
            report_file = f"text_chunking_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            text_chunking_impl.generate_chunking_report(report_file)
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
