import requests
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime, timedelta
from config.settings import settings
from scraping.groww_scraper import groww_scraper
from processing.data_processor import DataProcessor
from database.chroma_setup import chroma_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CorpusManager:
    """
    Manages the corpus of HDFC mutual fund data from Groww URLs.
    """
    
    def __init__(self):
        """
        Initialize corpus manager with fund URLs and metadata.
        """
        self.fund_urls = settings.fund_urls
        self.corpus_metadata = {
            "created_at": datetime.now().isoformat(),
            "total_funds": len(self.fund_urls),
            "source_platform": "Groww",
            "data_categories": [
                "scheme_documents",
                "fund_factsheets", 
                "performance_data",
                "risk_information",
                "investment_details"
            ],
            "update_frequency": "daily",
            "last_updated": None
        }
        logger.info(f"Corpus manager initialized with {len(self.fund_urls)} fund URLs")
    
    def get_corpus_info(self) -> Dict[str, Any]:
        """
        Get current corpus information and metadata.
        """
        return {
            "corpus_metadata": self.corpus_metadata,
            "fund_urls": self.fund_urls,
            "collection_stats": chroma_manager.get_collection_stats(),
            "data_quality": self._assess_data_quality()
        }
    
    def collect_corpus_data(self) -> List[Dict[str, Any]]:
        """
        Collect data from all configured fund URLs.
        """
        logger.info("Starting corpus data collection")
        all_fund_data = []
        
        for i, fund_url in enumerate(self.fund_urls):
            logger.info(f"Processing fund {i+1}/{len(self.fund_urls)}: {fund_url}")
            
            try:
                fund_data = groww_scraper.scrape_fund_page(fund_url)
                
                if fund_data and 'error' not in fund_data:
                    # Add corpus metadata
                    fund_data.update({
                        'corpus_collection_date': datetime.now().isoformat(),
                        'corpus_version': '1.0',
                        'data_source': 'groww_official',
                        'processing_status': 'collected'
                    })
                    all_fund_data.append(fund_data)
                    logger.info(f"Successfully collected data for {fund_data.get('fund_name', 'Unknown')}")
                else:
                    logger.error(f"Failed to collect data from {fund_url}")
                    
            except Exception as e:
                logger.error(f"Error collecting from {fund_url}: {e}")
                continue
            
            # Respect rate limiting
            import time
            time.sleep(settings.scraping_delay)
        
        logger.info(f"Corpus collection completed. Total funds: {len(all_fund_data)}")
        return all_fund_data
    
    def process_corpus_data(self, fund_data_list: List[Dict[str, Any]]) -> bool:
        """
        Process collected corpus data and store in ChromaDB.
        """
        logger.info("Starting corpus data processing")
        
        try:
            # Initialize data processor
            processor = DataProcessor(chroma_manager)
            
            # Process fund data
            processed_data = processor.process_fund_data(fund_data_list)
            
            if not processed_data:
                logger.error("No processed data generated from corpus")
                return False
            
            # Store processed data
            success = processor.store_processed_data(processed_data)
            
            if success:
                # Update corpus metadata
                self.corpus_metadata["last_updated"] = datetime.now().isoformat()
                self.corpus_metadata["total_documents"] = len(processed_data)
                
                logger.info(f"Successfully processed and stored {len(processed_data)} documents")
                return True
            else:
                logger.error("Failed to store processed corpus data")
                return False
                
        except Exception as e:
            logger.error(f"Error processing corpus data: {e}")
            return False
    
    def validate_corpus_completeness(self, fund_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate completeness of collected corpus data.
        """
        validation_results = {
            "total_funds": len(fund_data_list),
            "expected_funds": len(self.fund_urls),
            "completeness_rate": 0.0,
            "missing_funds": [],
            "data_quality_issues": [],
            "validation_timestamp": datetime.now().isoformat()
        }
        
        # Check fund completeness
        fund_names = [fund.get('fund_name', '').lower() for fund in fund_data_list]
        expected_funds = [
            "hdfc large cap fund",
            "hdfc equity fund", 
            "hdfc focused fund",
            "hdfc elss tax saver fund",
            "hdfc mid cap fund"
        ]
        
        missing_funds = []
        for expected_fund in expected_funds:
            if not any(expected_fund in fund_name for fund_name in fund_names):
                missing_funds.append(expected_fund)
        
        validation_results["missing_funds"] = missing_funds
        
        # Calculate completeness rate
        if validation_results["expected_funds"] > 0:
            validation_results["completeness_rate"] = (
                (validation_results["total_funds"] / validation_results["expected_funds"]) * 100
            )
        
        # Check data quality for each fund
        quality_issues = []
        for fund_data in fund_data_list:
            fund_issues = self._check_fund_data_quality(fund_data)
            if fund_issues:
                quality_issues.extend(fund_issues)
        
        validation_results["data_quality_issues"] = quality_issues
        
        logger.info(f"Corpus validation completed. Completeness: {validation_results['completeness_rate']:.1f}%")
        return validation_results
    
    def _check_fund_data_quality(self, fund_data: Dict[str, Any]) -> List[str]:
        """
        Check quality of individual fund data.
        """
        issues = []
        
        # Check required fields
        required_fields = ['fund_name', 'source_url', 'scraped_at']
        for field in required_fields:
            if field not in fund_data or not fund_data[field]:
                issues.append(f"Missing required field: {field}")
        
        # Check important financial fields
        financial_fields = ['expense_ratio', 'exit_load', 'min_sip']
        for field in financial_fields:
            if field in fund_data and fund_data[field] == "Not available":
                issues.append(f"Important financial field not available: {field}")
        
        # Check data freshness
        if 'scraped_at' in fund_data:
            try:
                scraped_date = datetime.fromisoformat(fund_data['scraped_at'].replace(' ', 'T'))
                if datetime.now() - scraped_date > timedelta(days=7):
                    issues.append("Data may be outdated (more than 7 days old)")
            except:
                issues.append("Invalid scraped_at date format")
        
        return issues
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """
        Assess overall data quality in the corpus.
        """
        try:
            stats = chroma_manager.get_collection_stats()
            
            quality_assessment = {
                "total_documents": stats.get("document_count", 0),
                "collection_health": "healthy" if stats.get("document_count", 0) > 0 else "empty",
                "data_freshness": self._check_data_freshness(),
                "coverage_score": self._calculate_coverage_score(),
                "quality_score": self._calculate_quality_score(),
                "assessment_timestamp": datetime.now().isoformat()
            }
            
            return quality_assessment
            
        except Exception as e:
            logger.error(f"Error assessing data quality: {e}")
            return {
                "collection_health": "error",
                "error": str(e),
                "assessment_timestamp": datetime.now().isoformat()
            }
    
    def _check_data_freshness(self) -> str:
        """
        Check freshness of data in corpus.
        """
        try:
            if self.corpus_metadata.get("last_updated"):
                last_updated = datetime.fromisoformat(self.corpus_metadata["last_updated"])
                age_days = (datetime.now() - last_updated).days
                
                if age_days <= 1:
                    return "fresh"
                elif age_days <= 7:
                    return "recent"
                else:
                    return "stale"
            else:
                return "unknown"
        except:
            return "error"
    
    def _calculate_coverage_score(self) -> float:
        """
        Calculate coverage score based on available data types.
        """
        try:
            stats = chroma_manager.get_collection_stats()
            doc_count = stats.get("document_count", 0)
            
            # Expected documents: 5 funds × ~3 chunks per fund = 15 documents
            expected_docs = 15
            coverage_score = min((doc_count / expected_docs) * 100, 100.0)
            
            return round(coverage_score, 1)
        except:
            return 0.0
    
    def _calculate_quality_score(self) -> float:
        """
        Calculate overall quality score based on multiple factors.
        """
        try:
            freshness = self._check_data_freshness()
            coverage = self._calculate_coverage_score()
            
            # Weighted scoring
            freshness_score = {
                "fresh": 100,
                "recent": 80,
                "stale": 40,
                "unknown": 20,
                "error": 0
            }.get(freshness, 0)
            
            # Simple quality calculation (can be enhanced)
            quality_score = (freshness_score * 0.4) + (coverage * 0.6)
            
            return round(quality_score, 1)
        except:
            return 0.0
    
    def update_corpus(self, force_update: bool = False) -> Dict[str, Any]:
        """
        Update corpus with fresh data from Groww URLs.
        """
        logger.info(f"Starting corpus update (force: {force_update})")
        
        update_results = {
            "started_at": datetime.now().isoformat(),
            "force_update": force_update,
            "collection_results": {},
            "processing_results": {},
            "validation_results": {},
            "success": False,
            "errors": []
        }
        
        try:
            # Check if update is needed
            if not force_update:
                freshness = self._check_data_freshness()
                if freshness == "fresh":
                    logger.info("Corpus data is fresh, skipping update")
                    update_results["message"] = "Update skipped - data is fresh"
                    return update_results
            
            # Step 1: Collect data from URLs
            logger.info("Step 1: Collecting corpus data")
            fund_data_list = self.collect_corpus_data()
            update_results["collection_results"] = {
                "total_funds": len(fund_data_list),
                "success_count": len([f for f in fund_data_list if 'error' not in f]),
                "errors_count": len([f for f in fund_data_list if 'error' in f])
            }
            
            if not fund_data_list:
                update_results["errors"].append("No fund data collected")
                return update_results
            
            # Step 2: Validate corpus completeness
            logger.info("Step 2: Validating corpus completeness")
            validation_results = self.validate_corpus_completeness(fund_data_list)
            update_results["validation_results"] = validation_results
            
            # Step 3: Process and store data
            logger.info("Step 3: Processing and storing corpus data")
            processing_success = self.process_corpus_data(fund_data_list)
            update_results["processing_results"] = {
                "success": processing_success,
                "documents_processed": len(fund_data_list) * 3  # Approximate chunks per fund
            }
            
            if processing_success and validation_results["completeness_rate"] >= 80.0:
                update_results["success"] = True
                update_results["message"] = "Corpus update completed successfully"
            else:
                update_results["success"] = False
                update_results["message"] = "Corpus update completed with issues"
            
        except Exception as e:
            logger.error(f"Error during corpus update: {e}")
            update_results["errors"].append(str(e))
            update_results["success"] = False
        
        update_results["completed_at"] = datetime.now().isoformat()
        return update_results
    
    def get_corpus_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of corpus status.
        """
        return {
            "corpus_info": self.get_corpus_info(),
            "fund_details": self._get_fund_details(),
            "data_sources": {
                "platform": "Groww",
                "urls": self.fund_urls,
                "access_method": "Web scraping with Selenium fallback",
                "update_frequency": "Daily at 2:00 AM UTC"
            },
            "quality_metrics": self._assess_data_quality()
        }
    
    def _get_fund_details(self) -> List[Dict[str, Any]]:
        """
        Get details of funds in corpus.
        """
        try:
            # Query ChromaDB for fund information
            results = chroma_manager.query_documents("fund names and basic information", n_results=50)
            
            fund_details = []
            if results and 'metadatas' in results and results['metadatas'][0]:
                unique_funds = {}
                for metadata in results['metadatas'][0]:
                    fund_name = metadata.get('fund_name', 'Unknown')
                    if fund_name not in unique_funds:
                        unique_funds[fund_name] = {
                            'fund_name': fund_name,
                            'category': metadata.get('fund_category', 'Unknown'),
                            'source_url': metadata.get('source_url', ''),
                            'last_updated': metadata.get('scraped_at', ''),
                            'data_chunks': 0
                        }
                    unique_funds[fund_name]['data_chunks'] += 1
                
                fund_details = list(unique_funds.values())
            
            return fund_details
            
        except Exception as e:
            logger.error(f"Error getting fund details: {e}")
            return []
    
    def export_corpus_metadata(self, file_path: str) -> bool:
        """
        Export corpus metadata to JSON file.
        """
        try:
            metadata = {
                "corpus_metadata": self.corpus_metadata,
                "fund_urls": self.fund_urls,
                "export_timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Corpus metadata exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting corpus metadata: {e}")
            return False

# Initialize global corpus manager
corpus_manager = CorpusManager()

if __name__ == "__main__":
    # Test corpus manager
    print("Testing Corpus Manager...")
    
    # Get corpus info
    info = corpus_manager.get_corpus_info()
    print(f"Corpus Info: {json.dumps(info, indent=2)}")
    
    # Test corpus update
    update_result = corpus_manager.update_corpus(force_update=True)
    print(f"Update Result: {json.dumps(update_result, indent=2)}")
    
    # Export metadata
    corpus_manager.export_corpus_metadata("corpus_metadata.json")
