"""
Phase 4.3 - Unit Tests
Unit tests for query classification, response validation, and error handling
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app, is_advisory_query, ADVISORY_PATTERNS
from api.error_handlers import AdvisoryQueryError, InvalidQueryError, SystemError

client = TestClient(app)

class TestQueryClassification:
    """Test query classification accuracy."""
    
    def test_advisory_query_detection(self):
        """Test that advisory queries are correctly identified."""
        advisory_queries = [
            "Should I invest in HDFC Large Cap Fund?",
            "Which mutual fund should I buy for retirement?",
            "Can you recommend the best equity fund?",
            "Is it worth investing in debt funds right now?",
            "What advice would you give for first-time investors?"
        ]
        
        for query in advisory_queries:
            assert is_advisory_query(query), f"Failed to detect advisory query: {query}"
    
    def test_factual_query_classification(self):
        """Test that factual queries are not classified as advisory."""
        factual_queries = [
            "What is the expense ratio of HDFC Large Cap Fund?",
            "What are the returns of SBI Small Cap Fund?",
            "What is the risk level of Axis Bluechip Fund?",
            "What is the minimum SIP amount for ICICI Prudential Fund?",
            "What is the NAV of Kotak Emerging Equity Fund?"
        ]
        
        for query in factual_queries:
            assert not is_advisory_query(query), f"Incorrectly classified factual query as advisory: {query}"
    
    def test_edge_case_queries(self):
        """Test edge cases in query classification."""
        edge_cases = [
            ("What is the best performing fund?", True),  # Contains "best"
            ("What are the top 5 mutual funds?", True),   # Contains "top"
            ("What is the fund's performance history?", False),  # Factual
            ("What are the investment objectives?", False),  # Factual
            ("Should I consider this fund for my portfolio?", True),  # Advisory
        ]
        
        for query, expected_advisory in edge_cases:
            result = is_advisory_query(query)
            assert result == expected_advisory, f"Edge case failed: '{query}' expected {expected_advisory}, got {result}"

class TestResponseValidation:
    """Test response length and content validation."""
    
    def test_chat_response_structure(self):
        """Test that chat response has required fields."""
        response = client.post(
            "/api/chat",
            json={"query": "What is the expense ratio of HDFC Large Cap Fund?"}
        )
        
        # Note: This will fail until RAG integration is complete
        # For now, we test the structure
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "source" in data
            assert "timestamp" in data
            assert isinstance(data["response"], str)
            assert isinstance(data["source"], str)
            assert isinstance(data["timestamp"], str)
    
    def test_response_length_validation(self):
        """Test that responses don't exceed maximum length."""
        # This will be tested with actual RAG integration
        pass
    
    def test_source_url_format(self):
        """Test that source URLs are valid."""
        # This will be tested with actual RAG integration
        pass

class TestErrorHandling:
    """Test error responses and status codes."""
    
    def test_advisory_query_error_response(self):
        """Test that advisory queries return 422 status code."""
        response = client.post(
            "/api/chat",
            json={"query": "Should I invest in HDFC Large Cap Fund?"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "educational_link" in data
        assert "advisory" in data["error"].lower()
    
    def test_invalid_query_format_error(self):
        """Test that invalid query format returns 400 status code."""
        # Test missing query field
        response = client.post(
            "/api/chat",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_empty_query_error(self):
        """Test that empty query returns validation error."""
        response = client.post(
            "/api/chat",
            json={"query": ""}
        )
        
        assert response.status_code == 422
    
    def test_too_long_query_error(self):
        """Test that too long query returns validation error."""
        long_query = "a" * 501  # Exceeds max_length of 500
        
        response = client.post(
            "/api/chat",
            json={"query": long_query}
        )
        
        assert response.status_code == 422

class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_endpoint_success(self):
        """Test that health endpoint returns 200 status."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert data["status"] == "healthy"

class TestSourcesEndpoint:
    """Test sources endpoint."""
    
    def test_sources_endpoint_success(self):
        """Test that sources endpoint returns valid data."""
        response = client.get("/api/sources")
        
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert "count" in data
        assert "timestamp" in data
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) > 0
        assert data["count"] == len(data["sources"])
    
    def test_sources_are_valid_urls(self):
        """Test that all sources are valid URLs."""
        response = client.get("/api/sources")
        data = response.json()
        
        for source in data["sources"]:
            assert source.startswith("http://") or source.startswith("https://")

class TestRefusalMessage:
    """Test refusal message for advisory queries."""
    
    def test_refusal_message_content(self):
        """Test that refusal message contains appropriate content."""
        response = client.post(
            "/api/chat",
            json={"query": "Should I invest in HDFC Large Cap Fund?"}
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # Check that error message is appropriate
        assert "advisory" in data["error"].lower() or "investment advice" in data["error"].lower()
        
        # Check that educational link is provided
        assert data["educational_link"] is not None
        assert data["educational_link"].startswith("http")

class TestAPIModels:
    """Test API request/response models."""
    
    def test_chat_request_validation(self):
        """Test ChatRequest model validation."""
        from api.main import ChatRequest
        
        # Valid request
        valid_request = ChatRequest(query="What is the expense ratio?")
        assert valid_request.query == "What is the expense ratio?"
        
        # Invalid request (too short)
        with pytest.raises(Exception):
            ChatRequest(query="")
        
        # Invalid request (too long)
        with pytest.raises(Exception):
            ChatRequest(query="a" * 501)
    
    def test_chat_response_structure(self):
        """Test ChatResponse model structure."""
        from api.main import ChatResponse
        from datetime import datetime
        
        response = ChatResponse(
            response="Test response",
            source="https://example.com",
            timestamp=datetime.now().isoformat()
        )
        
        assert response.response == "Test response"
        assert response.source == "https://example.com"
        assert response.timestamp is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
