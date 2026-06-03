from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from guardrails import enforce_three_sentences, strip_urls
from retrieval.retriever import RetrievedChunk


SYSTEM_PROMPT = (
    "You are a facts-only mutual fund assistant. "
    "Your job is to extract and state the specific fact the user asked about, "
    "using ONLY the information in the provided context. "
    "Do NOT say the context is insufficient if the answer is present. "
    "Do NOT add opinions, advice, or caveats beyond what is in the context."
)


@dataclass
class ResponsePipelineInput:
    user_query: str
    chunks: List[RetrievedChunk]
    source_url: Optional[str]


class ResponseGenerationPipeline:
    """
    Phase 2.3 response generation pipeline.

    Responsibilities:
    - Build structured prompt from retrieved context.
    - Call Groq LLM through existing Groq client.
    - Enforce output constraints (max 3 sentences, footer, no inline URL spam).
    """

    def _build_context(self, chunks: List[RetrievedChunk], max_items: int = 6) -> str:
        lines: List[str] = []
        for chunk in chunks[:max_items]:
            if not chunk or not chunk.document:
                continue
            lines.append(f"- {chunk.document}")
        return "\n".join(lines)

    def _build_prompt(self, data: ResponsePipelineInput) -> str:
        context = self._build_context(data.chunks)
        return (
            f"{SYSTEM_PROMPT}\n\n"
            "Rules:\n"
            "- Answer in a maximum of 3 sentences.\n"
            "- State the specific fact directly (e.g. 'The NAV of X is Y.').\n"
            "- Use only the numbers and facts from the context below.\n"
            "- Do NOT provide investment advice or opinions.\n"
            "- Do NOT say 'based on the context' or 'according to the context'.\n"
            "- Do NOT include any URLs in your answer.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {data.user_query}\n"
            "Answer:"
        )

    def generate_factual_response(self, groq_client, data: ResponsePipelineInput) -> str:
        prompt = self._build_prompt(data)
        answer = groq_client.generate_response(prompt, max_tokens=300)

        # Enforce response constraints from architecture/problem statement.
        answer = strip_urls(answer)  # source link is attached separately in API output
        answer = enforce_three_sentences(answer)
        footer = f"Last updated from sources: {datetime.utcnow().date().isoformat()}"
        return f"{answer}\n\n{footer}"
