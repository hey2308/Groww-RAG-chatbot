"""Tests for ChromaDB backup and rollback utilities."""

import tempfile
from pathlib import Path

from pipeline.chroma_backup import backup_chroma_db, has_backup, restore_chroma_db


def test_backup_and_restore_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        chroma_path = Path(tmp) / "chroma_db"
        chroma_path.mkdir()
        marker = chroma_path / "marker.txt"
        marker.write_text("original", encoding="utf-8")

        backup_result = backup_chroma_db(chroma_path)
        assert backup_result["backed_up"] is True
        assert has_backup(chroma_path)

        marker.write_text("corrupted", encoding="utf-8")
        restore_result = restore_chroma_db(chroma_path)
        assert restore_result["restored"] is True
        assert marker.read_text(encoding="utf-8") == "original"


def test_backup_skipped_when_source_missing():
    with tempfile.TemporaryDirectory() as tmp:
        chroma_path = Path(tmp) / "chroma_db"
        result = backup_chroma_db(chroma_path)
        assert result["skipped"] is True
        assert result["backed_up"] is False
