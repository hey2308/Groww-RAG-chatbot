from __future__ import annotations

import logging
import re
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.settings import settings
from database.chroma_setup import chroma_manager

logger = logging.getLogger(__name__)


_METRIC_HINTS: List[Tuple[str, str]] = [
    (r"\bexpense\s*ratio\b", "metric"),
    (r"\bexit\s*load\b", "metric"),
    (r"\bminimum\s*sip\b|\bmin\s*sip\b|\bsip\b", "metric"),
    (r"\bnav\b|\bnet\s*asset\s*value\b", "metric"),
    (r"\baum\b|\bassets?\s*under\s*management\b", "metric"),
    (r"\block.?in\b", "metric"),
    (r"\brisk\b|\briskometer\b", "primary"),
    (r"\bbenchmark\b", "primary"),
    (r"\bfund\s*manager\b|\bmanager\b", "primary"),
    (r"\bcategory\b|\bfund\s*type\b", "primary"),
    (r"\breturn(s)?\b|\bperformance\b|\bcagr\b|\bxirr\b", "performance"),
    (r"\bholding(s)?\b|\bportfolio\b|\bstocks?\s*held\b", "metric"),
    (r"\bsector\b|\bsector\s*allocation\b|\bindustry\b", "metric"),
    (r"\basset\s*allocation\b|\ballocation\b", "metric"),
    (r"\btop\s*holdings?\b|\blargest\s*holdings?\b", "metric"),
]

# Canonical fund names as defined in the problem statement / architecture
_CANONICAL_FUNDS: List[str] = [
    "HDFC Mid Cap Fund Direct Growth",
    "HDFC Equity Fund Direct Growth",
    "HDFC Focused Fund Direct Growth",
    "HDFC ELSS Tax Saver Fund Direct Plan Growth",
    "HDFC Large Cap Fund Direct Growth",
]

# Keyword aliases that map to a canonical fund name
_FUND_ALIASES: List[Tuple[List[str], str]] = [
    (["mid cap", "midcap", "mid-cap"], "HDFC Mid Cap Fund Direct Growth"),
    (["equity fund", "equity direct"], "HDFC Equity Fund Direct Growth"),
    (["focused fund", "focused direct"], "HDFC Focused Fund Direct Growth"),
    (["elss", "tax saver", "80c"], "HDFC ELSS Tax Saver Fund Direct Plan Growth"),
    (["large cap", "largecap", "large-cap"], "HDFC Large Cap Fund Direct Growth"),
]

# Known out-of-scope fund names — return a clear "not in corpus" signal
_OUT_OF_SCOPE_PATTERNS: List[str] = [
    r"\bflexi\s*cap\b",
    r"\bsmall\s*cap\b",
    r"\bbalanced\b",
    r"\bhybrid\b",
    r"\bdebt\b",
    r"\bliquid\s*fund\b",
    r"\bindex\s*fund\b",
    r"\bnifty\s*50\b",
    r"\bsensex\b",
    r"\baxis\b",
    r"\bsbi\b",
    r"\bicici\b",
    r"\bkotak\b",
    r"\bmirae\b",
    r"\bparag\s*parikh\b",
    r"\bquant\b",
    r"\bnipon\b|\bnippon\b",
    r"\bdsp\b",
    r"\buti\b",
    r"\bcanara\b",
    r"\bfranklin\b",
    r"\binvesco\b",
    r"\bpgim\b",
    r"\bwhiteoak\b",
    r"\bmotilal\b",
    r"\btata\b",
    r"\bsundaram\b",
    r"\bnavi\b",
    r"\bzerodha\b",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _tokenize(text: str) -> List[str]:
    t = re.sub(r"[^a-z0-9\s%.-]", " ", text.lower())
    return [w for w in t.split() if len(w) >= 3]


def _lexical_overlap_score(query: str, doc: str) -> float:
    q = set(_tokenize(query))
    if not q:
        return 0.0
    d = set(_tokenize(doc))
    return len(q & d) / max(1, len(q))


def _detect_fund_name(query: str) -> Optional[str]:
    """
    Returns the canonical fund name if the query refers to one of the 5 in-scope funds.
    Returns None if no specific fund is mentioned (query is general).
    Does NOT return anything for out-of-scope funds — those are handled separately.
    """
    qn = _normalize(query)

    # 1. Exact full-name match (highest confidence)
    for name in _CANONICAL_FUNDS:
        if _normalize(name) in qn:
            return name

    # 2. Alias / keyword match (only if "hdfc" is present or alias is unambiguous)
    has_hdfc = "hdfc" in qn
    for aliases, canonical in _FUND_ALIASES:
        for alias in aliases:
            if alias in qn:
                # For generic aliases like "equity fund", require "hdfc" to avoid false positives
                if has_hdfc or alias in ("elss", "tax saver", "80c"):
                    return canonical

    return None


def _is_out_of_scope_fund(query: str) -> bool:
    """Returns True if the query mentions a fund that is clearly not in our corpus."""
    qn = _normalize(query)
    for pattern in _OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, qn):
            return True
    return False


