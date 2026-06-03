"""
Phase 1.3.2 - Data Cleaning and Preprocessing
Main implementation script integrating all data cleaning components
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from text_cleaner import text_cleaner
from field_extractor import field_extractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCleaningImplementation:
    """
    Main implementation of Phase 1.3.2 Data Cleaning and Preprocessing.
    Integrates text cleaning and field extraction components.
    """
    
    def __init__(self):
        """
        Initialize data cleaning implementation.
        """
        self.text_cleaner = text_cleaner
        self.field_extractor = field_extractor
        
        self.cleaning_stats = {
            'started_at': None,
            'completed_at': None,
            'total_documents': 0,
            'successful_cleanings': 0,
            'failed_cleanings': 0,
            'cleaning_results': {},
            'validation_results': {},
            'errors': []
        }
        
        logger.info("Data cleaning implementation initialized")
    
    def initialize_cleaning_system(self) -> bool:
        """
        Initialize all cleaning components.
        """
        logger.info("Initializing data cleaning system...")
        
        try:
            # Step 1: Initialize text cleaner
            cleaner_stats = self.text_cleaner.get_cleaning_stats()
            logger.info(f"Text cleaner ready: {cleaner_stats['cleaning_rules_count']} rules")
            
            # Step 2: Initialize field extractor
            extractor_stats = self.field_extractor.get_extraction_stats()
            logger.info(f"Field extractor ready: {extractor_stats['supported_fields']} fields")
            
            # Step 3: Reset statistics
            self._reset_cleaning_stats()
            
            logger.info("✅ Data cleaning system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    def clean_scraped_data(self, scraped_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Clean and process scraped data from Phase 1.3.1.
        """
        logger.info(f"Starting data cleaning for {len(scraped_data_list)} documents")
        
        self.cleaning_stats['started_at'] = datetime.now().isoformat()
        self.cleaning_stats['total_documents'] = len(scraped_data_list)
        
        cleaning_results = {
            'implementation_metadata': {
                'phase': '1.3.2',
                'version': '1.0',
                'started_at': self.cleaning_stats['started_at'],
                'input_documents': len(scraped_data_list)
            },
            'cleaning_results': [],
            'validation_summary': {},
            'processing_summary': {},
            'success': False,
            'errors': []
        }
        
        try:
            # Process each scraped document
            for i, scraped_data in enumerate(scraped_data_list):
                logger.info(f"Cleaning document {i+1}/{len(scraped_data_list)}")
                
                try:
                    # Step 1: Extract text content from scraped data
                    text_content = self._extract_text_content(scraped_data)
                    
                    if not text_content:
                        logger.warning(f"⚠️ No text content found in document {i+1}")
                        self.cleaning_stats['failed_cleanings'] += 1
                        continue
                    
                    # Step 2: Clean text content
                    cleaning_result = self.text_cleaner.clean_html_content(
                        text_content.get('soup', text_content),
                        scraped_data.get('source_url', '')
                    )
                    
                    # Step 3: Extract structured fields from cleaned text
                    if cleaning_result.get('cleaned_content'):
                        extraction_result = self.field_extractor.extract_from_text(
                            cleaning_result['cleaned_content'],
                            scraped_data.get('source_url', '')
                        )
                        
                        # Step 4: Combine cleaning and extraction results
                        combined_result = self._combine_cleaning_extraction_results(
                            scraped_data, cleaning_result, extraction_result
                        )
                        
                        # Step 5: Validate combined result
                        validation_result = self.text_cleaner.validate_cleaned_data(combined_result)
                        
                        # Step 6: Create final cleaned data
                        final_result = self._create_final_cleaned_data(
                            scraped_data, combined_result, validation_result
                        )
                        
                        cleaning_results['cleaning_results'].append(final_result)
                        self.cleaning_stats['successful_cleanings'] += 1
                        
                        logger.info(f"✅ Successfully cleaned document {i+1}")
                        logger.info(f"   Cleaning score: {cleaning_result['cleaning_score']:.1f}")
                        logger.info(f"   Extraction confidence: {extraction_result['extraction_confidence']:.1f}")
                        logger.info(f"   Validation score: {validation_result['validation_score']:.1f}")
                    else:
                        logger.error(f"❌ Text cleaning failed for document {i+1}")
                        self.cleaning_stats['failed_cleanings'] += 1
                        cleaning_results['errors'].append({
                            'document_index': i,
                            'error': 'Text cleaning failed',
                            'url': scraped_data.get('source_url', '')
                        })
                        
                except Exception as e:
                    logger.error(f"❌ Error processing document {i+1}: {e}")
                    self.cleaning_stats['failed_cleanings'] += 1
                    cleaning_results['errors'].append({
                        'document_index': i,
                        'error': str(e),
                        'url': scraped_data.get('source_url', '')
                    })
            
            # Calculate summary statistics
            cleaning_results['processing_summary'] = self._calculate_processing_summary()
            cleaning_results['validation_summary'] = self._calculate_validation_summary()
            
            # Determine overall success
            success_rate = (self.cleaning_stats['successful_cleanings'] / 
                          self.cleaning_stats['total_documents']) * 100 if self.cleaning_stats['total_documents'] > 0 else 0
            
            cleaning_results['success'] = (
                success_rate >= 80.0 and  # At least 80% success rate
                len(cleaning_results['errors']) == 0
            )
            
            self.cleaning_stats['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"Data cleaning completed. Success rate: {success_rate:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Critical error in cleaning pipeline: {e}")
            cleaning_results['success'] = False
            cleaning_results['errors'].append({
                'error': str(e),
                'stage': 'pipeline'
            })
        
        return cleaning_results
    
    def _extract_text_content(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract text content from scraped data.
        """
        # Look for HTML content in scraped data
        if 'content' in scraped_data and hasattr(scraped_data['content'], 'get_text'):
            return {
                'type': 'html',
                'soup': scraped_data['content'],
                'text_length': len(scraped_data['content'].get_text())
            }
        elif 'scraping_metadata' in scraped_data:
            # Try to reconstruct from metadata
            return {
                'type': 'metadata',
                'soup': None,
                'text_length': len(str(scraped_data.get('fund_name', '')))
            }
        else:
            return {
                'type': 'unknown',
                'soup': None,
                'text_length': 0
            }
    
    def _combine_cleaning_extraction_results(self, scraped_data: Dict[str, Any], 
                                       cleaning_result: Dict[str, Any], 
                                       extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine cleaning and extraction results.
        """
        combined_result = {
            'source_data': scraped_data,
            'cleaning_result': cleaning_result,
            'extraction_result': extraction_result,
            'combined_confidence': 0.0,
            'data_quality_score': 0.0,
            'processing_status': 'completed'
        }
        
        try:
            # Calculate combined confidence score
            cleaning_score = cleaning_result.get('cleaning_score', 0)
            extraction_confidence = extraction_result.get('extraction_confidence', 0)
            
            # Weighted combination (cleaning 40%, extraction 60%)
            combined_result['combined_confidence'] = (cleaning_score * 0.4) + (extraction_confidence * 0.6)
            
            # Calculate overall data quality score
            validation_score = extraction_result.get('validation_result', {}).get('validation_score', 0)
            combined_result['data_quality_score'] = (cleaning_score * 0.3) + (validation_score * 0.4) + (extraction_confidence * 0.3)
            
            # Determine processing status
            if cleaning_score >= 80.0 and extraction_confidence >= 80.0 and validation_score >= 80.0:
                combined_result['processing_status'] = 'excellent'
            elif combined_result['combined_confidence'] >= 70.0:
                combined_result['processing_status'] = 'good'
            elif combined_result['combined_confidence'] >= 50.0:
                combined_result['processing_status'] = 'acceptable'
            else:
                combined_result['processing_status'] = 'needs_improvement'
            
        except Exception as e:
            logger.error(f"Error combining results: {e}")
            combined_result['processing_status'] = 'error'
        
        return combined_result
    
    def _create_final_cleaned_data(self, scraped_data: Dict[str, Any], 
                                   combined_result: Dict[str, Any], 
                                   validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create final cleaned data structure.
        """
        final_data = {
            # Original scraped data
            'original_data': scraped_data,
            
            # Cleaning results
            'cleaning_metadata': {
                'cleaning_confidence': combined_result.get('combined_confidence', 0),
                'processing_status': combined_result.get('processing_status', 'unknown'),
                'cleaning_actions': combined_result.get('cleaning_result', {}).get('cleaning_actions', [])
            },
            
            # Extracted and cleaned fields
            'fund_data': combined_result.get('extraction_result', {}).get('extracted_fields', {}),
            
            # Validation results
            'validation_result': validation_result,
            
            # Quality metrics
            'quality_metrics': {
                'text_quality_score': combined_result.get('cleaning_result', {}).get('cleaning_score', 0),
                'extraction_confidence': combined_result.get('extraction_result', {}).get('extraction_confidence', 0),
                'overall_quality_score': combined_result.get('data_quality_score', 0),
                'data_completeness': self._calculate_data_completeness(combined_result.get('extraction_result', {}).get('extracted_fields', {}))
            },
            
            # Processing metadata
            'processing_metadata': {
                'processed_at': datetime.now().isoformat(),
                'processing_phase': '1.3.2',
                'source_url': scraped_data.get('source_url', ''),
                'fund_name': combined_result.get('extraction_result', {}).get('extracted_fields', {}).get('fund_name', 'Unknown')
            }
        }
        
        return final_data
    
    def _calculate_data_completeness(self, extracted_fields: Dict[str, Any]) -> float:
        """
        Calculate data completeness percentage.
        """
        critical_fields = ['fund_name', 'source_url']
        important_fields = ['expense_ratio', 'exit_load', 'min_sip', 'nav']
        optional_fields = ['returns', 'riskometer', 'benchmark', 'asset_allocation']
        
        total_fields = len(critical_fields) + len(important_fields) + len(optional_fields)
        present_fields = 0
        
        # Count present fields
        for field in critical_fields + important_fields + optional_fields:
            if field in extracted_fields and extracted_fields[field] != "Not available":
                present_fields += 1
        
        # Weighted completeness (critical fields worth more)
        weighted_score = 0.0
        for field in critical_fields:
            if field in extracted_fields and extracted_fields[field] != "Not available":
                weighted_score += 30  # 30% per critical field
        
        for field in important_fields:
            if field in extracted_fields and extracted_fields[field] != "Not available":
                weighted_score += 15  # 15% per important field
        
        for field in optional_fields:
            if field in extracted_fields and extracted_fields[field] != "Not available":
                weighted_score += 5   # 5% per optional field
        
        return min(100.0, weighted_score)
    
    def _calculate_processing_summary(self) -> Dict[str, Any]:
        """
        Calculate processing summary statistics.
        """
        total = self.cleaning_stats['total_documents']
        successful = self.cleaning_stats['successful_cleanings']
        failed = self.cleaning_stats['failed_cleanings']
        
        return {
            'total_documents': total,
            'successful_cleanings': successful,
            'failed_cleanings': failed,
            'success_rate': (successful / total) * 100 if total > 0 else 0,
            'processing_duration': self._calculate_duration(),
            'average_quality_score': self._calculate_average_quality_score()
        }
    
    def _calculate_validation_summary(self) -> Dict[str, Any]:
        """
        Calculate validation summary from all results.
        """
        validation_results = self.cleaning_stats.get('validation_results', {})
        
        if not validation_results:
            return {'status': 'no_data', 'message': 'No validation results available'}
        
        total_validations = len(validation_results)
        passed_validations = len([
            v for v in validation_results.values() 
            if isinstance(v, dict) and v.get('overall_status') == 'passed'
        ])
        
        validation_scores = [
            v.get('validation_score', 0) for v in validation_results.values() 
            if isinstance(v, dict)
        ]
        avg_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0
        
        return {
            'total_validations': total_validations,
            'passed_validations': passed_validations,
            'failed_validations': total_validations - passed_validations,
            'average_validation_score': round(avg_score, 1),
            'validation_success_rate': (passed_validations / total_validations) * 100 if total_validations > 0 else 0,
            'validation_status': 'excellent' if avg_score >= 90.0 else 'good' if avg_score >= 80.0 else 'needs_improvement'
        }
    
    def _calculate_average_quality_score(self) -> float:
        """
        Calculate average quality score from all results.
        """
        quality_scores = []
        
        for result in self.cleaning_stats.get('cleaning_results', []):
            if isinstance(result, dict):
                quality_score = result.get('quality_metrics', {}).get('overall_quality_score', 0)
                if quality_score > 0:
                    quality_scores.append(quality_score)
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_duration(self) -> str:
        """
        Calculate processing duration.
        """
        if not self.cleaning_stats.get('started_at') or not self.cleaning_stats.get('completed_at'):
            return "unknown"
        
        try:
            start = datetime.fromisoformat(self.cleaning_stats['started_at'].replace(' ', 'T'))
            end = datetime.fromisoformat(self.cleaning_stats['completed_at'].replace(' ', 'T'))
            duration = end - start
            
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "error"
    
    def _reset_cleaning_stats(self):
        """
        Reset cleaning statistics.
        """
        self.cleaning_stats = {
            'started_at': None,
            'completed_at': None,
            'total_documents': 0,
            'successful_cleanings': 0,
            'failed_cleanings': 0,
            'cleaning_results': {},
            'validation_results': {},
            'errors': []
        }
        logger.info("Cleaning statistics reset")
    
    def generate_cleaning_report(self, output_file: str = None) -> str:
        """
        Generate comprehensive cleaning report.
        """
        logger.info("Generating cleaning report...")
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'data_cleaning_implementation',
                'phase': '1.3.2',
                'version': '1.0'
            },
            'cleaning_stats': self.cleaning_stats,
            'system_info': {
                'text_cleaner_config': self.text_cleaner.get_cleaning_stats(),
                'field_extractor_config': self.field_extractor.get_extraction_stats()
            },
            'recommendations': self._generate_recommendations()
        }
        
        report_json = json.dumps(report, indent=2, default=str)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_json)
            logger.info(f"Cleaning report saved to {output_file}")
        
        return report_json
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on cleaning results.
        """
        recommendations = []
        
        success_rate = (self.cleaning_stats['successful_cleanings'] / 
                      self.cleaning_stats['total_documents']) * 100 if self.cleaning_stats['total_documents'] > 0 else 0
        
        # Success rate recommendations
        if success_rate < 100.0:
            recommendations.append(f"Improve success rate from {success_rate:.1f}% to 100%")
        
        # Quality score recommendations
        avg_quality_score = self._calculate_average_quality_score()
        if avg_quality_score < 85.0:
            recommendations.append(f"Improve average quality score from {avg_quality_score:.1f}% to 85%+")
        
        # Error-based recommendations
        if self.cleaning_stats['errors']:
            error_types = set()
            for error in self.cleaning_stats['errors']:
                if isinstance(error, dict) and 'stage' in error:
                    error_types.add(error['stage'])
            
            for error_type in error_types:
                recommendations.append(f"Fix errors in {error_type} stage")
        
        # General recommendations
        recommendations.extend([
            "Monitor cleaning performance regularly",
            "Update extraction patterns if website structure changes",
            "Implement better error handling for edge cases",
            "Add more robust validation rules",
            "Consider machine learning for field extraction"
        ])
        
        return recommendations

# Global implementation instance
data_cleaning_impl = DataCleaningImplementation()

if __name__ == "__main__":
    # Test data cleaning implementation
    print("🧹 Testing Phase 1.3.2 Data Cleaning Implementation")
    print("=" * 60)
    
    try:
        # Initialize system
        if data_cleaning_impl.initialize_cleaning_system():
            print("✅ System initialization successful")
            
            # Create test scraped data
            test_scraped_data = [
                {
                    'fund_name': 'HDFC Large Cap Fund Direct Growth',
                    'source_url': 'https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth',
                    'content': '<html><body><h1>HDFC Large Cap Fund</h1></body></html>',
                    'scraped_at': '2024-01-01 12:00:00'
                }
            ]
            
            # Run cleaning
            print("\n🧹 Starting data cleaning...")
            results = data_cleaning_impl.clean_scraped_data(test_scraped_data)
            
            # Display results
            print(f"\n📊 Cleaning Results:")
            print(f"Success: {results.get('success', False)}")
            print(f"Total Documents: {results.get('processing_summary', {}).get('total_documents', 0)}")
            print(f"Successful: {results.get('processing_summary', {}).get('successful_cleanings', 0)}")
            print(f"Success Rate: {results.get('processing_summary', {}).get('success_rate', 0):.1f}%")
            
            # Validation summary
            validation_summary = results.get('validation_summary', {})
            print(f"\n🔍 Validation Summary:")
            print(f"Avg Score: {validation_summary.get('average_validation_score', 0):.1f}")
            print(f"Validation Success Rate: {validation_summary.get('validation_success_rate', 0):.1f}%")
            print(f"Validation Status: {validation_summary.get('validation_status', 'unknown')}")
            
            # Show cleaned results
            cleaning_results = results.get('cleaning_results', [])
            print(f"\n📋 Cleaned Results:")
            for i, result in enumerate(cleaning_results[:3], 1):  # Show first 3
                fund_name = result.get('processing_metadata', {}).get('fund_name', 'Unknown')
                quality_score = result.get('quality_metrics', {}).get('overall_quality_score', 0)
                print(f"  {i}. {fund_name} (Quality: {quality_score:.1f})")
            
            if len(cleaning_results) > 3:
                print(f"  ... and {len(cleaning_results) - 3} more documents")
            
            # Errors
            errors = results.get('errors', [])
            if errors:
                print(f"\n❌ Errors:")
                for error in errors[:2]:
                    print(f"  • {error}")
            
            # Generate report
            report_file = f"data_cleaning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            data_cleaning_impl.generate_cleaning_report(report_file)
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
