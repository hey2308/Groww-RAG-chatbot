import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from corpus.corpus_manager import corpus_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CorpusValidator:
    """
    Validates corpus data quality and completeness according to project requirements.
    """
    
    def __init__(self):
        """
        Initialize validator with corpus manager.
        """
        self.corpus_manager = corpus_manager
        self.required_funds = [
            "HDFC Large Cap Fund Direct Growth",
            "HDFC Equity Fund Direct Growth", 
            "HDFC Focused Fund Direct Growth",
            "HDFC ELSS Tax Saver Fund Direct Plan Growth",
            "HDFC Mid Cap Fund Direct Growth"
        ]
        
        self.required_data_fields = {
            "basic_info": ["fund_name", "category", "fund_type", "expense_ratio", "exit_load", "min_sip"],
            "risk_info": ["riskometer", "benchmark"],
            "performance": ["nav", "returns"],
            "allocation": ["asset_allocation"]
        }
        
        logger.info("Corpus validator initialized")
    
    def validate_corpus_completeness(self) -> Dict[str, Any]:
        """
        Validate corpus completeness against required funds and data fields.
        """
        logger.info("Starting corpus completeness validation")
        
        validation_report = {
            "validation_timestamp": datetime.now().isoformat(),
            "overall_status": "passed",
            "completeness_score": 0.0,
            "missing_funds": [],
            "incomplete_funds": [],
            "data_gaps": [],
            "recommendations": [],
            "fund_details": {}
        }
        
        try:
            # Get fund details from corpus
            fund_details = self.corpus_manager._get_fund_details()
            
            # Check for missing funds
            found_funds = [fund['fund_name'] for fund in fund_details]
            missing_funds = [fund for fund in self.required_funds if fund not in found_funds]
            
            validation_report["missing_funds"] = missing_funds
            
            # Validate each fund's data completeness
            total_score = 0.0
            for fund_detail in fund_details:
                fund_name = fund_detail['fund_name']
                fund_validation = self._validate_individual_fund(fund_detail)
                
                validation_report["fund_details"][fund_name] = fund_validation
                total_score += fund_validation['completeness_score']
            
            # Calculate overall completeness score
            if fund_details:
                validation_report["completeness_score"] = total_score / len(fund_details)
            else:
                validation_report["completeness_score"] = 0.0
                validation_report["overall_status"] = "failed"
            
            # Identify incomplete funds (score < 80%)
            validation_report["incomplete_funds"] = [
                fund_name for fund_name, details in validation_report["fund_details"].items()
                if details['completeness_score'] < 80.0
            ]
            
            # Generate data gap analysis
            validation_report["data_gaps"] = self._analyze_data_gaps(validation_report["fund_details"])
            
            # Generate recommendations
            validation_report["recommendations"] = self._generate_recommendations(validation_report)
            
            # Set overall status
            if (len(missing_funds) == 0 and 
                len(validation_report["incomplete_funds"]) == 0 and 
                validation_report["completeness_score"] >= 90.0):
                validation_report["overall_status"] = "passed"
            else:
                validation_report["overall_status"] = "needs_improvement"
            
            logger.info(f"Corpus validation completed. Score: {validation_report['completeness_score']:.1f}%")
            
        except Exception as e:
            logger.error(f"Error during corpus validation: {e}")
            validation_report["overall_status"] = "error"
            validation_report["error"] = str(e)
        
        return validation_report
    
    def _validate_individual_fund(self, fund_detail: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate individual fund data completeness.
        """
        fund_validation = {
            "fund_name": fund_detail.get('fund_name', 'Unknown'),
            "completeness_score": 0.0,
            "missing_fields": [],
            "available_fields": [],
            "field_coverage": {}
        }
        
        total_fields = 0
        available_fields = 0
        
        # Check each data category
        for category, required_fields in self.required_data_fields.items():
            category_score = 0
            category_available = []
            
            for field in required_fields:
                total_fields += 1
                if self._is_field_available(fund_detail, field):
                    available_fields += 1
                    category_score += 1
                    category_available.append(field)
                    fund_validation["available_fields"].append(field)
                else:
                    fund_validation["missing_fields"].append(f"{category}.{field}")
            
            # Calculate category coverage
            category_coverage = (category_score / len(required_fields)) * 100 if required_fields else 0
            fund_validation["field_coverage"][category] = {
                "coverage_percentage": round(category_coverage, 1),
                "available_fields": category_available,
                "missing_fields": [f for f in required_fields if f not in category_available]
            }
        
        # Calculate overall completeness score
        fund_validation["completeness_score"] = (available_fields / total_fields) * 100 if total_fields > 0 else 0
        
        return fund_validation
    
    def _is_field_available(self, fund_detail: Dict[str, Any], field: str) -> bool:
        """
        Check if a specific field is available and valid.
        """
        # Check direct field availability
        if field in fund_detail and fund_detail[field]:
            value = str(fund_detail[field]).strip()
            return value not in ["Not available", "", "N/A", "null", "None"]
        
        # Check if field might be in nested structures
        if field in ["returns", "asset_allocation"]:
            return field in fund_detail and isinstance(fund_detail[field], dict) and fund_detail[field]
        
        return False
    
    def _analyze_data_gaps(self, fund_details: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze data gaps across all funds.
        """
        data_gaps = []
        
        # Analyze field-level gaps
        field_availability = {}
        for category, required_fields in self.required_data_fields.items():
            for field in required_fields:
                field_key = f"{category}.{field}"
                if field_key not in field_availability:
                    field_availability[field_key] = {"available": 0, "total": 0}
                
                field_availability[field_key]["total"] += len(fund_details)
                
                for fund_validation in fund_details.values():
                    if self._is_field_available(fund_validation, field):
                        field_availability[field_key]["available"] += 1
        
        # Identify significant gaps
        for field_key, stats in field_availability.items():
            availability_rate = (stats["available"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            
            if availability_rate < 50.0:  # Less than 50% availability
                data_gaps.append({
                    "field": field_key,
                    "availability_rate": round(availability_rate, 1),
                    "severity": "high" if availability_rate < 25.0 else "medium",
                    "impact": self._get_field_impact(field_key)
                })
        
        return data_gaps
    
    def _get_field_impact(self, field: str) -> str:
        """
        Get impact description for missing field.
        """
        impact_mapping = {
            "basic_info.expense_ratio": "Cannot answer cost-related queries",
            "basic_info.exit_load": "Cannot answer exit load questions",
            "basic_info.min_sip": "Cannot answer investment amount queries",
            "risk_info.riskometer": "Cannot provide risk assessment",
            "risk_info.benchmark": "Cannot compare with benchmark",
            "performance.nav": "Cannot provide current NAV information",
            "performance.returns": "Cannot answer performance queries",
            "allocation.asset_allocation": "Cannot provide portfolio composition"
        }
        
        return impact_mapping.get(field, "May affect query responses")
    
    def _generate_recommendations(self, validation_report: Dict[str, Any]) -> List[str]:
        """
        Generate improvement recommendations based on validation results.
        """
        recommendations = []
        
        # Missing funds recommendations
        if validation_report["missing_funds"]:
            recommendations.append(
                f"Add missing funds: {', '.join(validation_report['missing_funds'])}"
            )
        
        # Incomplete funds recommendations
        if validation_report["incomplete_funds"]:
            recommendations.append(
                f"Improve data completeness for: {', '.join(validation_report['incomplete_funds'])}"
            )
        
        # Data gap recommendations
        high_priority_gaps = [gap for gap in validation_report.get("data_gaps", []) if gap.get("severity") == "high"]
        if high_priority_gaps:
            gap_fields = [gap["field"] for gap in high_priority_gaps]
            recommendations.append(
                f"Priority: Fix high-impact data gaps: {', '.join(gap_fields)}"
            )
        
        # Overall score recommendations
        if validation_report["completeness_score"] < 90.0:
            recommendations.append(
                f"Target 90%+ completeness (current: {validation_report['completeness_score']:.1f}%)"
            )
        
        # Data freshness recommendations
        freshness = self.corpus_manager._check_data_freshness()
        if freshness != "fresh":
            recommendations.append("Update corpus data - appears to be stale")
        
        return recommendations
    
    def validate_data_quality(self) -> Dict[str, Any]:
        """
        Validate overall data quality metrics.
        """
        logger.info("Starting data quality validation")
        
        quality_report = {
            "validation_timestamp": datetime.now().isoformat(),
            "overall_quality_score": 0.0,
            "data_freshness": self.corpus_manager._check_data_freshness(),
            "consistency_check": {},
            "accuracy_indicators": {},
            "quality_issues": [],
            "recommendations": []
        }
        
        try:
            # Get corpus statistics
            corpus_info = self.corpus_manager.get_corpus_info()
            collection_stats = corpus_info.get("chroma_stats", {})
            
            # Data freshness check
            last_updated = self.corpus_manager.corpus_metadata.get("last_updated")
            if last_updated:
                last_updated_date = datetime.fromisoformat(last_updated.replace(' ', 'T'))
                age_days = (datetime.now() - last_updated_date).days
                
                if age_days <= 1:
                    quality_report["data_freshness"] = "excellent"
                elif age_days <= 7:
                    quality_report["data_freshness"] = "good"
                elif age_days <= 30:
                    quality_report["data_freshness"] = "acceptable"
                else:
                    quality_report["data_freshness"] = "poor"
                    quality_report["quality_issues"].append(f"Data is {age_days} days old")
            
            # Consistency checks
            quality_report["consistency_check"] = self._perform_consistency_checks()
            
            # Accuracy indicators
            quality_report["accuracy_indicators"] = self._assess_accuracy_indicators()
            
            # Calculate overall quality score
            freshness_score = {
                "excellent": 100,
                "good": 85,
                "acceptable": 70,
                "poor": 40
            }.get(quality_report["data_freshness"], 0)
            
            consistency_score = quality_report["consistency_check"].get("score", 0)
            accuracy_score = quality_report["accuracy_indicators"].get("score", 0)
            
            quality_report["overall_quality_score"] = (
                freshness_score * 0.4 + 
                consistency_score * 0.3 + 
                accuracy_score * 0.3
            )
            
            # Generate quality recommendations
            quality_report["recommendations"] = self._generate_quality_recommendations(quality_report)
            
            logger.info(f"Data quality validation completed. Score: {quality_report['overall_quality_score']:.1f}")
            
        except Exception as e:
            logger.error(f"Error during data quality validation: {e}")
            quality_report["overall_quality_score"] = 0.0
            quality_report["error"] = str(e)
        
        return quality_report
    
    def _perform_consistency_checks(self) -> Dict[str, Any]:
        """
        Perform data consistency checks across the corpus.
        """
        consistency_results = {
            "score": 0.0,
            "checks": {},
            "issues": []
        }
        
        try:
            # Get fund details for consistency analysis
            fund_details = self.corpus_manager._get_fund_details()
            
            # Check 1: Fund name consistency
            fund_names = [fund['fund_name'] for fund in fund_details]
            duplicate_names = [name for name in fund_names if fund_names.count(name) > 1]
            
            if duplicate_names:
                consistency_results["issues"].append(f"Duplicate fund names: {duplicate_names}")
            else:
                consistency_results["checks"]["fund_name_uniqueness"] = "passed"
            
            # Check 2: Category consistency
            categories = [fund.get('category', 'Unknown') for fund in fund_details]
            unique_categories = set(categories)
            consistency_results["checks"]["category_diversity"] = {
                "total_categories": len(unique_categories),
                "categories": list(unique_categories),
                "status": "good" if len(unique_categories) >= 3 else "needs_improvement"
            }
            
            # Check 3: Data format consistency
            format_issues = 0
            for fund_detail in fund_details:
                if not self._check_data_format_consistency(fund_detail):
                    format_issues += 1
            
            consistency_results["checks"]["format_consistency"] = {
                "issues_count": format_issues,
                "status": "good" if format_issues == 0 else "needs_improvement"
            }
            
            # Calculate consistency score
            total_checks = 3
            passed_checks = sum([
                1 if len(duplicate_names) == 0 else 0,
                1 if len(unique_categories) >= 3 else 0,
                1 if format_issues == 0 else 0
            ])
            
            consistency_results["score"] = (passed_checks / total_checks) * 100
            
        except Exception as e:
            logger.error(f"Error in consistency checks: {e}")
            consistency_results["error"] = str(e)
        
        return consistency_results
    
    def _check_data_format_consistency(self, fund_detail: Dict[str, Any]) -> bool:
        """
        Check if fund data follows consistent format.
        """
        # Check for required fields with proper data types
        required_checks = [
            ('fund_name', str),
            ('source_url', str),
            ('scraped_at', str)
        ]
        
        for field, expected_type in required_checks:
            if field in fund_detail:
                if not isinstance(fund_detail[field], expected_type):
                    return False
                if not fund_detail[field] or str(fund_detail[field]).strip() == "":
                    return False
            else:
                return False
        
        return True
    
    def _assess_accuracy_indicators(self) -> Dict[str, Any]:
        """
        Assess accuracy indicators for the corpus.
        """
        accuracy_results = {
            "score": 0.0,
            "indicators": {},
            "concerns": []
        }
        
        try:
            # Get corpus statistics
            corpus_info = self.corpus_manager.get_corpus_info()
            collection_stats = corpus_info.get("chroma_stats", {})
            doc_count = collection_stats.get("document_count", 0)
            
            # Indicator 1: Document count adequacy
            expected_docs = len(self.required_funds) * 15  # ~15 chunks per fund
            doc_adequacy = min((doc_count / expected_docs) * 100, 100)
            
            accuracy_results["indicators"]["document_coverage"] = {
                "actual_documents": doc_count,
                "expected_documents": expected_docs,
                "coverage_percentage": round(doc_adequacy, 1),
                "status": "excellent" if doc_adequacy >= 90 else "good" if doc_adequacy >= 70 else "needs_improvement"
            }
            
            # Indicator 2: Source reliability
            source_urls = self.corpus_manager.fund_urls
            accuracy_results["indicators"]["source_reliability"] = {
                "total_sources": len(source_urls),
                "source_platform": "Groww",
                "reliability_score": 85,  # Based on historical success rates
                "status": "reliable"
            }
            
            # Indicator 3: Data structure integrity
            fund_details = self.corpus_manager._get_fund_details()
            structured_funds = len([f for f in fund_details if f.get('fund_name') and f.get('source_url')])
            structure_integrity = (structured_funds / len(fund_details)) * 100 if fund_details else 0
            
            accuracy_results["indicators"]["structure_integrity"] = {
                "structured_funds": structured_funds,
                "total_funds": len(fund_details),
                "integrity_percentage": round(structure_integrity, 1),
                "status": "excellent" if structure_integrity >= 95 else "good" if structure_integrity >= 85 else "needs_improvement"
            }
            
            # Calculate overall accuracy score
            indicators_score = (
                doc_adequacy * 0.4 + 
                85 * 0.3 +  # Source reliability
                structure_integrity * 0.3
            )
            
            accuracy_results["score"] = round(indicators_score, 1)
            
        except Exception as e:
            logger.error(f"Error assessing accuracy indicators: {e}")
            accuracy_results["error"] = str(e)
        
        return accuracy_results
    
    def _generate_quality_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """
        Generate quality improvement recommendations.
        """
        recommendations = []
        
        # Freshness recommendations
        if quality_report["data_freshness"] in ["poor", "acceptable"]:
            recommendations.append("Schedule more frequent data updates")
        
        # Consistency recommendations
        consistency_issues = quality_report.get("consistency_check", {}).get("issues", [])
        if consistency_issues:
            recommendations.append("Address data consistency issues")
        
        # Accuracy recommendations
        accuracy_indicators = quality_report.get("accuracy_indicators", {})
        if isinstance(accuracy_indicators, dict):
            doc_coverage = accuracy_indicators.get("indicators", {}).get("document_coverage", {})
            if doc_coverage.get("coverage_percentage", 0) < 80:
                recommendations.append("Increase document coverage for better query responses")
        
        # Overall quality recommendations
        if quality_report["overall_quality_score"] < 80:
            recommendations.append("Focus on improving overall data quality metrics")
        
        return recommendations
    
    def generate_validation_report(self, output_file: str = None) -> str:
        """
        Generate comprehensive validation report.
        """
        logger.info("Generating comprehensive validation report")
        
        try:
            # Get completeness and quality reports
            completeness_report = self.validate_corpus_completeness()
            quality_report = self.validate_data_quality()
            
            # Combine reports
            full_report = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "corpus_version": "1.0",
                    "validator_version": "1.0"
                },
                "completeness_validation": completeness_report,
                "quality_validation": quality_report,
                "overall_assessment": {
                    "ready_for_production": (
                        completeness_report["overall_status"] == "passed" and
                        quality_report["overall_quality_score"] >= 80.0
                    ),
                    "critical_issues": (
                        completeness_report["missing_funds"] or
                        len(completeness_report["incomplete_funds"]) > 2 or
                        quality_report["overall_quality_score"] < 60.0
                    )
                }
            }
            
            # Output report
            report_json = json.dumps(full_report, indent=2, default=str)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_json)
                logger.info(f"Validation report saved to {output_file}")
            
            return report_json
            
        except Exception as e:
            logger.error(f"Error generating validation report: {e}")
            return json.dumps({"error": str(e)}, indent=2)

# Initialize global validator
corpus_validator = CorpusValidator()

if __name__ == "__main__":
    # Run validation and generate report
    print("Running Corpus Validation...")
    
    report = corpus_validator.generate_validation_report("corpus_validation_report.json")
    print(f"Validation Report Generated")
    print("\nSummary:")
    print("-" * 50)
    
    # Parse and display summary
    try:
        report_data = json.loads(report)
        completeness = report_data.get("completeness_validation", {})
        quality = report_data.get("quality_validation", {})
        
        print(f"Completeness Score: {completeness.get('completeness_score', 0):.1f}%")
        print(f"Quality Score: {quality.get('overall_quality_score', 0):.1f}")
        print(f"Missing Funds: {len(completeness.get('missing_funds', []))}")
        print(f"Incomplete Funds: {len(completeness.get('incomplete_funds', []))}")
        print(f"Ready for Production: {report_data.get('overall_assessment', {}).get('ready_for_production', False)}")
        
    except Exception as e:
        print(f"Error displaying summary: {e}")