def _detect_preferred_chunk_type(query: str) -> Optional[str]:
    q = _normalize(query)
    for pattern, chunk_type in _METRIC_HINTS:
        if re.search(pattern, q):
            return chunk_type
    return None


def _fund_matches(candidate_fund_name: str, requested_fund_name: str) -> bool:
    return _normalize(candidate_fund_name) == _normalize(requested_fund_name)


@dataclass
class RetrievedChunk:
    document: str
    metadata: Dict[str, Any]
    distance: Optional[float] = None
    score: Optional[float] = None


@dataclass
class RetrievalResult:
    query: str
    fund_name: Optional[str]
    preferred_chunk_type: Optional[str]
    chunks: List[RetrievedChunk]
    out_of_scope: bool = False

    @property
    def best_source_url(self) -> str:
        # Use the source URL from the highest-scored chunk first
        if self.chunks:
            url = (self.chunks[0].metadata or {}).get("source_url")
            if url:
                return url
        # Fall back to any chunk that has a URL
        for c in self.chunks:
            url = (c.metadata or {}).get("source_url")
            if url:
                return url
        # Last resort: fund-specific URL based on detected fund name, NOT generic fallback
        if self.fund_name:
            fund_url_map = {
                "HDFC Mid Cap Fund Direct Growth": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
                "HDFC Equity Fund Direct Growth": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
                "HDFC Focused Fund Direct Growth": "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
                "HDFC ELSS Tax Saver Fund Direct Plan Growth": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
                "HDFC Large Cap Fund Direct Growth": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
            }
            return fund_url_map.get(self.fund_name, settings.fund_urls[0] if settings.fund_urls else "")
        return settings.fund_urls[0] if settings.fund_urls else ""

    @property
    def best_score(self) -> float:
        if not self.chunks:
            return 0.0
        return max((c.score or 0.0) for c in self.chunks)

    @property
    def has_sufficient_context(self) -> bool:
        if self.out_of_scope:
            return False
        if not self.chunks:
            return False
        top = self.chunks[0]
        if top.distance is None:
            # Lexical fallback: any non-trivial overlap is sufficient
            return self.best_score >= 0.10
        # Vector retrieval: cosine similarity threshold
        return self.best_score >= 0.35


