"""
Phase 1.3.1 - Web Scraping Implementation
Main implementation script integrating all web scraping components
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from scraper_initializer import enhanced_scraper, ScraperConfig
from html_parser import groww_parser
from data_validator import scraped_data_validator
from config.settings import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebScrapingImplementation:
    """
    Main implementation of Phase 1.3.1 Web Scraping.
    Integrates scraper initializer, HTML parser, and data validator.
    """
    
    def __init__(self):
        """
        Initialize web scraping implementation.
        """
        self.scraper = enhanced_scraper
        self.parser = groww_parser
        self.validator = scraped_data_validator
        
        self.scraping_stats = {
            'started_at': None,
            'completed_at': None,
            'total_urls': len(settings.fund_urls),
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'total_documents': 0,
            'validation_results': {},
            'errors': []
        }
        
        logger.info("Web scraping implementation initialized")
        logger.info(f"Configured URLs: {len(settings.fund_urls)}")
    
    def initialize_scraping_system(self) -> bool:
        """
        Initialize all scraping components.
        """
        logger.info("Initializing web scraping system...")
        
        try:
            # Step 1: Initialize scraper
            if not self.scraper.initialize_scraper():
                logger.error("❌ Scraper initialization failed")
                return False
            
            # Step 2: Setup Selenium driver (for fallback)
            if not self.scraper.setup_selenium_driver():
                logger.warning("⚠️ Selenium setup failed, will use requests only")
            
            # Step 3: Validate parser
            parser_stats = self.parser.get_parsing_stats()
            logger.info(f"Parser ready: {parser_stats['field_selectors_count']} field categories")
            
            # Step 4: Reset validator stats
            self.validator.reset_stats()
            
            logger.info("✅ Web scraping system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    def scrape_all_funds(self, force_scrape: bool = False) -> Dict[str, Any]:
        """
        Scrape all configured fund URLs with full pipeline.
        """
        logger.info(f"Starting full scraping pipeline (force: {force_scrape})")
        
        self.scraping_stats['started_at'] = datetime.now().isoformat()
        
        scraping_results = {
            'implementation_metadata': {
                'phase': '1.3.1',
                'version': '1.0',
                'started_at': self.scraping_stats['started_at'],
                'force_scrape': force_scrape
            },
            'fund_results': [],
            'summary': {},
            'validation_summary': {},
            'success': False,
            'errors': []
        }
        
        try:
            # Process each fund URL
            for i, fund_url in enumerate(settings.fund_urls):
                logger.info(f"Processing fund {i+1}/{len(settings.fund_urls)}: {fund_url}")
                
                try:
                    # Step 1: Scrape URL with retry and fallback
                    scrape_result = self.scraper.scrape_with_retry(fund_url)
                    
                    if not scrape_result.get('success', False):
                        logger.error(f"❌ Scraping failed: {scrape_result.get('error', 'Unknown')}")
                        self.scraping_stats['failed_scrapes'] += 1
                        scraping_results['errors'].append({
                            'url': fund_url,
                            'error': scrape_result.get('error', 'Unknown'),
                            'method': scrape_result.get('method', 'unknown')
                        })
                        continue
                    
                    # Step 2: Parse HTML content
                    soup = scrape_result.get('content')
                    if not soup:
                        logger.error("❌ No HTML content to parse")
                        self.scraping_stats['failed_scrapes'] += 1
                        continue
                    
                    fund_data = self.parser.parse_fund_page(soup, fund_url)
                    
                    # Step 3: Validate parsed data
                    validation_result = self.validator.validate_fund_data(fund_data)
                    
                    # Step 4: Enhance with scraping metadata
                    fund_data.update({
                        'scraping_metadata': {
                            'scrape_method': scrape_result.get('method', 'unknown'),
                            'scrape_time': scrape_result.get('scraped_at'),
                            'request_id': scrape_result.get('request_id', 0),
                            'validation_confidence': fund_data.get('extraction_confidence', 0.0)
                        },
                        'validation_result': validation_result,
                        'processing_status': 'completed'
                    })
                    
                    # Add to results
                    scraping_results['fund_results'].append(fund_data)
                    self.scraping_stats['successful_scrapes'] += 1
                    self.scraping_stats['total_documents'] += 1
                    
                    # Store validation result
                    fund_name = fund_data.get('fund_name', 'Unknown')
                    self.scraping_stats['validation_results'][fund_name] = validation_result
                    
                    logger.info(f"✅ Successfully processed: {fund_name}")
                    logger.info(f"   Validation score: {validation_result.get('validation_score', 0):.1f}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing fund {fund_url}: {e}")
                    self.scraping_stats['failed_scrapes'] += 1
                    scraping_results['errors'].append({
                        'url': fund_url,
                        'error': str(e),
                        'stage': 'processing'
                    })
            
            # Calculate summary statistics
            scraping_results['summary'] = self._calculate_summary_stats()
            scraping_results['validation_summary'] = self._calculate_validation_summary()
            
            # Determine overall success
            success_rate = (self.scraping_stats['successful_scrapes'] / 
                          self.scraping_stats['total_urls']) * 100 if self.scraping_stats['total_urls'] > 0 else 0
            
            scraping_results['success'] = (
                success_rate >= 80.0 and  # At least 80% success rate
                len(scraping_results['errors']) == 0
            )
            
            self.scraping_stats['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"Web scraping completed. Success rate: {success_rate:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Critical error in scraping pipeline: {e}")
            scraping_results['success'] = False
            scraping_results['errors'].append({
                'error': str(e),
                'stage': 'pipeline'
            })
        
        return scraping_results
    
    def _calculate_summary_stats(self) -> Dict[str, Any]:
        """
        Calculate summary statistics from scraping results.
        """
        total = self.scraping_stats['total_urls']
        successful = self.scraping_stats['successful_scrapes']
        failed = self.scraping_stats['failed_scrapes']
        
        return {
            'total_urls': total,
            'successful_scrapes': successful,
            'failed_scrapes': failed,
            'success_rate': (successful / total) * 100 if total > 0 else 0,
            'total_documents': self.scraping_stats['total_documents'],
            'scraping_duration': self._calculate_duration(),
            'methods_used': self._get_methods_used(),
            'average_confidence': self._calculate_average_confidence()
        }
    
    def _calculate_validation_summary(self) -> Dict[str, Any]:
        """
        Calculate validation summary from all validation results.
        """
        validation_results = self.scraping_stats['validation_results']
        
        if not validation_results:
            return {'status': 'no_data', 'message': 'No validation results available'}
        
        total_validations = len(validation_results)
        passed_validations = len([
            v for v in validation_results.values() 
            if v.get('overall_status') == 'passed'
        ])
        
        validation_scores = [
            v.get('validation_score', 0) for v in validation_results.values()
        ]
        avg_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0
        
        return {
            'total_validations': total_validations,
            'passed_validations': passed_validations,
            'failed_validations': total_validations - passed_validations,
            'average_validation_score': round(avg_score, 1),
            'validation_success_rate': (passed_validations / total_validations) * 100 if total_validations > 0 else 0,
            'validation_status': 'good' if avg_score >= 80.0 else 'needs_improvement'
        }
    
    def _calculate_duration(self) -> str:
        """
        Calculate scraping duration.
        """
        if not self.scraping_stats.get('started_at') or not self.scraping_stats.get('completed_at'):
            return "unknown"
        
        try:
            start = datetime.fromisoformat(self.scraping_stats['started_at'].replace(' ', 'T'))
            end = datetime.fromisoformat(self.scraping_stats['completed_at'].replace(' ', 'T'))
            duration = end - start
            
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "error"
    
    def _get_methods_used(self) -> Dict[str, int]:
        """
        Get count of scraping methods used.
        """
        methods = {'requests': 0, 'selenium': 0}
        
        for validation_result in self.scraping_stats['validation_results'].values():
            if isinstance(validation_result, dict):
                fund_name = validation_result.get('fund_name', '')
                # This would need to be tracked during scraping
                # For now, return default
                break
        
        return methods
    
    def _calculate_average_confidence(self) -> float:
        """
        Calculate average extraction confidence.
        """
        confidences = []
        
        for validation_result in self.scraping_stats['validation_results'].values():
            if isinstance(validation_result, dict):
                fund_name = validation_result.get('fund_name', '')
                # This would need to be tracked during parsing
                # For now, return default
                break
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def generate_scraping_report(self, output_file: str = None) -> str:
        """
        Generate comprehensive scraping report.
        """
        logger.info("Generating scraping report...")
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'web_scraping_implementation',
                'phase': '1.3.1',
                'version': '1.0'
            },
            'scraping_stats': self.scraping_stats,
            'system_info': {
                'scraper_config': self.scraper.get_scraping_stats(),
                'parser_config': self.parser.get_parsing_stats(),
                'validator_config': self.validator.get_validation_stats()
            },
            'fund_urls': settings.fund_urls,
            'recommendations': self._generate_recommendations()
        }
        
        report_json = json.dumps(report, indent=2, default=str)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_json)
            logger.info(f"Scraping report saved to {output_file}")
        
        return report_json
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on scraping results.
        """
        recommendations = []
        
        success_rate = (self.scraping_stats['successful_scrapes'] / 
                      self.scraping_stats['total_urls']) * 100 if self.scraping_stats['total_urls'] > 0 else 0
        
        # Success rate recommendations
        if success_rate < 100.0:
            recommendations.append(f"Improve success rate from {success_rate:.1f}% to 100%")
        
        # Validation score recommendations
        validation_summary = self._calculate_validation_summary()
        avg_score = validation_summary.get('average_validation_score', 0)
        
        if avg_score < 90.0:
            recommendations.append(f"Improve data validation score from {avg_score:.1f}% to 90%+")
        
        # Error-based recommendations
        if self.scraping_stats['errors']:
            error_types = set()
            for error in self.scraping_stats['errors']:
                if isinstance(error, dict) and 'stage' in error:
                    error_types.add(error['stage'])
            
            for error_type in error_types:
                recommendations.append(f"Fix errors in {error_type} stage")
        
        # General recommendations
        recommendations.extend([
            "Monitor scraping performance regularly",
            "Update selectors if website structure changes",
            "Implement better error handling for edge cases",
            "Consider adding more robust fallback mechanisms"
        ])
        
        return recommendations
    
    def cleanup_resources(self):
        """
        Cleanup all scraping resources.
        """
        try:
            logger.info("Cleaning up scraping resources...")
            
            if self.scraper:
                self.scraper.cleanup()
                logger.info("✅ Scraper resources cleaned up")
            
            logger.info("✅ All scraping resources cleaned up")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

