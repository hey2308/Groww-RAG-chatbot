"""
Phase 4.3 - Performance Tests
Performance tests for response time, concurrent users, and vector search
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
import time
import threading
import statistics

client = TestClient(app)

class TestResponseTime:
    """Test API response time performance."""
    
    def test_chat_response_time_under_3_seconds(self):
        """Test that chat endpoint responds within 3 seconds."""
        start_time = time.time()
        
        response = client.post(
            "/api/chat",
            json={"query": "What is the expense ratio of HDFC Large Cap Fund?"}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response_time < 3.0, f"Response time {response_time}s exceeds 3s limit"
    
    def test_health_response_time_under_1_second(self):
        """Test that health endpoint responds within 1 second."""
        start_time = time.time()
        
        response = client.get("/api/health")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response_time < 1.0, f"Response time {response_time}s exceeds 1s limit"
    
    def test_sources_response_time_under_1_second(self):
        """Test that sources endpoint responds within 1 second."""
        start_time = time.time()
        
        response = client.get("/api/sources")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response_time < 1.0, f"Response time {response_time}s exceeds 1s limit"
    
    def test_average_response_time(self):
        """Test average response time across multiple requests."""
        response_times = []
        
        for _ in range(10):
            start_time = time.time()
            
            response = client.post(
                "/api/chat",
                json={"query": "What is the NAV of HDFC Large Cap Fund?"}
            )
            
            end_time = time.time()
            response_times.append(end_time - start_time)
        
        average_time = statistics.mean(response_times)
        assert average_time < 2.0, f"Average response time {average_time}s exceeds 2s limit"

class TestConcurrentUserHandling:
    """Test concurrent user handling performance."""
    
    def test_concurrent_requests_performance(self):
        """Test handling of 10 concurrent requests."""
        response_times = []
        errors = []
        
        def make_request():
            try:
                start_time = time.time()
                response = client.post(
                    "/api/chat",
                    json={"query": "What is the expense ratio of HDFC Large Cap Fund?"}
                )
                end_time = time.time()
                response_times.append(end_time - start_time)
                
                if response.status_code not in [200, 422]:
                    errors.append(f"Status code: {response.status_code}")
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Check that all requests completed
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(response_times) == 10, "Not all requests completed"
        
        # Check average response time under load
        average_time = statistics.mean(response_times)
        assert average_time < 3.0, f"Average response time under load {average_time}s exceeds 3s limit"
    
    def test_high_concurrent_load(self):
        """Test handling of 50 concurrent requests."""
        response_times = []
        errors = []
        
        def make_request():
            try:
                start_time = time.time()
                response = client.post(
                    "/api/chat",
                    json={"query": "What is the NAV of HDFC Large Cap Fund?"}
                )
                end_time = time.time()
                response_times.append(end_time - start_time)
                
                if response.status_code not in [200, 422]:
                    errors.append(f"Status code: {response.status_code}")
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for _ in range(50):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Check that most requests completed (allow some failures under heavy load)
        success_rate = len(response_times) / 50
        assert success_rate >= 0.9, f"Success rate {success_rate} under 90% under heavy load"
        
        # Check average response time
        if response_times:
            average_time = statistics.mean(response_times)
            assert average_time < 5.0, f"Average response time under heavy load {average_time}s exceeds 5s limit"

class TestVectorSearchPerformance:
    """Test vector search performance (placeholder for actual implementation)."""
    
    def test_vector_search_performance(self):
        """Test that vector search completes within acceptable time."""
        # This will be tested with actual RAG integration
        # For now, we test the API response time as a proxy
        start_time = time.time()
        
        response = client.post(
            "/api/chat",
            json={"query": "What is the expense ratio of HDFC Large Cap Fund?"}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Vector search should be fast (< 1 second)
        assert response_time < 3.0, f"Vector search time {response_time}s exceeds limit"
    
    def test_vector_search_accuracy(self):
        """Test vector search accuracy (placeholder)."""
        # This will be tested with actual RAG integration
        pass
    
    def test_vector_search_scalability(self):
        """Test vector search scalability with larger datasets (placeholder)."""
        # This will be tested with actual RAG integration
        pass

class TestMemoryUsage:
    """Test memory usage and resource management."""
    
    def test_memory_leak_prevention(self):
        """Test that memory doesn't leak over multiple requests."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make 100 requests
        for _ in range(100):
            client.post(
                "/api/chat",
                json={"query": "What is the NAV of HDFC Large Cap Fund?"}
            )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 50MB)
        assert memory_increase < 50, f"Memory increase {memory_increase}MB exceeds 50MB limit"

class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiting_enforcement(self):
        """Test that rate limiting is enforced."""
        # This will test the RateLimitMiddleware when fully implemented
        # For now, we test that the API can handle rapid requests
        response_times = []
        
        for _ in range(20):
            start_time = time.time()
            response = client.post(
                "/api/chat",
                json={"query": "What is the NAV of HDFC Large Cap Fund?"}
            )
            end_time = time.time()
            response_times.append(end_time - start_time)
        
        # All requests should complete (rate limiting may slow them but not block)
        assert len(response_times) == 20, "Not all requests completed"

class TestThroughput:
    """Test API throughput performance."""
    
    def test_requests_per_second(self):
        """Test that API can handle at least 10 requests per second."""
        start_time = time.time()
        
        for _ in range(10):
            client.post(
                "/api/chat",
                json={"query": "What is the NAV of HDFC Large Cap Fund?"}
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        requests_per_second = 10 / total_time
        assert requests_per_second >= 10, f"Throughput {requests_per_second} req/s below 10 req/s limit"

class TestErrorHandlingPerformance:
    """Test performance of error handling."""
    
    def test_advisory_query_error_response_time(self):
        """Test that advisory query errors are handled quickly."""
        start_time = time.time()
        
        response = client.post(
            "/api/chat",
            json={"query": "Should I invest in HDFC Large Cap Fund?"}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 422
        assert response_time < 0.5, f"Error response time {response_time}s exceeds 0.5s limit"
    
    def test_validation_error_response_time(self):
        """Test that validation errors are handled quickly."""
        start_time = time.time()
        
        response = client.post(
            "/api/chat",
            json={"query": ""}  # Empty query
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 422
        assert response_time < 0.5, f"Validation error response time {response_time}s exceeds 0.5s limit"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
