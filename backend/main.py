from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from datetime import datetime

from llm.groq_client import groq_client
from llm.response_pipeline import ResponseGenerationPipeline, ResponsePipelineInput
from guardrails import classify_query_policy
from retrieval.retriever import Retriever

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Mutual Fund FAQ Assistant API",
    description="Facts-only Q&A for mutual fund schemes",
    version="1.0.0"
)

response_pipeline = ResponseGenerationPipeline()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    source: Optional[str] = None
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    message: str

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Mutual Fund FAQ Assistant API",
        "version": "1.0.0",
        "status": "active"
    }

# Health check endpoint
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="API is running and all systems operational"
    )

# Chat endpoint (placeholder - will be implemented in Phase 2)
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process user query and return factual response with source citation.
    This endpoint will be fully implemented in Phase 2 with RAG pipeline.
    """
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        policy = classify_query_policy(query)
        category = policy.category

        if category == "personal_info":
            return ChatResponse(
                response=(
                    "I can’t help with personal or sensitive information requests. "
                    "Please do not share PAN, Aadhaar, account numbers, OTPs, email, or phone details."
                ),
                source=None,
                timestamp=datetime.utcnow().isoformat() + "Z",
            )

        if category == "advisory":
            return ChatResponse(
                response=(
                    "I can only provide factual mutual fund information and cannot give investment advice. "
                    "Please refer to investor education resources for guidance."
                ),
                source="https://www.amfiindia.com/investor-education",
                timestamp=datetime.utcnow().isoformat() + "Z",
            )

        if category == "performance":
            return ChatResponse(
                response="I can’t interpret performance or recommend funds. Please refer to the official fund page for the latest performance tables.",
                source="https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
                timestamp=datetime.utcnow().isoformat() + "Z",
            )

        retriever = Retriever()
        retrieval = retriever.retrieve(query)

        # Out-of-scope fund: the query mentions a fund not in our corpus
        if retrieval.out_of_scope:
            return ChatResponse(
                response=(
                    "This fund is not part of our current corpus. "
                    "I can only answer questions about these 5 HDFC funds: "
                    "HDFC Large Cap Fund Direct Growth, HDFC Equity Fund Direct Growth, "
                    "HDFC Focused Fund Direct Growth, HDFC ELSS Tax Saver Fund Direct Plan Growth, "
                    "and HDFC Mid Cap Fund Direct Growth."
                ),
                source=None,
                timestamp=datetime.utcnow().isoformat() + "Z",
            )

        if not retrieval.has_sufficient_context:
            # Per user constraint: do not attach URL when answer is unknown.
            return ChatResponse(
                response="I do not have enough source-backed information to answer this query accurately.",
                source=None,
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
        answer = response_pipeline.generate_factual_response(
            groq_client=groq_client,
            data=ResponsePipelineInput(
                user_query=query,
                chunks=retrieval.chunks,
                source_url=retrieval.best_source_url,
            ),
        )

        return ChatResponse(
            response=answer,
            source=retrieval.best_source_url,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Sources endpoint
@app.get("/api/sources")
async def get_sources():
    """
    Return list of official sources used for data collection.
    """
    sources = [
        "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
    ]
    return {"sources": sources}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