# Global implementation instance
web_scraping_impl = WebScrapingImplementation()

if __name__ == "__main__":
    # Test web scraping implementation
    print("🚀 Testing Phase 1.3.1 Web Scraping Implementation")
    print("=" * 60)
    
    try:
        # Initialize system
        if web_scraping_impl.initialize_scraping_system():
            print("✅ System initialization successful")
            
            # Run scraping
            print("\n📥 Starting web scraping...")
            results = web_scraping_impl.scrape_all_funds(force_scrape=True)
            
            # Display results
            print(f"\n📊 Scraping Results:")
            print(f"Success: {results.get('success', False)}")
            print(f"Total URLs: {results.get('summary', {}).get('total_urls', 0)}")
            print(f"Successful: {results.get('summary', {}).get('successful_scrapes', 0)}")
            print(f"Failed: {results.get('summary', {}).get('failed_scrapes', 0)}")
            print(f"Success Rate: {results.get('summary', {}).get('success_rate', 0):.1f}%")
            print(f"Documents: {results.get('summary', {}).get('total_documents', 0)}")
            
            # Validation summary
            validation_summary = results.get('validation_summary', {})
            print(f"\n🔍 Validation Summary:")
            print(f"Avg Score: {validation_summary.get('average_validation_score', 0):.1f}")
            print(f"Validation Success Rate: {validation_summary.get('validation_success_rate', 0):.1f}%")
            print(f"Validation Status: {validation_summary.get('validation_status', 'unknown')}")
            
            # Show fund results
            fund_results = results.get('fund_results', [])
            print(f"\n📋 Fund Results:")
            for i, fund in enumerate(fund_results[:5], 1):  # Show first 5
                fund_name = fund.get('fund_name', 'Unknown')
                validation_score = fund.get('validation_result', {}).get('validation_score', 0)
                print(f"  {i}. {fund_name} (Score: {validation_score:.1f})")
            
            if len(fund_results) > 5:
                print(f"  ... and {len(fund_results) - 5} more funds")
            
            # Errors
            errors = results.get('errors', [])
            if errors:
                print(f"\n❌ Errors:")
                for error in errors[:3]:
                    print(f"  • {error}")
            
            # Generate report
            report_file = f"web_scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            web_scraping_impl.generate_scraping_report(report_file)
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
        web_scraping_impl.cleanup_resources()
        print("\n🏁 Testing completed")
        print("=" * 60)
