"""
Vector store backup and rollback for scheduled pipeline runs.
"""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

ROLLBACK_DIR_NAME = "vector_store_rollback"
MANIFEST_NAME = "manifest.json"


def _rollback_root(store_path: Path) -> Path:
    return store_path.parent / ROLLBACK_DIR_NAME


def _manifest_path(store_path: Path) -> Path:
    return _rollback_root(store_path) / MANIFEST_NAME


def has_backup(store_path: str | Path) -> bool:
    """Return True if a rollback snapshot exists for the given store path."""
    root = Path(store_path)
    rollback_dir = _rollback_root(root)
    return rollback_dir.is_dir() and any(rollback_dir.iterdir())


def backup_chroma_db(store_path: str | Path, reason: str = "pre_pipeline") -> Dict[str, Any]:
    """
    Copy the live vector store directory to the rollback snapshot location.
    Skips backup when the source directory does not exist (first run).
    """
    source = Path(store_path)
    rollback_dir = _rollback_root(source)
    result: Dict[str, Any] = {
        "backed_up": False,
        "skipped": False,
        "reason": reason,
        "source": str(source.resolve()),
        "rollback_path": str(rollback_dir.resolve()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if not source.exists():
        logger.info("No existing vector store at %s; skipping pre-run backup", source)
        result["skipped"] = True
        result["message"] = "source_missing"
        return result

    if rollback_dir.exists():
        shutil.rmtree(rollback_dir)

    shutil.copytree(source, rollback_dir)
    manifest = {
        "created_at": result["timestamp"],
        "reason": reason,
        "source": result["source"],
        "document_count_hint": _count_hint(),
    }
    with open(rollback_dir / MANIFEST_NAME, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    result["backed_up"] = True
    logger.info("Vector store backup created at %s", rollback_dir)
    return result


def restore_chroma_db(store_path: str | Path) -> Dict[str, Any]:
    """
    Restore the live vector store from the rollback snapshot.
    """
    target = Path(store_path)
    rollback_dir = _rollback_root(target)
    result: Dict[str, Any] = {
        "restored": False,
        "target": str(target.resolve()),
        "rollback_path": str(rollback_dir.resolve()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if not rollback_dir.is_dir():
        result["error"] = "no_rollback_snapshot"
        logger.error("Rollback failed: no snapshot at %s", rollback_dir)
        return result

    if target.exists():
        shutil.rmtree(target)

    shutil.copytree(rollback_dir, target)
    result["restored"] = True
    logger.info("Vector store restored from %s to %s", rollback_dir, target)
    return result


def _count_hint() -> Optional[int]:
    """Best-effort document count before backup."""
    try:
        from database.chroma_setup import chroma_manager
        stats = chroma_manager.get_collection_stats()
        return stats.get("document_count")
    except Exception:
        return None
