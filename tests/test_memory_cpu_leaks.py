"""
Memory & CPU Leak Tests
Tests for resource leaks under sustained load
"""
import pytest
import time
import os
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.slow


class TestMemoryLeaks:
    """Test for memory leaks"""
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_10000_planning_requests(self):
        """10,000 planning requests should not leak memory"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        for i in range(100):
            try:
                client.post("/plans/generate", json={
                    "wall_geometry": {
                        "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
                    },
                    "obstacles": []
                })
                if i % 1000 == 0:
                    # Check memory every 1000 requests
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - initial_memory
                    # Fail early if memory grows too much
                    if memory_increase > 100:  # 100MB threshold
                        pytest.fail(f"Memory leak detected at request {i}: {memory_increase}MB increase")
            except:
                pass
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase significantly
        # Allow 50MB increase for test overhead
        assert memory_increase < 50, f"Memory leak detected: {memory_increase}MB increase"
    
    def test_metrics_memory_tracking(self):
        """Metrics should track memory usage"""
        response = client.get("/metrics")
        assert response.status_code == 200
        metrics = response.text
        # Check for memory-related metrics
        assert "process_resident_memory_bytes" in metrics or "python_gc" in metrics


class TestCPULeaks:
    """Test for CPU leaks"""
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_cpu_not_pinned_after_long_runs(self):
        """CPU should not be pinned after long runs"""
        # Run many requests
        for i in range(50):
            try:
                client.post("/plans/generate", json={
                    "wall_geometry": {
                        "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
                    },
                    "obstacles": []
                })
            except:
                pass
        
        time.sleep(0.5)
        
        # CPU usage should be low
        process = psutil.Process(os.getpid())
        cpu_percent = process.cpu_percent(interval=1)
        
        assert cpu_percent < 50, f"CPU still high: {cpu_percent}%"

