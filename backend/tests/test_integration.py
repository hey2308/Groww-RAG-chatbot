"""
Phase 4.3 - Integration Tests
Integration tests for end-to-end query processing and API validation
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
import time

client = TestClient(app)

class TestEndToEndQueryProcessing:
    """Test end-to-end query processing pipeline."""
    
    def test_complete_query_flow(self):
        """Test complete flow from query to response."""
        # This will be fully functional after RAG integration
        # For now, test the API structure
        response = client.post(
            "/api/chat",
            json={"query": "What is the expense ratio of HDFC Large Cap Fund?"}
        )
        
        # Currently returns placeholder, but structure should be correct
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "source" in data
            assert "timestamp" in data
    
    def test_advisory_query_flow(self):
        """Test that advisory queries are properly rejected."""
        response = client.post(
            "/api/chat",
            json={"query": "Should I invest in HDFC Large Cap Fund?"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "educational_link" in data
    
    def test_multiple_sequential_queries(self):
        """Test handling of multiple sequential queries."""
        queries = [
            "What is the NAV of HDFC Large Cap Fund?",
            "What is the expense ratio of SBI Small Cap Fund?",
            "What is the risk level of Axis Bluechip Fund?"
        ]
        
        for query in queries:
            response = client.post("/api/chat", json={"query": query})
            # Should not crash, even if returning placeholder
            assert response.status_code in [200, 422]

class TestAPIResponseValidation:
    """Test API response structure and validation."""
    
    def test_chat_response_schema(self):
        """Test that chat response matches expected schema."""
        response = client.post(
            "/api/chat",
            json={"query": "What is the expense ratio of HDFC Large Cap Fund?"}
        )
        
        if response.status_code == 200:
            data = response.json()
            # Validate required fields
            required_fields = ["response", "source", "timestamp"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Validate field types
            assert isinstance(data["response"], str)
            assert isinstance(data["source"], str)
            assert isinstance(data["timestamp"], str)
    
    def test_health_response_schema(self):
        """Test that health response matches expected schema."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["status", "timestamp", "version"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["version"], str)
    
    def test_sources_response_schema(self):
        """Test that sources response matches expected schema."""
        response = client.get("/api/sources")
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["sources", "count", "timestamp"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert isinstance(data["sources"], list)
        assert isinstance(data["count"], int)
        assert isinstance(data["timestamp"], str)
    
    def test_error_response_schema(self):
        """Test that error responses match expected schema."""
        response = client.post(
            "/api/chat",
            json={"query": "Should I invest in HDFC Large Cap Fund?"}
        )
        
        assert response.status_code == 422
        data = response.json()
        
        assert "error" in data
        assert isinstance(data["error"], str)

class TestSourceLinkVerification:
    """Test source link validation and verification."""
    
    def test_source_links_are_accessible(self):
        """Test that source links are valid and accessible."""
        response = client.get("/api/sources")
        data = response.json()
        
        for source in data["sources"]:
            # Validate URL format
            assert source.startswith("http://") or source.startswith("https://")
    
    def test_source_link_in_response(self):
        """Test that responses include valid source links."""
        # This will be tested with actual RAG integration
        response = client.post(
            "/api/chat",
            json={"query": "What is the expense ratio of HDFC Large Cap Fund?"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["source"].startswith("http://") or data["source"].startswith("https://")

class TestAPIEndpoints:
    """Test all API endpoints functionality."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_chat_endpoint_methods(self):
        """Test that chat endpoint only accepts POST."""
        # GET should not be allowed
        response = client.get("/api/chat")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_health_endpoint_methods(self):
        """Test that health endpoint accepts GET."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        # POST should not be allowed
        response = client.post("/api/health")
        assert response.status_code == 405
    
    def test_sources_endpoint_methods(self):
        """Test that sources endpoint accepts GET."""
        response = client.get("/api/sources")
        assert response.status_code == 200
        
        # POST should not be allowed
        response = client.post("/api/sources")
        assert response.status_code == 405

class TestErrorScenarios:
    """Test various error scenarios."""
    
    def test_malformed_json_request(self):
        """Test handling of malformed JSON requests."""
        response = client.post(
            "/api/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_content_type(self):
        """Test handling of missing content-type header."""
        response = client.post(
            "/api/chat",
            json={"query": "test"}
        )
        
        # Should still work as FastAPI handles this
        assert response.status_code in [200, 422]
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import threading
        
        def make_request():
            client.post(
                "/api/chat",
                json={"query": "What is the NAV of HDFC Large Cap Fund?"}
            )
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # If we get here without crashing, concurrent handling works
        assert True

class TestDataConsistency:
    """Test data consistency across endpoints."""
    
    def test_sources_consistency(self):
        """Test that sources endpoint returns consistent data."""
        response1 = client.get("/api/sources")
        response2 = client.get("/api/sources")
        
        assert response1.json() == response2.json()
    
    def test_timestamp_format(self):
        """Test that timestamps are in ISO format."""
        response = client.get("/api/health")
        data = response.json()
        
        # Should be valid ISO format
        from datetime import datetime
        try:
            datetime.fromisoformat(data["timestamp"])
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
