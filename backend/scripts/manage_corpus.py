#!/usr/bin/env python3
"""
Corpus Management Script for Phase 1.2
Integrates corpus collection, processing, and validation.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from corpus.corpus_manager import corpus_manager
from corpus.corpus_validator import corpus_validator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main corpus management function.
    """
    parser = argparse.ArgumentParser(description='Manage HDFC Mutual Fund Corpus')
    parser.add_argument(
        'action',
        choices=['collect', 'validate', 'update', 'info', 'report'],
        required=True,
        help='Action to perform'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update even if data is fresh'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file for reports'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if args.action == 'collect':
            collect_corpus(args.force)
        elif args.action == 'validate':
            validate_corpus(args.output)
        elif args.action == 'update':
            update_corpus(args.force)
        elif args.action == 'info':
            show_corpus_info()
        elif args.action == 'report':
            generate_corpus_report(args.output)
        else:
            logger.error(f"Unknown action: {args.action}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)

def collect_corpus(force_update: bool = False):
    """
    Collect corpus data from Groww URLs.
    """
    logger.info("Starting corpus collection...")
    
    # Update corpus if needed
    update_result = corpus_manager.update_corpus(force_update=force_update)
    
    if update_result["success"]:
        logger.info("✅ Corpus collection completed successfully")
        logger.info(f"📊 Total funds processed: {update_result['collection_results']['total_funds']}")
        logger.info(f"📄 Total documents created: {update_result['processing_results']['documents_processed']}")
        
        # Show summary
        print("\n" + "="*60)
        print("📊 CORPUS COLLECTION SUMMARY")
        print("="*60)
        print(f"✅ Status: {update_result['success']}")
        print(f"📈 Total Funds: {update_result['collection_results']['total_funds']}")
        print(f"📄 Documents Created: {update_result['processing_results']['documents_processed']}")
        print(f"⏰ Completed At: {update_result['completed_at']}")
        print("="*60)
    else:
        logger.error("❌ Corpus collection failed")
        if update_result.get("errors"):
            for error in update_result["errors"]:
                logger.error(f"Error: {error}")
        print("\n" + "="*60)
        print("❌ CORPUS COLLECTION FAILED")
        print("="*60)

def validate_corpus(output_file: str = None):
    """
    Validate corpus completeness and quality.
    """
    logger.info("Starting corpus validation...")
    
    # Generate validation report
    report = corpus_validator.generate_validation_report(output_file)
    
    try:
        report_data = json.loads(report)
        completeness = report_data.get("completeness_validation", {})
        quality = report_data.get("quality_validation", {})
        
        print("\n" + "="*60)
        print("🔍 CORPUS VALIDATION REPORT")
        print("="*60)
        
        # Completeness summary
        print(f"📊 Completeness Score: {completeness.get('completeness_score', 0):.1f}%")
        print(f"📈 Total Funds: {completeness.get('total_funds', 0)}")
        print(f"❌ Missing Funds: {len(completeness.get('missing_funds', []))}")
        
        if completeness.get("missing_funds"):
            print("Missing:")
            for fund in completeness["missing_funds"]:
                print(f"  • {fund}")
        
        # Quality summary
        print(f"🎯 Quality Score: {quality.get('overall_quality_score', 0):.1f}")
        print(f"📅 Data Freshness: {quality.get('data_freshness', 'unknown')}")
        
        # Overall status
        overall_status = report_data.get("overall_assessment", {}).get("ready_for_production", False)
        status_emoji = "✅" if overall_status else "⚠️"
        print(f"{status_emoji} Ready for Production: {overall_status}")
        
        # Recommendations
        recommendations = report_data.get("overall_assessment", {}).get("recommendations", [])
        if recommendations:
            print("\n📋 Recommendations:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"  {i}. {rec}")
        
        print("="*60)
        
        if output_file:
            print(f"\n📄 Detailed report saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error displaying validation report: {e}")

def update_corpus(force_update: bool = False):
    """
    Update corpus with fresh data.
    """
    logger.info(f"Starting corpus update (force: {force_update})...")
    
    update_result = corpus_manager.update_corpus(force_update=force_update)
    
    if update_result["success"]:
        logger.info("✅ Corpus update completed successfully")
        
        # Show update summary
        print("\n" + "="*60)
        print("🔄 CORPUS UPDATE SUMMARY")
        print("="*60)
        print(f"✅ Status: {update_result['success']}")
        print(f"📈 Funds Updated: {update_result['collection_results']['success_count']}")
        print(f"⏰ Updated At: {update_result['completed_at']}")
        
        # Show validation if available
        if "validation_results" in update_result:
            validation = update_result["validation_results"]
            print(f"📊 Completeness: {validation.get('completeness_rate', 0):.1f}%")
        
        print("="*60)
    else:
        logger.error("❌ Corpus update failed")
        print("\n" + "="*60)
        print("❌ CORPUS UPDATE FAILED")
        print("="*60)

def show_corpus_info():
    """
    Show current corpus information.
    """
    logger.info("Retrieving corpus information...")
    
    corpus_info = corpus_manager.get_corpus_summary()
    
    print("\n" + "="*60)
    print("📊 CORPUS INFORMATION")
    print("="*60)
    
    # Metadata
    metadata = corpus_info.get("corpus_info", {})
    print(f"📅 Created At: {metadata.get('created_at', 'Unknown')}")
    print(f"🔗 Total URLs: {metadata.get('total_funds', 0)}")
    print(f"🌐 Source Platform: {metadata.get('source_platform', 'Unknown')}")
    print(f"⏰ Update Frequency: {metadata.get('update_frequency', 'Unknown')}")
    print(f"📅 Last Updated: {metadata.get('last_updated', 'Never')}")
    
    # Quality metrics
    quality = corpus_info.get("quality_metrics", {})
    print(f"📈 Document Count: {quality.get('total_documents', 0)}")
    print(f"💾 Collection Health: {quality.get('collection_health', 'Unknown')}")
    print(f"🎯 Quality Score: {quality.get('quality_score', 0):.1f}")
    print(f"📅 Data Freshness: {quality.get('data_freshness', 'Unknown')}")
    
    # Fund details
    fund_details = corpus_info.get("fund_details", [])
    print(f"📋 Available Funds: {len(fund_details)}")
    
    if fund_details:
        print("\nFund Details:")
        for fund in fund_details[:10]:  # Show first 10 funds
            print(f"  • {fund.get('fund_name', 'Unknown')} ({fund.get('category', 'N/A')})")
    
    if len(fund_details) > 10:
        print(f"  ... and {len(fund_details) - 10} more funds")
    
    print("="*60)

def generate_corpus_report(output_file: str = None):
    """
    Generate comprehensive corpus report.
    """
    logger.info("Generating comprehensive corpus report...")
    
    # Generate both validation and quality reports
    validation_report = corpus_validator.generate_validation_report()
    quality_report = corpus_validator.validate_data_quality()
    
    # Combine reports
    comprehensive_report = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "report_type": "comprehensive_corpus_report",
            "version": "1.0"
        },
        "corpus_summary": corpus_manager.get_corpus_summary(),
        "validation_report": json.loads(validation_report),
        "quality_report": quality_report,
        "recommendations": _generate_comprehensive_recommendations()
    }
    
    # Save report
    report_json = json.dumps(comprehensive_report, indent=2, default=str)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_json)
        logger.info(f"Comprehensive report saved to {output_file}")
    
    # Display summary
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE CORPUS REPORT")
    print("="*60)
    
    # Key metrics
    validation = comprehensive_report.get("validation_report", {})
    quality = comprehensive_report.get("quality_report", {})
    
    print(f"📊 Completeness Score: {validation.get('completeness_score', 0):.1f}%")
    print(f"🎯 Quality Score: {quality.get('overall_quality_score', 0):.1f}")
    print(f"📅 Data Freshness: {quality.get('data_freshness', 'Unknown')}")
    print(f"📄 Total Documents: {quality.get('total_documents', 0)}")
    
    # Status
    ready_for_production = (
        validation.get("overall_status") == "passed" and 
        quality.get("overall_quality_score", 0) >= 80.0
    )
    
    status_emoji = "✅" if ready_for_production else "⚠️"
    print(f"{status_emoji} Production Ready: {ready_for_production}")
    
    # Top recommendations
    recommendations = comprehensive_report.get("recommendations", [])
    if recommendations:
        print("\n🔧 Top Recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec}")
    
    print("="*60)
    
    return report_json

def _generate_comprehensive_recommendations() -> list:
    """
    Generate comprehensive recommendations based on corpus status.
    """
    recommendations = []
    
    # Get current status
    corpus_info = corpus_manager.get_corpus_summary()
    quality_metrics = corpus_info.get("quality_metrics", {})
    
    # Data freshness recommendations
    freshness = quality_metrics.get("data_freshness", "unknown")
    if freshness != "fresh":
        recommendations.append("Schedule more frequent data updates to ensure freshness")
    
    # Document coverage recommendations
    doc_count = quality_metrics.get("total_documents", 0)
    if doc_count < 75:  # Expected ~75 documents (5 funds × ~15 chunks)
        recommendations.append("Increase document coverage by improving chunking strategy")
    
    # Quality score recommendations
    quality_score = quality_metrics.get("quality_score", 0)
    if quality_score < 85:
        recommendations.append("Focus on improving data quality metrics")
    
    # General recommendations
    recommendations.extend([
        "Monitor corpus health metrics regularly",
        "Implement automated quality checks",
        "Set up alerts for data degradation"
    ])
    
    return recommendations

if __name__ == "__main__":
    main()
