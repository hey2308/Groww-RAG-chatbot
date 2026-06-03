"""
Phase 1.3.3 - Text Chunking Strategy
Financial Data-Specific Chunker for Mutual Fund Information
"""

import logging
import re
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChunkConfig:
    """
    Configuration for financial data chunking.
    """
    primary_chunk_size: int = 500  # 400-600 tokens for main info
    metric_chunk_size: int = 250  # 200-300 tokens for data tables
    overview_chunk_size: int = 350  # 300-400 tokens for descriptions
    performance_chunk_size: int = 300  # 250-350 tokens for performance data
    overlap_tokens: int = 135  # 120-150 tokens for financial context
    min_chunk_size: int = 100
    max_chunk_size: int = 600
    financial_boundary_patterns: List[str] = None
    
    def __post_init__(self):
        if self.financial_boundary_patterns is None:
            self.financial_boundary_patterns = [
                r'\n\s*\n',  # Double newlines
                r'\.\s+',  # Sentence endings
                r'[:]\s*',  # Colons (common in financial data)
                r'[;]\s*',  # Semicolons
                r'[-]\s*',  # Dashes
                r'\t+',  # Tabs (table separators)
                r'Risk\s+Level',  # Risk sections
                r'Asset\s+Allocation',  # Allocation sections
                r'Performance\s+Analysis',  # Performance sections
                r'Investment\s+Objective',  # Objective sections
                r'Fund\s+Details'  # Details sections
            ]

