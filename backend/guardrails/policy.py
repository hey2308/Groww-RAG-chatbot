from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


ADVISORY_PATTERNS = [
    r"\bshould i invest\b",
    r"\bwhich fund is better\b",
    r"\brecommend\b",
    r"\bbest fund\b",
    r"\bwhat should i buy\b",
]

PERFORMANCE_PATTERNS = [
    r"\breturn(s)?\b",
    r"\bperformance\b",
    r"\bcagr\b",
    r"\bxirr\b",
    r"\bcompare\b",
    r"\bbeat(s)?\s+the\s+market\b",
    r"\boutperform\b",
]

# NAV, expense ratio, exit load, SIP, AUM, lock-in, benchmark, riskometer
# are all FACTUAL — never block them as performance queries.
FACTUAL_OVERRIDE_PATTERNS = [
    r"\bnav\b|\bnet\s*asset\s*value\b",
    r"\bexpense\s*ratio\b",
    r"\bexit\s*load\b",
    r"\bminimum\s*sip\b|\bmin\s*sip\b|\bsip\s*amount\b",
    r"\baum\b|\bassets?\s*under\s*management\b",
    r"\block.?in\b",
    r"\bbenchmark\b",
    r"\briskometer\b",
    r"\bfund\s*manager\b",
    r"\bfund\s*category\b",
    r"\bholding(s)?\b|\bportfolio\b",
    r"\bsector\s*allocation\b|\bsector\b|\bindustry\b",
    r"\basset\s*allocation\b|\ballocation\b",
    r"\btop\s*holdings?\b|\blargest\s*holdings?\b",
]

PERSONAL_INFO_PATTERNS = [
    r"\bpan\b",
    r"\baadhaar\b|\baadhar\b",
    r"\botp\b",
    r"\baccount number\b|\bbank account\b",
    r"\bifsc\b",
    r"\bemail\b|\be-mail\b",
    r"\bphone number\b|\bmobile number\b",
    r"[A-Z]{5}[0-9]{4}[A-Z]",  # PAN-like token
    r"\b\d{12}\b",  # Aadhaar-like token
]


@dataclass
class PolicyDecision:
    category: str  # factual|advisory|performance|personal_info
    reason: Optional[str] = None


def classify_query_policy(query: str) -> PolicyDecision:
    q = query.strip().lower()

    for p in PERSONAL_INFO_PATTERNS:
        if re.search(p, q, flags=re.IGNORECASE):
            return PolicyDecision("personal_info", "personal_or_sensitive_information")

    for p in ADVISORY_PATTERNS:
        if re.search(p, q, flags=re.IGNORECASE):
            return PolicyDecision("advisory", "investment_advice_request")

    # Check if the query is about a factual metric — these override performance patterns
    is_factual_metric = any(
        re.search(p, q, flags=re.IGNORECASE) for p in FACTUAL_OVERRIDE_PATTERNS
    )
    if not is_factual_metric:
        for p in PERFORMANCE_PATTERNS:
            if re.search(p, q, flags=re.IGNORECASE):
                return PolicyDecision("performance", "performance_or_return_query")

    return PolicyDecision("factual")


def strip_urls(text: str) -> str:
    return re.sub(r"https?://\S+", "", text).strip()


def enforce_three_sentences(text: str) -> str:
    # simple sentence boundary split
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) <= 3:
        return " ".join(parts)
    return " ".join(parts[:3])

