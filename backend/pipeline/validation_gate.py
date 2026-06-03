"""
Post-pipeline validation gate for scheduled Phase 1.3 runs.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ValidationGateResult:
    passed: bool
    checks: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": self.checks,
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": self.summary,
            "validated_at": datetime.utcnow().isoformat() + "Z",
        }


class PipelineValidationGate:
    """
    Validates pipeline output before a scheduled run is considered successful.
    """

    def __init__(
        self,
        min_funds: Optional[int] = None,
        min_scrape_success_rate: Optional[float] = None,
        min_document_count: Optional[int] = None,
        min_completeness_score: Optional[float] = None,
        min_quality_score: Optional[float] = None,
    ):
        self.min_funds = min_funds or int(os.getenv("PIPELINE_MIN_FUNDS", "5"))
        self.min_scrape_success_rate = min_scrape_success_rate or float(
            os.getenv("PIPELINE_MIN_SCRAPE_SUCCESS_RATE", "80")
        )
        self.min_document_count = min_document_count or int(
            os.getenv("PIPELINE_MIN_DOCUMENT_COUNT", "10")
        )
        self.min_completeness_score = min_completeness_score or float(
            os.getenv("PIPELINE_MIN_COMPLETENESS_SCORE", "70")
        )
        self.min_quality_score = min_quality_score or float(
            os.getenv("PIPELINE_MIN_QUALITY_SCORE", "60")
        )

    def validate(
        self,
        pipeline_result: Dict[str, Any],
        *,
        use_corpus_validator: bool = True,
    ) -> ValidationGateResult:
        result = ValidationGateResult(passed=True)

        self._check_pipeline_stages(pipeline_result, result)
        self._check_chroma_stats(result)

        if use_corpus_validator:
            self._check_corpus_validator(result)

        result.passed = len(result.errors) == 0
        result.summary = {
            "min_funds": self.min_funds,
            "min_document_count": self.min_document_count,
            "required_fund_urls": len(settings.fund_urls),
        }
        return result

    def _record(
        self,
        result: ValidationGateResult,
        name: str,
        passed: bool,
        detail: Dict[str, Any],
        *,
        error_message: Optional[str] = None,
        warning_message: Optional[str] = None,
    ) -> None:
        check = {"name": name, "passed": passed, **detail}
        result.checks.append(check)
        if not passed and error_message:
            result.errors.append(error_message)
        if warning_message:
            result.warnings.append(warning_message)

    def _check_pipeline_stages(
        self, pipeline_result: Dict[str, Any], result: ValidationGateResult
    ) -> None:
        stages = pipeline_result.get("stages", {})
        for stage_name in ("scraping", "cleaning", "chunking", "embedding", "storage"):
            stage = stages.get(stage_name, {})
            success = stage.get("success", False)
            self._record(
                result,
                f"stage_{stage_name}",
                success,
                {"stage": stage_name},
                error_message=None if success else f"Stage {stage_name} did not succeed",
            )

        scrape_summary = stages.get("scraping", {}).get("summary", {})
        success_rate = scrape_summary.get("success_rate", 0)
        funds_ok = scrape_summary.get("successful_scrapes", 0) >= self.min_funds
        rate_ok = success_rate >= self.min_scrape_success_rate
        self._record(
            result,
            "scrape_coverage",
            funds_ok and rate_ok,
            {
                "successful_scrapes": scrape_summary.get("successful_scrapes", 0),
                "success_rate": success_rate,
            },
            error_message=None
            if (funds_ok and rate_ok)
            else (
                f"Scrape coverage insufficient: {scrape_summary.get('successful_scrapes', 0)}"
                f" funds, {success_rate:.1f}% success rate"
            ),
        )

    def _check_chroma_stats(self, result: ValidationGateResult) -> None:
        try:
            from database.chroma_setup import chroma_manager

            stats = chroma_manager.get_collection_stats()
            count = stats.get("document_count", 0)
            ok = count >= self.min_document_count
            self._record(
                result,
                "chroma_document_count",
                ok,
                {"document_count": count, "collection": stats.get("collection_name")},
                error_message=None
                if ok
                else f"ChromaDB has {count} documents; minimum is {self.min_document_count}",
            )
        except Exception as e:
            self._record(
                result,
                "chroma_document_count",
                False,
                {"error": str(e)},
                error_message=f"Could not read ChromaDB stats: {e}",
            )

    def _check_corpus_validator(self, result: ValidationGateResult) -> None:
        try:
            from corpus.corpus_validator import corpus_validator

            completeness = corpus_validator.validate_corpus_completeness()
            quality = corpus_validator.validate_data_quality()

            completeness_score = completeness.get("completeness_score", 0)
            quality_score = quality.get("overall_quality_score", 0)
            missing = completeness.get("missing_funds", [])
            status = completeness.get("overall_status", "failed")

            completeness_ok = (
                len(missing) == 0
                and completeness_score >= self.min_completeness_score
                and status in ("passed", "needs_improvement")
            )
            quality_ok = quality_score >= self.min_quality_score

            self._record(
                result,
                "corpus_completeness",
                completeness_ok,
                {
                    "completeness_score": completeness_score,
                    "missing_funds": missing,
                    "status": status,
                },
                error_message=None
                if completeness_ok
                else (
                    f"Corpus completeness failed: score={completeness_score:.1f}, "
                    f"missing={missing}"
                ),
                warning_message=(
                    f"Completeness status is {status}" if status == "needs_improvement" else None
                ),
            )

            self._record(
                result,
                "corpus_quality",
                quality_ok,
                {"overall_quality_score": quality_score},
                error_message=None
                if quality_ok
                else f"Corpus quality score {quality_score:.1f} below {self.min_quality_score}",
            )
        except Exception as e:
            logger.warning("Corpus validator check skipped: %s", e)
            result.warnings.append(f"Corpus validator unavailable: {e}")
