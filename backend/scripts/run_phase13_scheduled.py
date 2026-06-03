#!/usr/bin/env python3
"""
Scheduled Phase 1.3 pipeline entry point (Phase 1.4).
Runs full pipeline with pre-backup, validation gate, and rollback on failure.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from pipeline.phase13_orchestrator import Phase13Orchestrator
from pipeline.validation_gate import PipelineValidationGate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 1.3 scheduled data pipeline")
    parser.add_argument(
        "--force-scrape",
        action="store_true",
        default=True,
        help="Force fresh scrape of all fund URLs (default: true)",
    )
    parser.add_argument(
        "--no-force-scrape",
        action="store_false",
        dest="force_scrape",
        help="Use cached scrape behavior where supported",
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping (for testing downstream stages only)",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="pipeline_run_report.json",
        help="Write JSON report to this path",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run validation gate only (no pipeline)",
    )
    args = parser.parse_args()

    if args.validate_only:
        gate = PipelineValidationGate()
        result = gate.validate({"stages": {}, "success": True})
        report = result.to_dict()
        _write_report(args.report, report)
        return 0 if result.passed else 1

    orchestrator = Phase13Orchestrator(skip_scrape=args.skip_scrape)
    run_result = orchestrator.run(force_scrape=args.force_scrape)
    report = run_result.to_dict()

    _write_report(args.report, report)

    if run_result.success:
        logger.info("Pipeline succeeded")
        return 0

    if run_result.rolled_back:
        logger.error("Pipeline failed; ChromaDB was rolled back")
    else:
        logger.error("Pipeline failed; rollback was not performed or failed")

    for err in run_result.errors:
        logger.error("  %s", err)
    return 1


def _write_report(path: str, data: dict) -> None:
    out = Path(path)
    if not out.is_absolute():
        out = BACKEND_ROOT / out
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Report written to %s", out)


if __name__ == "__main__":
    sys.exit(main())
