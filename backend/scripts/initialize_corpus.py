#!/usr/bin/env python3
"""
Corpus Initialization Script for Phase 1.2
Initializes the corpus with first-time data collection and setup.
"""

import logging
import sys
import json
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
    Initialize corpus for the first time.
    """
    logger.info("Starting corpus initialization...")
    
    print("\n" + "="*60)
    print("🚀 CORPUS INITIALIZATION")
    print("="*60)
    print("This script will:")
    print("1. Collect data from all 5 Groww mutual fund URLs")
    print("2. Process and chunk the data for RAG")
    print("3. Store in ChromaDB with embeddings")
    print("4. Validate corpus completeness and quality")
    print("5. Generate initialization report")
    print("="*60)
    
    # Confirm initialization
    response = input("\nDo you want to proceed with corpus initialization? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        logger.info("Corpus initialization cancelled by user")
        print("\n❌ Corpus initialization cancelled")
        sys.exit(0)
    
    print("\n🔄 Starting corpus initialization...")
    
    try:
        # Step 1: Collect corpus data
        logger.info("Step 1: Collecting corpus data")
        print("\n📥 Step 1: Collecting corpus data...")
        
        update_result = corpus_manager.update_corpus(force_update=True)
        
        if not update_result["success"]:
            logger.error("Corpus initialization failed at data collection")
            print("\n❌ Step 1 Failed: Data collection")
            if update_result.get("errors"):
                print("Errors:")
                for error in update_result["errors"]:
                    print(f"  • {error}")
            sys.exit(1)
        
        print("✅ Step 1 Completed: Data collection successful")
        print(f"   📈 Funds processed: {update_result['collection_results']['total_funds']}")
        print(f"   📄 Documents created: {update_result['processing_results']['documents_processed']}")
        
        # Step 2: Validate corpus
        logger.info("Step 2: Validating corpus")
        print("\n🔍 Step 2: Validating corpus...")
        
        validation_report = corpus_validator.validate_corpus_completeness()
        
        completeness_score = validation_report.get("completeness_score", 0)
        missing_funds = validation_report.get("missing_funds", [])
        incomplete_funds = validation_report.get("incomplete_funds", [])
        
        if completeness_score < 80.0 or missing_funds:
            print(f"\n⚠️  Step 2 Warning: Corpus completeness score is {completeness_score:.1f}%")
            if missing_funds:
                print(f"   ❌ Missing funds: {len(missing_funds)}")
                for fund in missing_funds:
                    print(f"     • {fund}")
            if incomplete_funds:
                print(f"   ⚠️  Incomplete funds: {len(incomplete_funds)}")
                for fund in incomplete_funds:
                    print(f"     • {fund}")
        else:
            print("✅ Step 2 Completed: Corpus validation passed")
            print(f"   📊 Completeness score: {completeness_score:.1f}%")
        
        # Step 3: Quality assessment
        logger.info("Step 3: Assessing data quality")
        print("\n🎯 Step 3: Assessing data quality...")
        
        quality_report = corpus_validator.validate_data_quality()
        quality_score = quality_report.get("overall_quality_score", 0)
        data_freshness = quality_report.get("data_freshness", "unknown")
        
        if quality_score < 70.0:
            print(f"\n⚠️  Step 3 Warning: Quality score is {quality_score:.1f}")
            print(f"   📅 Data freshess: {data_freshness}")
        else:
            print("✅ Step 3 Completed: Data quality assessment passed")
            print(f"   🎯 Quality score: {quality_score:.1f}")
            print(f"   📅 Data freshess: {data_freshness}")
        
        # Step 4: Generate initialization report
        logger.info("Step 4: Generating initialization report")
        print("\n📋 Step 4: Generating initialization report...")
        
        init_report = {
            "initialization_metadata": {
                "started_at": datetime.now().isoformat(),
                "script_version": "1.0",
                "corpus_version": "1.0"
            },
            "collection_results": update_result.get("collection_results", {}),
            "validation_results": validation_report,
            "quality_results": quality_report,
            "overall_status": {
                "success": True,
                "ready_for_phase_2": completeness_score >= 80.0 and quality_score >= 70.0,
                "completeness_score": completeness_score,
                "quality_score": quality_score,
                "data_freshness": data_freshness
            },
            "next_steps": _generate_next_steps(completeness_score, quality_score)
        }
        
        # Save initialization report
        report_file = f"corpus_initialization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(init_report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Step 4 Completed: Initialization report saved to {report_file}")
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 CORPUS INITIALIZATION COMPLETED")
        print("="*60)
        print(f"✅ Overall Status: {'SUCCESS' if init_report['overall_status']['success'] else 'NEEDS ATTENTION'}")
        print(f"📊 Completeness Score: {completeness_score:.1f}%")
        print(f"🎯 Quality Score: {quality_score:.1f}")
        print(f"📅 Data Freshness: {data_freshness}")
        print(f"🚀 Ready for Phase 2: {init_report['overall_status']['ready_for_phase_2']}")
        
        if init_report["overall_status"]["ready_for_phase_2"]:
            print("\n🎯 Your corpus is ready for Phase 2 (RAG System Development)!")
            print("Next steps:")
            for step in init_report["next_steps"]:
                print(f"  • {step}")
        else:
            print("\n⚠️  Corpus needs attention before proceeding to Phase 2")
            print("Recommended actions:")
            for step in init_report["next_steps"]:
                print(f"  • {step}")
        
        print("="*60)
        
        return init_report
        
    except KeyboardInterrupt:
        logger.info("Corpus initialization cancelled by user")
        print("\n❌ Corpus initialization cancelled")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Corpus initialization failed: {e}")
        print(f"\n❌ Corpus initialization failed: {e}")
        sys.exit(1)

def _generate_next_steps(completeness_score: float, quality_score: float) -> list:
    """
    Generate next steps based on initialization results.
    """
    next_steps = []
    
    if completeness_score >= 80.0 and quality_score >= 70.0:
        next_steps.extend([
            "Proceed to Phase 2: RAG System Development",
            "Implement query classification system",
            "Set up vector search and retrieval",
            "Integrate Groq LLM for response generation",
            "Test end-to-end RAG pipeline"
        ])
    else:
        if completeness_score < 80.0:
            next_steps.extend([
                "Improve data completeness by collecting missing fund information",
                "Fix data gaps identified in validation",
                "Re-run corpus collection with updated scraping logic",
                "Target 90%+ completeness score"
            ])
        
        if quality_score < 70.0:
            next_steps.extend([
                "Improve data quality metrics",
                "Fix data consistency issues",
                "Enhance data validation and cleaning",
                "Implement better error handling in collection"
            ])
        
        if completeness_score < 80.0 or quality_score < 70.0:
            next_steps.extend([
                "Review and fix corpus issues before Phase 2",
                "Run comprehensive corpus validation",
                "Address missing critical data fields",
                "Ensure data freshness and accuracy"
            ])
    
    return next_steps

if __name__ == "__main__":
    main()