class Retriever:
    """
    Phase 2.1 retrieval implementation.

    Strategy:
    - Fetch candidate results from ChromaDB using query_texts (best effort).
    - Rerank with metadata-aware boosts + lexical overlap.
    - Detect out-of-scope fund queries and return early.
    """

    def __init__(self, *, candidate_k: int = 30, final_k: int = 6):
        self.candidate_k = candidate_k
        self.final_k = final_k
        self._chunk_file_candidates = [
            Path("backend/phase1_3/text_chunking"),
            Path("phase1_3/text_chunking"),
            Path("backend/backend/phase1_3/text_chunking"),
        ]

    def retrieve(self, query: str) -> RetrievalResult:
        fund_name = _detect_fund_name(query)
        preferred_chunk_type = _detect_preferred_chunk_type(query)

        # Check if the query is about a fund that is not in our corpus
        if _is_out_of_scope_fund(query):
            logger.info("Out-of-scope fund detected in query: %s", query)
            return RetrievalResult(
                query=query,
                fund_name=None,
                preferred_chunk_type=preferred_chunk_type,
                chunks=[],
                out_of_scope=True,
            )

        try:
            raw = chroma_manager.collection.query(
                query_texts=[query],
                n_results=self.candidate_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            logger.exception("Retriever query failed; trying lexical fallback: %s", exc)
            return self._fallback_lexical_retrieve(
                query=query,
                fund_name=fund_name,
                preferred_chunk_type=preferred_chunk_type,
            )

        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        dists = (raw.get("distances") or [[]])[0]

        candidates: List[RetrievedChunk] = []
        for doc, meta, dist in zip(docs, metas, dists):
            candidates.append(RetrievedChunk(document=doc or "", metadata=meta or {}, distance=dist))

        reranked = self._rerank(query, candidates, fund_name, preferred_chunk_type)
        return RetrievalResult(
            query=query,
            fund_name=fund_name,
            preferred_chunk_type=preferred_chunk_type,
            chunks=reranked[: self.final_k],
        )

    def _fallback_lexical_retrieve(
        self,
        *,
        query: str,
        fund_name: Optional[str],
        preferred_chunk_type: Optional[str],
    ) -> RetrievalResult:
        candidates = self._load_candidates_from_chunk_files()
        if not candidates:
            return RetrievalResult(
                query=query,
                fund_name=fund_name,
                preferred_chunk_type=preferred_chunk_type,
                chunks=[],
            )

        reranked = self._rerank(query, candidates, fund_name, preferred_chunk_type)
        return RetrievalResult(
            query=query,
            fund_name=fund_name,
            preferred_chunk_type=preferred_chunk_type,
            chunks=reranked[: self.final_k],
        )

    def _load_candidates_from_chunk_files(self) -> List[RetrievedChunk]:
        candidates: List[RetrievedChunk] = []
        latest_file: Optional[Path] = None
        for base in self._chunk_file_candidates:
            if not base.exists():
                continue
            files = sorted(base.glob("chunked_data_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if files:
                latest_file = files[0]
                break

        if latest_file is None:
            return candidates

        try:
            data = json.loads(latest_file.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Failed reading chunk file fallback: %s", latest_file)
            return candidates

        for fund_entry in data:
            for chunk in fund_entry.get("chunks", []):
                fund_meta = chunk.get("fund_metadata") or {}
                fn = fund_meta.get("fund_name", "")
                content = chunk.get("content", "")
                if fn and content:
                    content = f"Fund: {fn}. {content}"
                metadata = {
                    "chunk_type": chunk.get("chunk_type", ""),
                    "fund_name": fn,
                    "source_url": fund_meta.get("source_url", ""),
                }
                candidates.append(
                    RetrievedChunk(
                        document=content,
                        metadata=metadata,
                        distance=None,
                    )
                )
        return candidates

    def _rerank(
        self,
        query: str,
        candidates: List[RetrievedChunk],
        fund_name: Optional[str],
        preferred_chunk_type: Optional[str],
    ) -> List[RetrievedChunk]:
        def sim(dist: Optional[float]) -> float:
            if dist is None:
                return 0.0
            try:
                return max(0.0, 1.0 - float(dist))
            except Exception:
                return 0.0

        qn = _normalize(query)

        # If the user asked about a specific known fund, only keep chunks for that fund
        if fund_name:
            fund_candidates = [
                c for c in candidates
                if _fund_matches(str((c.metadata or {}).get("fund_name", "")), fund_name)
            ]
            # Only filter if we actually found matching chunks
            if fund_candidates:
                candidates = fund_candidates

        for c in candidates:
            base = sim(c.distance)
            lex = _lexical_overlap_score(query, c.document)
            meta = c.metadata or {}

            boost = 0.0
            c_fund = _normalize(str(meta.get("fund_name", "")))
            if fund_name and _normalize(fund_name) == c_fund:
                boost += 0.10

            c_type = str(meta.get("chunk_type", "")).lower()
            if preferred_chunk_type and c_type == preferred_chunk_type:
                boost += 0.12

            # Extra boost when the document explicitly contains the queried metric keyword
            if preferred_chunk_type == "metric":
                for kw in ["expense ratio", "exit load", "nav", "sip", "aum", "lock-in", "lock in",
                           "holding", "holdings", "sector", "allocation", "portfolio", "top holdings"]:
                    if kw in qn and kw in c.document.lower():
                        boost += 0.05
                        break

            # Lexical fallback mode: lexical score dominates
            if c.distance is None:
                c.score = (lex * 0.90) + boost
            else:
                c.score = (base * 0.75) + (lex * 0.20) + boost

        candidates.sort(key=lambda x: (x.score or 0.0), reverse=True)
        return candidates
