"""
Orchestrates Phase 1.3.1–1.3.5 for scheduled data pipeline runs.
"""

from __future__ import annotations

import importlib
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import settings

from .chroma_backup import backup_chroma_db, restore_chroma_db
from .validation_gate import PipelineValidationGate, ValidationGateResult

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class PipelineRunResult:
    success: bool
    rolled_back: bool = False
    stages: Dict[str, Any] = field(default_factory=dict)
    validation: Optional[ValidationGateResult] = None
    backup: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "rolled_back": self.rolled_back,
            "stages": self.stages,
            "validation": self.validation.to_dict() if self.validation else None,
            "backup": self.backup,
            "errors": self.errors,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


def _import_from_phase13(subpackage: str, module_name: str, attr: str):
    """Import a singleton from a phase1_3 subpackage (uses local relative imports)."""
    subdir = BACKEND_ROOT / "phase1_3" / subpackage
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))
    if str(subdir) not in sys.path:
        sys.path.insert(0, str(subdir))
    module = importlib.import_module(module_name)
    return getattr(module, attr)


class Phase13Orchestrator:
    """Runs scrape → clean → chunk → embed → store with backup, validation, and rollback."""

    def __init__(
        self,
        chroma_path: Optional[str] = None,
        validation_gate: Optional[PipelineValidationGate] = None,
        skip_scrape: bool = False,
    ):
        self.chroma_path = chroma_path or settings.chroma_db_path
        self.validation_gate = validation_gate or PipelineValidationGate()
        self.skip_scrape = skip_scrape

    def run(self, *, force_scrape: bool = True) -> PipelineRunResult:
        run = PipelineRunResult(success=False, started_at=datetime.utcnow().isoformat() + "Z")
        chroma_config = None

        try:
            from phase1_3.vector_database.chroma_integration import ChromaConfig

            chroma_config = ChromaConfig(persist_directory=self.chroma_path)
        except ImportError:
            pass

        run.backup = backup_chroma_db(self.chroma_path, reason="pre_pipeline")

        try:
            if not self._run_pipeline_stages(run, force_scrape=force_scrape, chroma_config=chroma_config):
                run.errors.append("One or more pipeline stages failed")
                self._rollback(run, "pipeline_stage_failure")
                return run

            run.validation = self.validation_gate.validate(run.to_dict())
            if not run.validation.passed:
                run.errors.extend(run.validation.errors)
                self._rollback(run, "validation_gate_failed")
                return run

            run.success = True
            logger.info("Phase 1.3 pipeline completed and passed validation")
            return run

        except Exception as e:
            logger.exception("Pipeline failed with exception: %s", e)
            run.errors.append(str(e))
            self._rollback(run, "unhandled_exception")
            return run

        finally:
            run.completed_at = datetime.utcnow().isoformat() + "Z"
            self._cleanup_scraper()

    def _run_pipeline_stages(
        self,
        run: PipelineRunResult,
        *,
        force_scrape: bool,
        chroma_config: Any,
    ) -> bool:
        web_scraping_impl = _import_from_phase13("web_scraping", "main_scraper", "web_scraping_impl")
        data_cleaning_impl = _import_from_phase13("data_cleaning", "main_cleaner", "data_cleaning_impl")
        text_chunking_impl = _import_from_phase13("text_chunking", "main_chunker", "text_chunking_impl")
        embedding_generation_impl = _import_from_phase13(
            "embedding_generation", "main_embedder", "embedding_generation_impl"
        )
        vector_db_integration = _import_from_phase13(
            "vector_database", "main_integration", "vector_db_integration"
        )

        if chroma_config is not None:
            vector_db_integration.config = chroma_config
            vector_db_integration.chroma_integration.config = chroma_config

        # 1.3.1 Web scraping
        scraped_funds: List[Dict[str, Any]] = []
        if self.skip_scrape:
            logger.info("Skipping scrape (skip_scrape=True)")
            run.stages["scraping"] = {"success": True, "skipped": True, "summary": {}}
        else:
            if not web_scraping_impl.initialize_scraping_system():
                run.stages["scraping"] = {"success": False, "error": "initialization_failed"}
                return False
            scrape_result = web_scraping_impl.scrape_all_funds(force_scrape=force_scrape)
            run.stages["scraping"] = {
                "success": scrape_result.get("success", False),
                "summary": scrape_result.get("summary", {}),
                "errors": scrape_result.get("errors", []),
            }
            if not run.stages["scraping"]["success"]:
                return False
            scraped_funds = scrape_result.get("fund_results", [])

        if not scraped_funds and not self.skip_scrape:
            run.stages["scraping"]["success"] = False
            run.errors.append("No fund data scraped")
            return False

        # 1.3.2 Cleaning
        if not data_cleaning_impl.initialize_cleaning_system():
            run.stages["cleaning"] = {"success": False, "error": "initialization_failed"}
            return False
        cleaning_result = data_cleaning_impl.clean_scraped_data(scraped_funds)
        cleaned_list = cleaning_result.get("cleaning_results", [])
        run.stages["cleaning"] = {
            "success": cleaning_result.get("success", False),
            "summary": cleaning_result.get("processing_summary", {}),
            "document_count": len(cleaned_list),
        }
        if not run.stages["cleaning"]["success"]:
            return False

        # 1.3.3 Chunking
        if not text_chunking_impl.initialize_chunking_system():
            run.stages["chunking"] = {"success": False, "error": "initialization_failed"}
            return False
        chunking_result = text_chunking_impl.chunk_cleaned_data(cleaned_list)
        chunked_list = chunking_result.get("chunking_results", [])
        run.stages["chunking"] = {
            "success": chunking_result.get("success", False),
            "summary": chunking_result.get("chunking_summary", {}),
            "document_count": len(chunked_list),
        }
        if not run.stages["chunking"]["success"]:
            return False

        # 1.3.4 Embeddings
        if not embedding_generation_impl.initialize_embedding_system():
            run.stages["embedding"] = {"success": False, "error": "initialization_failed"}
            return False
        embedding_result = embedding_generation_impl.generate_embeddings_for_chunks(chunked_list)
        embedding_list = embedding_result.get("embedding_results", [])
        run.stages["embedding"] = {
            "success": embedding_result.get("success", False),
            "summary": embedding_result.get("generation_summary", {}),
            "document_count": len(embedding_list),
        }
        if not run.stages["embedding"]["success"]:
            return False

        # 1.3.5 Vector store
        if not vector_db_integration.initialize_vector_db():
            run.stages["storage"] = {"success": False, "error": "initialization_failed"}
            return False
        storage_result = vector_db_integration.store_embeddings(embedding_list)
        run.stages["storage"] = {
            "success": storage_result.get("success", False),
            "summary": storage_result.get("storage_summary", {}),
            "collection_stats": storage_result.get("collection_stats", {}),
        }
        return bool(run.stages["storage"]["success"])

    def _rollback(self, run: PipelineRunResult, reason: str) -> None:
        if not run.backup.get("backed_up"):
            logger.warning("Rollback skipped (%s): no backup was taken", reason)
            return
        restore_result = restore_chroma_db(self.chroma_path)
        run.rolled_back = restore_result.get("restored", False)
        if run.rolled_back:
            logger.info("Rolled back ChromaDB after %s", reason)
        else:
            run.errors.append(f"Rollback failed: {restore_result.get('error', 'unknown')}")

    def _cleanup_scraper(self) -> None:
        try:
            web_scraping_impl = _import_from_phase13("web_scraping", "main_scraper", "web_scraping_impl")
            web_scraping_impl.cleanup_resources()
        except Exception as e:
            logger.debug("Scraper cleanup: %s", e)
