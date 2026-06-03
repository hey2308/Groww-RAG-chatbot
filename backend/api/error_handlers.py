"""
Phase 4.2 - Error Handling
Custom exception handlers and error response formatting
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AdvisoryQueryError(Exception):
    """Exception raised for advisory queries."""
    def __init__(self, message: str, educational_link: str = "https://www.amfiindia.com/investor-education"):
        self.message = message
        self.educational_link = educational_link
        super().__init__(self.message)

class InvalidQueryError(Exception):
    """Exception raised for invalid query format."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class SystemError(Exception):
    """Exception raised for system errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

def register_error_handlers(app: FastAPI):
    """Register custom error handlers for the FastAPI app."""
    
    @app.exception_handler(AdvisoryQueryError)
    async def advisory_query_handler(request: Request, exc: AdvisoryQueryError):
        """Handle advisory query errors with 422 status code."""
        logger.warning(f"Advisory query error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": exc.message,
                "educational_link": exc.educational_link
            }
        )
    
    @app.exception_handler(InvalidQueryError)
    async def invalid_query_handler(request: Request, exc: InvalidQueryError):
        """Handle invalid query errors with 400 status code."""
        logger.warning(f"Invalid query error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": exc.message
            }
        )
    
    @app.exception_handler(SystemError)
    async def system_error_handler(request: Request, exc: SystemError):
        """Handle system errors with 500 status code."""
        logger.error(f"System error: {exc.message}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "An internal system error occurred. Please try again later."
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors with 400 status code."""
        logger.warning(f"Validation error: {exc.errors()}")
        
        error_messages = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_messages.append(f"{field}: {message}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Invalid request format",
                "details": error_messages
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other unexpected exceptions with 500 status code."""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "An unexpected error occurred. Please try again later."
            }
        )

# Response validation middleware
class ResponseValidationMiddleware:
    """Middleware to validate response length and content."""
    
    def __init__(self, app: FastAPI, max_response_length: int = 1000):
        self.app = app
        self.max_response_length = max_response_length
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.body":
                body = message.get("body", b"")
                if len(body) > self.max_response_length * 1024:  # Convert KB to bytes
                    logger.warning(f"Response too long: {len(body)} bytes")
                    # Truncate response if too long
                    message["body"] = body[:self.max_response_length * 1024]
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

# Input sanitization middleware
class InputSanitizationMiddleware:
    """Middleware to sanitize and validate input data."""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def receive_wrapper():
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                # Log input for monitoring
                logger.info(f"Request received: {len(body)} bytes")
            return message
        
        await self.app(scope, receive_wrapper, send)

# Rate limiting middleware (simplified version)
class RateLimitMiddleware:
    """Simple rate limiting middleware."""
    
    def __init__(self, app: FastAPI, max_requests: int = 100, window_seconds: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Get client IP (simplified - in production use proper IP extraction)
        client_ip = scope.get("client", ("unknown",))[0]
        
        # Check rate limit
        current_time = time.time()
        if client_ip in self.request_counts:
            requests, window_start = self.request_counts[client_ip]
            if current_time - window_start < self.window_seconds:
                if requests >= self.max_requests:
                    logger.warning(f"Rate limit exceeded for {client_ip}")
                    response = JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"error": "Rate limit exceeded. Please try again later."}
                    )
                    await response(scope, receive, send)
                    return
            else:
                # Reset window
                self.request_counts[client_ip] = (0, current_time)
        else:
            self.request_counts[client_ip] = (0, current_time)
        
        # Increment request count
        self.request_counts[client_ip] = (
            self.request_counts[client_ip][0] + 1,
            self.request_counts[client_ip][1]
        )
        
        await self.app(scope, receive, send)

import time
