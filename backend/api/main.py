"""
Phase 4.1 - API Architecture
Main FastAPI application with chat, health, and sources endpoints
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging
from error_handlers import (
    register_error_handlers,
    AdvisoryQueryError,
    InvalidQueryError,
    SystemError,
    ResponseValidationMiddleware,
    InputSanitizationMiddleware
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Mutual Fund FAQ Assistant API",
    description="Facts-only RAG-based mutual fund FAQ assistant",
    version="1.0.0"
)

# Register error handlers
register_error_handlers(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ResponseValidationMiddleware, max_response_length=1000)
app.add_middleware(InputSanitizationMiddleware)

# Request/Response Models
class ChatRequest(BaseModel):
    query: str = Field(..., description="User query about mutual funds", min_length=1, max_length=500)
    
class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response to the query")
    source: str = Field(..., description="Source URL for the information")
    timestamp: str = Field(..., description="Response timestamp")
    
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    educational_link: Optional[str] = Field(None, description="Educational link for advisory queries")

class HealthResponse(BaseModel):
    status: str = Field(..., description="System health status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")

class SourcesResponse(BaseModel):
    sources: List[str] = Field(..., description="List of official sources")
    count: int = Field(..., description="Number of sources")
    timestamp: str = Field(..., description="Response timestamp")

# Official sources
OFFICIAL_SOURCES = [
    "https://www.amfiindia.com",
    "https://www.groww.in",
    "https://www.mutualfundsindia.com",
    "https://www.valueresearchonline.com"
]

# Advisory query patterns
ADVISORY_PATTERNS = [
    "should i invest",
    "should i buy",
    "should i sell",
    "recommend",
    "best fund",
    "top fund",
    "advice",
    "suggestion",
    "which fund to invest",
    "is it good to invest",
    "worth investing"
]

def is_advisory_query(query: str) -> bool:
    """Check if query is advisory in nature."""
    query_lower = query.lower()
    return any(pattern in query_lower for pattern in ADVISORY_PATTERNS)

@app.post("/api/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_endpoint(request: ChatRequest):
    """
    Process user query and return factual response with source citation.
    
    Args:
        request: ChatRequest with user query
        
    Returns:
        ChatResponse with AI response, source, and timestamp
        
    Raises:
        HTTPException: For advisory queries or invalid input
    """
    logger.info(f"Received query: {request.query}")
    
    # Check for advisory query
    if is_advisory_query(request.query):
        logger.warning("Advisory query detected")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "This appears to be an advisory query. I can only provide factual information about mutual funds.",
                "educational_link": "https://www.amfiindia.com/investor-education"
            }
        )
    
    try:
        # TODO: Integrate with RAG pipeline
        # For now, return a placeholder response
        response_text = "This is a placeholder response. The RAG pipeline integration will be implemented in Phase 2."
        source_url = "https://www.amfiindia.com"
        
        response = ChatResponse(
            response=response_text,
            source=source_url,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Response generated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing query"
        )

@app.get("/api/health", response_model=HealthResponse)
async def health_endpoint():
    """
    System health check endpoint.
    
    Returns:
        HealthResponse with system status and timestamp
    """
    logger.info("Health check requested")
    
    try:
        # TODO: Add actual health checks (database, RAG pipeline, etc.)
        health_status = "healthy"
        
        response = HealthResponse(
            status=health_status,
            timestamp=datetime.now().isoformat(),
            version="1.0.0"
        )
        
        logger.info(f"Health check: {health_status}")
        return response
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@app.get("/api/sources", response_model=SourcesResponse)
async def sources_endpoint():
    """
    List of official sources used for mutual fund information.
    
    Returns:
        SourcesResponse with list of sources and metadata
    """
    logger.info("Sources list requested")
    
    try:
        response = SourcesResponse(
            sources=OFFICIAL_SOURCES,
            count=len(OFFICIAL_SOURCES),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Returned {len(OFFICIAL_SOURCES)} sources")
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sources"
        )

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Mutual Fund FAQ Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health",
            "sources": "/api/sources"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