class FinancialDataChunker:
    """
    Specialized chunker for mutual fund financial data.
    Implements financial-aware chunking with multiple chunk types.
    """
    
    def __init__(self, config: ChunkConfig = None):
        """
        Initialize financial data chunker.
        """
        self.config = config or ChunkConfig()
        self.chunking_stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'chunk_types': {},
            'average_chunk_size': 0.0,
            'financial_boundaries_found': 0
        }
        
        logger.info("Financial data chunker initialized")
        logger.info(f"Config: primary={self.config.primary_chunk_size}, overlap={self.config.overlap_tokens}")
    
    def chunk_fund_data(self, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chunk fund data using financial-aware strategy.
        """
        logger.info(f"Chunking fund data: {fund_data.get('fund_name', 'Unknown')}")
        
        chunking_result = {
            'fund_name': fund_data.get('fund_name', 'Unknown'),
            'chunking_timestamp': datetime.now().isoformat(),
            'original_data_size': self._calculate_data_size(fund_data),
            'chunks': [],
            'chunking_metadata': {
                'strategy': 'financial_aware',
                'config_used': {
                    'primary_size': self.config.primary_chunk_size,
                    'overlap': self.config.overlap_tokens,
                    'financial_boundaries': len(self.config.financial_boundary_patterns)
                }
            },
            'quality_metrics': {},
            'chunking_success': False
        }
        
        try:
            # Step 1: Classify and organize fund data
            classified_data = self._classify_fund_data(fund_data)
            
            # Step 2: Create specialized chunks
            chunks = []
            
            # Primary chunk with basic fund information
            primary_chunk = self._create_primary_chunk(classified_data)
            if primary_chunk:
                chunks.append(primary_chunk)
            
            # Metric chunks for structured data
            metric_chunks = self._create_metric_chunks(classified_data)
            chunks.extend(metric_chunks)
            
            # Overview chunk for descriptions
            overview_chunk = self._create_overview_chunk(classified_data)
            if overview_chunk:
                chunks.append(overview_chunk)
            
            # Performance chunks for historical data
            performance_chunks = self._create_performance_chunks(classified_data)
            chunks.extend(performance_chunks)
            
            # Step 3: Add overlap and finalize chunks
            final_chunks = self._add_overlap_to_chunks(chunks)
            
            # Step 4: Enrich chunks with metadata
            enriched_chunks = self._enrich_chunks_with_metadata(final_chunks, fund_data)
            
            chunking_result['chunks'] = enriched_chunks
            chunking_result['chunking_success'] = True
            
            # Step 5: Calculate quality metrics
            chunking_result['quality_metrics'] = self._calculate_chunking_quality_metrics(
                enriched_chunks, fund_data
            )
            
            # Update statistics
            self._update_chunking_stats(chunking_result)
            
            logger.info(f"Successfully created {len(enriched_chunks)} chunks")
            logger.info(f"Average chunk size: {chunking_result['quality_metrics']['average_chunk_size']:.1f} tokens")
            
        except Exception as e:
            logger.error(f"Error chunking fund data: {e}")
            chunking_result['chunking_success'] = False
            chunking_result['error'] = str(e)
        
        return chunking_result
    
    def _classify_fund_data(self, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify fund data into different categories for specialized chunking.
        """
        classified = {
            'primary_info': {},
            'metric_data': {},
            'overview_data': {},
            'performance_data': {},
            'financial_tables': {}
        }
        
        # Primary information (basic fund details)
        primary_fields = ['fund_name', 'fund_type', 'category', 'riskometer', 'benchmark']
        for field in primary_fields:
            if field in fund_data and fund_data[field] != "Not available":
                classified['primary_info'][field] = fund_data[field]
        
        # Metric data (structured numerical data)
        metric_fields = ['expense_ratio', 'exit_load', 'min_sip', 'nav']
        for field in metric_fields:
            if field in fund_data and fund_data[field] != "Not available":
                classified['metric_data'][field] = fund_data[field]
        
        # Asset allocation (table data)
        if 'asset_allocation' in fund_data and fund_data['asset_allocation']:
            classified['financial_tables']['asset_allocation'] = fund_data['asset_allocation']
        
        # Returns data (performance table)
        if 'returns' in fund_data and fund_data['returns']:
            classified['financial_tables']['returns'] = fund_data['returns']
        
        # Overview data (descriptive information)
        if 'fund_details' in fund_data and fund_data['fund_details']:
            classified['overview_data'] = fund_data['fund_details']
        
        # Performance data (historical)
        # This would typically come from time-series data
        classified['performance_data'] = {
            'historical_performance': 'Not available',  # Would be populated with actual data
            'benchmark_comparison': 'Not available'
        }
        
        return classified
    
    def _create_primary_chunk(self, classified_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create primary chunk with main fund information.
        """
        primary_info = classified_data.get('primary_info', {})
        
        if not primary_info:
            return None
        
        # Build chunk content
        chunk_content = []
        chunk_content.append("Fund Overview:")
        
        if 'fund_name' in primary_info:
            chunk_content.append(f"Fund Name: {primary_info['fund_name']}")
        
        if 'fund_type' in primary_info:
            chunk_content.append(f"Fund Type: {primary_info['fund_type']}")
        
        if 'category' in primary_info:
            chunk_content.append(f"Category: {primary_info['category']}")
        
        if 'riskometer' in primary_info:
            chunk_content.append(f"Risk Level: {primary_info['riskometer']}")
        
        if 'benchmark' in primary_info:
            chunk_content.append(f"Benchmark: {primary_info['benchmark']}")
        
        chunk_text = "\n".join(chunk_content)
        
        # Apply financial boundary splitting if too long
        if self._estimate_token_count(chunk_text) > self.config.primary_chunk_size:
            chunk_text = self._split_at_financial_boundaries(
                chunk_text, self.config.primary_chunk_size
            )
        
        return {
            'chunk_id': 'primary_001',
            'chunk_type': 'primary',
            'content': chunk_text,
            'token_count': self._estimate_token_count(chunk_text),
            'source_fields': list(primary_info.keys()),
            'priority': 'high'
        }
    
    def _create_metric_chunks(self, classified_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create metric chunks for structured financial data.
        """
        metric_chunks = []
        metric_data = classified_data.get('metric_data', {})
        financial_tables = classified_data.get('financial_tables', {})
        
        # Create expense and load chunk
        expense_load_data = {}
        if 'expense_ratio' in metric_data:
            expense_load_data['expense_ratio'] = metric_data['expense_ratio']
        if 'exit_load' in metric_data:
            expense_load_data['exit_load'] = metric_data['exit_load']
        
        if expense_load_data:
            chunk_content = ["Cost Information:"]
            if 'expense_ratio' in expense_load_data:
                chunk_content.append(f"Expense Ratio: {expense_load_data['expense_ratio']}")
            if 'exit_load' in expense_load_data:
                chunk_content.append(f"Exit Load: {expense_load_data['exit_load']}")
            
            metric_chunks.append({
                'chunk_id': 'metric_001',
                'chunk_type': 'metric',
                'content': "\n".join(chunk_content),
                'token_count': self._estimate_token_count("\n".join(chunk_content)),
                'source_fields': list(expense_load_data.keys()),
                'priority': 'high'
            })
        
        # Create investment information chunk
        investment_data = {}
        if 'min_sip' in metric_data:
            investment_data['min_sip'] = metric_data['min_sip']
        if 'nav' in metric_data:
            investment_data['nav'] = metric_data['nav']
        
        if investment_data:
            chunk_content = ["Investment Information:"]
            if 'min_sip' in investment_data:
                chunk_content.append(f"Minimum SIP: {investment_data['min_sip']}")
            if 'nav' in investment_data:
                chunk_content.append(f"Current NAV: {investment_data['nav']}")
            
            metric_chunks.append({
                'chunk_id': 'metric_002',
                'chunk_type': 'metric',
                'content': "\n".join(chunk_content),
                'token_count': self._estimate_token_count("\n".join(chunk_content)),
                'source_fields': list(investment_data.keys()),
                'priority': 'high'
            })
        
        # Create financial table chunks
        if 'returns' in financial_tables:
            returns_data = financial_tables['returns']
            chunk_content = ["Performance Returns:"]
            
            for period, value in returns_data.items():
                if value != "Not available":
                    chunk_content.append(f"{period} Return: {value}")
            
            metric_chunks.append({
                'chunk_id': 'metric_003',
                'chunk_type': 'metric',
                'content': "\n".join(chunk_content),
                'token_count': self._estimate_token_count("\n".join(chunk_content)),
                'source_fields': ['returns'],
                'priority': 'high'
            })
        
        if 'asset_allocation' in financial_tables:
            allocation_data = financial_tables['asset_allocation']
            chunk_content = ["Asset Allocation:"]
            
            for asset_type, value in allocation_data.items():
                if value != "Not available":
                    chunk_content.append(f"{asset_type.title()}: {value}")
            
            metric_chunks.append({
                'chunk_id': 'metric_004',
                'chunk_type': 'metric',
                'content': "\n".join(chunk_content),
                'token_count': self._estimate_token_count("\n".join(chunk_content)),
                'source_fields': ['asset_allocation'],
                'priority': 'high'
            })
        
        return metric_chunks
    
    def _create_overview_chunk(self, classified_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create overview chunk with fund descriptions and objectives.
        """
        overview_data = classified_data.get('overview_data', {})
        
        if not overview_data:
            return None
        
        chunk_content = ["Fund Details and Objectives:"]
        
        for key, value in overview_data.items():
            if value != "Not available":
                # Format key for better readability
                formatted_key = key.replace('_', ' ').title()
                chunk_content.append(f"{formatted_key}: {value}")
        
        chunk_text = "\n".join(chunk_content)
        
        return {
            'chunk_id': 'overview_001',
            'chunk_type': 'overview',
            'content': chunk_text,
            'token_count': self._estimate_token_count(chunk_text),
            'source_fields': list(overview_data.keys()),
            'priority': 'medium'
        }
    
    def _create_performance_chunks(self, classified_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create performance chunks for historical data.
        """
        performance_chunks = []
        performance_data = classified_data.get('performance_data', {})
        
        # Historical performance chunk
        if 'historical_performance' in performance_data:
            chunk_content = ["Historical Performance Analysis:"]
            chunk_content.append(str(performance_data['historical_performance']))
            
            performance_chunks.append({
                'chunk_id': 'performance_001',
                'chunk_type': 'performance',
                'content': "\n".join(chunk_content),
                'token_count': self._estimate_token_count("\n".join(chunk_content)),
                'source_fields': ['historical_performance'],
                'priority': 'medium'
            })
        
        # Benchmark comparison chunk
        if 'benchmark_comparison' in performance_data:
            chunk_content = ["Benchmark Comparison:"]
            chunk_content.append(str(performance_data['benchmark_comparison']))
            
            performance_chunks.append({
                'chunk_id': 'performance_002',
                'chunk_type': 'performance',
                'content': "\n".join(chunk_content),
                'token_count': self._estimate_token_count("\n".join(chunk_content)),
                'source_fields': ['benchmark_comparison'],
                'priority': 'medium'
            })
        
        return performance_chunks
    
    def _add_overlap_to_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add overlap between chunks for context preservation.
        """
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            chunk_content = chunk['content']
            
            # Add overlap from previous chunk (except for first chunk)
            if i > 0:
                previous_chunk = chunks[i - 1]
                overlap_text = self._extract_overlap_text(
                    previous_chunk['content'], self.config.overlap_tokens
                )
                if overlap_text:
                    chunk_content = f"Context: {overlap_text}\n\n{chunk_content}"
            
            # Add preview of next chunk (except for last chunk)
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                preview_text = self._extract_overlap_text(
                    next_chunk['content'], self.config.overlap_tokens // 2
                )
                if preview_text:
                    chunk_content = f"{chunk_content}\n\nRelated: {preview_text}"
            
            overlapped_chunk = chunk.copy()
            overlapped_chunk['content'] = chunk_content
            overlapped_chunk['token_count'] = self._estimate_token_count(chunk_content)
            overlapped_chunk['has_overlap'] = True
            
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def _extract_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """
        Extract overlap text from beginning of chunk.
        """
        if not text or overlap_tokens <= 0:
            return ""
        
        # Simple approximation: split by words and take first N words
        words = text.split()
        if len(words) <= overlap_tokens:
            return text
        
        # Take first overlap_tokens words
        overlap_words = words[:overlap_tokens]
        return " ".join(overlap_words)
    
    def _enrich_chunks_with_metadata(self, chunks: List[Dict[str, Any]], fund_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Enrich chunks with financial metadata.
        """
        enriched_chunks = []
        
        for chunk in chunks:
            enriched_chunk = chunk.copy()
            
            # Add fund metadata
            enriched_chunk['fund_metadata'] = {
                'fund_name': fund_data.get('fund_name', 'Unknown'),
                'fund_type': fund_data.get('fund_type', 'Not available'),
                'category': fund_data.get('category', 'Not available'),
                'risk_level': fund_data.get('riskometer', 'Not available'),
                'aum_size': fund_data.get('fund_details', {}).get('aum', 'Not available')
            }
            
            # Add chunking metadata
            enriched_chunk['chunking_metadata'] = {
                'chunk_id': chunk['chunk_id'],
                'chunk_type': chunk['chunk_type'],
                'priority': chunk['priority'],
                'created_at': datetime.now().isoformat(),
                'overlap_applied': chunk.get('has_overlap', False)
            }
            
            # Add quality metadata
            enriched_chunk['quality_metadata'] = {
                'token_count': chunk['token_count'],
                'source_field_count': len(chunk.get('source_fields', [])),
                'completeness_score': self._calculate_chunk_completeness(chunk),
                'relevance_score': self._calculate_chunk_relevance(chunk)
            }
            
            # Add source metadata
            enriched_chunk['source_metadata'] = {
                'source_url': fund_data.get('source_url', ''),
                'extraction_timestamp': fund_data.get('scraped_at', ''),
                'data_freshness': self._assess_data_freshness(fund_data.get('scraped_at', ''))
            }
            
            enriched_chunks.append(enriched_chunk)
        
        return enriched_chunks
    
    def _calculate_chunk_completeness(self, chunk: Dict[str, Any]) -> float:
        """
        Calculate completeness score for a chunk.
        """
        source_fields = chunk.get('source_fields', [])
        chunk_type = chunk.get('chunk_type', 'unknown')
        
        # Expected fields for different chunk types
        expected_fields = {
            'primary': ['fund_name', 'fund_type', 'category'],
            'metric': ['expense_ratio', 'nav', 'returns'],
            'overview': ['description', 'objectives'],
            'performance': ['historical_performance', 'benchmark']
        }
        
        expected = expected_fields.get(chunk_type, [])
        if not expected:
            return 50.0  # Default score for unknown types
        
        # Calculate completeness based on expected fields
        present_fields = len([field for field in expected if any(field in sf for sf in source_fields)])
        completeness = (present_fields / len(expected)) * 100
        
        return min(100.0, completeness)
    
    def _calculate_chunk_relevance(self, chunk: Dict[str, Any]) -> float:
        """
        Calculate relevance score for a chunk.
        """
        chunk_type = chunk.get('chunk_type', 'unknown')
        priority = chunk.get('priority', 'low')
        
        # Base relevance by chunk type
        type_relevance = {
            'primary': 90.0,
            'metric': 85.0,
            'overview': 75.0,
            'performance': 80.0
        }
        
        base_score = type_relevance.get(chunk_type, 50.0)
        
        # Adjust by priority
        priority_multiplier = {
            'high': 1.0,
            'medium': 0.8,
            'low': 0.6
        }
        
        return base_score * priority_multiplier.get(priority, 0.5)
    
    def _assess_data_freshness(self, scraped_at: str) -> str:
        """
        Assess freshness of scraped data.
        """
        try:
            if not scraped_at:
                return "unknown"
            
            # Parse timestamp
            if 'T' in scraped_at:
                scraped_date = datetime.fromisoformat(scraped_at.replace(' ', 'T'))
            else:
                scraped_date = datetime.strptime(scraped_at, '%Y-%m-%d %H:%M:%S')
            
            # Calculate age
            age_days = (datetime.now() - scraped_date).days
            
            if age_days <= 1:
                return "fresh"
            elif age_days <= 7:
                return "recent"
            elif age_days <= 30:
                return "acceptable"
            else:
                return "stale"
                
        except:
            return "unknown"
    
    def _split_at_financial_boundaries(self, text: str, max_tokens: int) -> str:
        """
        Split text at financial boundaries if too long.
        """
        if self._estimate_token_count(text) <= max_tokens:
            return text
        
        # Try to split at financial boundaries
        for pattern in self.config.financial_boundary_patterns:
            if re.search(pattern, text):
                # Split at first boundary that keeps chunks under limit
                parts = re.split(pattern, text, maxsplit=1)
                if len(parts) > 1:
                    first_part = parts[0]
                    if self._estimate_token_count(first_part) <= max_tokens:
                        return first_part
        
        # Fallback: split at word boundary
        words = text.split()
        current_chunk = []
        current_tokens = 0
        
        for word in words:
            word_tokens = 1  # Approximate
            if current_tokens + word_tokens > max_tokens:
                break
            current_chunk.append(word)
            current_tokens += word_tokens
        
        return " ".join(current_chunk)
    
    def _estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        """
        if not text:
            return 0
        
        # Simple approximation: ~4 characters per token for English
        return max(1, len(text) // 4)
    
    def _calculate_data_size(self, fund_data: Dict[str, Any]) -> int:
        """
        Calculate total size of fund data.
        """
        total_size = 0
        
        for key, value in fund_data.items():
            if isinstance(value, str):
                total_size += self._estimate_token_count(value)
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        total_size += self._estimate_token_count(sub_value)
        
        return total_size
    
    def _calculate_chunking_quality_metrics(self, chunks: List[Dict[str, Any]], fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quality metrics for chunking results.
        """
        if not chunks:
            return {'overall_score': 0.0, 'error': 'No chunks created'}
        
        # Basic metrics
        total_chunks = len(chunks)
        total_tokens = sum(chunk.get('token_count', 0) for chunk in chunks)
        avg_chunk_size = total_tokens / total_chunks if total_chunks > 0 else 0
        
        # Chunk type distribution
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk.get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        # Quality scores
        completeness_scores = [
            chunk.get('quality_metadata', {}).get('completeness_score', 0) for chunk in chunks
        ]
        relevance_scores = [
            chunk.get('quality_metadata', {}).get('relevance_score', 0) for chunk in chunks
        ]
        
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        
        # Overall quality score
        overall_score = (avg_completeness * 0.4) + (avg_relevance * 0.3) + (100 - abs(avg_chunk_size - 400)) * 0.3
        
        return {
            'total_chunks': total_chunks,
            'total_tokens': total_tokens,
            'average_chunk_size': round(avg_chunk_size, 1),
            'chunk_type_distribution': chunk_types,
            'average_completeness': round(avg_completeness, 1),
            'average_relevance': round(avg_relevance, 1),
            'overall_score': round(min(100.0, overall_score), 1),
            'target_chunk_sizes': {
                'primary': self.config.primary_chunk_size,
                'metric': self.config.metric_chunk_size,
                'overview': self.config.overview_chunk_size,
                'performance': self.config.performance_chunk_size
            }
        }
    
    def _update_chunking_stats(self, chunking_result: Dict[str, Any]):
        """
        Update chunking statistics.
        """
        self.chunking_stats['total_documents'] += 1
        
        chunks = chunking_result.get('chunks', [])
        self.chunking_stats['total_chunks'] += len(chunks)
        
        # Update chunk type counts
        for chunk in chunks:
            chunk_type = chunk.get('chunk_type', 'unknown')
            self.chunking_stats['chunk_types'][chunk_type] = \
                self.chunking_stats['chunk_types'].get(chunk_type, 0) + 1
        
        # Update average chunk size
        if chunks:
            total_tokens = sum(chunk.get('token_count', 0) for chunk in chunks)
            current_avg = total_tokens / len(chunks)
            
            # Update running average
            if self.chunking_stats['average_chunk_size'] == 0:
                self.chunking_stats['average_chunk_size'] = current_avg
            else:
                self.chunking_stats['average_chunk_size'] = (
                    self.chunking_stats['average_chunk_size'] + current_avg
                ) / 2
    
    def get_chunking_stats(self) -> Dict[str, Any]:
        """
        Get chunking statistics.
        """
        stats = self.chunking_stats.copy()
        
        # Calculate additional metrics
        if stats['total_documents'] > 0:
            stats['average_chunks_per_document'] = \
                stats['total_chunks'] / stats['total_documents']
        else:
            stats['average_chunks_per_document'] = 0
        
        stats['chunker_version'] = '1.0'
        stats['config_summary'] = {
            'primary_chunk_size': self.config.primary_chunk_size,
            'overlap_tokens': self.config.overlap_tokens,
            'financial_boundaries_count': len(self.config.financial_boundary_patterns)
        }
        
        return stats
    
    def reset_stats(self):
        """
        Reset chunking statistics.
        """
        self.chunking_stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'chunk_types': {},
            'average_chunk_size': 0.0,
            'financial_boundaries_found': 0
        }
        logger.info("Chunking statistics reset")

# Global chunker instance
financial_chunker = FinancialDataChunker()

if __name__ == "__main__":
    # Test financial chunker
    print("🧩 Testing Financial Data Chunker")
    print("=" * 50)
    
    # Test fund data
    test_fund_data = {
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
    }
    
    # Test chunking
    result = financial_chunker.chunk_fund_data(test_fund_data)
    
    print(f"Chunking Result:")
    print(f"Success: {result['chunking_success']}")
    print(f"Total Chunks: {len(result['chunks'])}")
    print(f"Original Data Size: {result['original_data_size']} tokens")
    
    # Show chunks
    print(f"\nChunks Created:")
    for i, chunk in enumerate(result['chunks'], 1):
        chunk_type = chunk.get('chunk_type', 'unknown')
        token_count = chunk.get('token_count', 0)
        priority = chunk.get('priority', 'low')
        print(f"  {i}. {chunk_type.upper()} (Tokens: {token_count}, Priority: {priority})")
        print(f"     Content: {chunk['content'][:100]}...")
        print(f"     Fields: {chunk.get('source_fields', [])}")
    
    # Show quality metrics
    quality_metrics = result.get('quality_metrics', {})
    print(f"\nQuality Metrics:")
    print(f"Overall Score: {quality_metrics.get('overall_score', 0):.1f}")
    print(f"Average Chunk Size: {quality_metrics.get('average_chunk_size', 0):.1f}")
    print(f"Average Completeness: {quality_metrics.get('average_completeness', 0):.1f}")
    print(f"Average Relevance: {quality_metrics.get('average_relevance', 0):.1f}")
    
    # Show chunk type distribution
    chunk_types = quality_metrics.get('chunk_type_distribution', {})
    print(f"\nChunk Type Distribution:")
    for chunk_type, count in chunk_types.items():
        print(f"  {chunk_type}: {count}")
    
    # Show stats
    stats = financial_chunker.get_chunking_stats()
    print(f"\nChunker Stats:")
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Total Chunks: {stats['total_chunks']}")
    print(f"Average Chunks per Document: {stats['average_chunks_per_document']:.1f}")
    print(f"Average Chunk Size: {stats['average_chunk_size']:.1f}")
    
    print("\n✅ Financial chunker testing completed")
