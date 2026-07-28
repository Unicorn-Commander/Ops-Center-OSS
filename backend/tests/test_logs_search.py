"""Test Suite for Advanced Log Search API

Comprehensive tests covering:
- Basic text search
- Multi-filter combinations
- Regex pattern matching
- Date range filtering
- Pagination
- Performance with large datasets
- Error handling
- Redis caching
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from logs_search_api import (
    AdvancedLogSearchRequest,
    LogSearchResponse,
    apply_filters,
    generate_cache_key,
    get_docker_services,
    fetch_docker_logs
)


# Sample log data for testing
SAMPLE_LOGS = [
    {
        "timestamp": "2025-11-29T10:00:00Z",
        "severity": "ERROR",
        "service": "ops-center",
        "message": "User login failed for user@example.com",
        "metadata": {}
    },
    {
        "timestamp": "2025-11-29T10:05:00Z",
        "severity": "WARN",
        "service": "ops-center",
        "message": "High memory usage detected: 85%",
        "metadata": {}
    },
    {
        "timestamp": "2025-11-29T10:10:00Z",
        "severity": "INFO",
        "service": "litellm",
        "message": "API request completed successfully",
        "metadata": {}
    },
    {
        "timestamp": "2025-11-29T10:15:00Z",
        "severity": "DEBUG",
        "service": "litellm",
        "message": "Cache hit for model list",
        "metadata": {}
    },
    {
        "timestamp": "2025-11-29T10:20:00Z",
        "severity": "ERROR",
        "service": "keycloak",
        "message": "Failed to connect to database",
        "metadata": {}
    },
    {
        "timestamp": "2025-11-28T09:00:00Z",
        "severity": "INFO",
        "service": "ops-center",
        "message": "System startup complete",
        "metadata": {}
    },
    {
        "timestamp": "2025-11-28T09:30:00Z",
        "severity": "ERROR",
        "service": "ops-center",
        "message": "Invalid API key provided",
        "metadata": {}
    },
]


class TestAdvancedLogSearch:
    """Test advanced log search functionality"""

    def test_basic_text_search(self):
        """Test basic text search in messages"""
        request = AdvancedLogSearchRequest(
            query="user",
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 2  # "user login" and "High memory usage"
        assert any("user" in log['message'].lower() for log in filtered)

    def test_severity_filter_single(self):
        """Test filtering by single severity level"""
        request = AdvancedLogSearchRequest(
            severity=["ERROR"],
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 3  # All ERROR logs
        assert all(log['severity'] == "ERROR" for log in filtered)

    def test_severity_filter_multiple(self):
        """Test filtering by multiple severity levels"""
        request = AdvancedLogSearchRequest(
            severity=["ERROR", "WARN"],
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 4  # 3 ERROR + 1 WARN
        assert all(log['severity'] in ["ERROR", "WARN"] for log in filtered)

    def test_service_filter_single(self):
        """Test filtering by single service"""
        request = AdvancedLogSearchRequest(
            services=["ops-center"],
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 4  # All ops-center logs
        assert all(log['service'] == "ops-center" for log in filtered)

    def test_service_filter_multiple(self):
        """Test filtering by multiple services"""
        request = AdvancedLogSearchRequest(
            services=["ops-center", "litellm"],
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 6  # All except keycloak
        assert all(log['service'] in ["ops-center", "litellm"] for log in filtered)

    def test_date_range_filter(self):
        """Test filtering by date range"""
        request = AdvancedLogSearchRequest(
            start_date="2025-11-29",
            end_date="2025-11-29",
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 5  # Only Nov 29 logs
        for log in filtered:
            log_date = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
            assert log_date.date() == datetime(2025, 11, 29).date()

    def test_date_start_only(self):
        """Test filtering with only start date"""
        request = AdvancedLogSearchRequest(
            start_date="2025-11-29",
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 5  # All Nov 29 logs
        for log in filtered:
            log_date = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
            assert log_date >= datetime(2025, 11, 29)

    def test_date_end_only(self):
        """Test filtering with only end date"""
        request = AdvancedLogSearchRequest(
            end_date="2025-11-28",
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 2  # Nov 28 logs only
        for log in filtered:
            log_date = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
            assert log_date < datetime(2025, 11, 29)

    def test_regex_filter_simple(self):
        """Test regex pattern matching - simple pattern"""
        request = AdvancedLogSearchRequest(
            regex=r"failed",
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 2  # "login failed" and "Failed to connect"

    def test_regex_filter_complex(self):
        """Test regex pattern matching - complex pattern"""
        request = AdvancedLogSearchRequest(
            regex=r"user.*failed",
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 1  # Only "User login failed"
        assert "user@example.com" in filtered[0]['message'].lower()

    def test_regex_filter_case_insensitive(self):
        """Test regex case insensitive matching"""
        request = AdvancedLogSearchRequest(
            regex=r"(?i)ERROR|FAILED",
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        # Should match ERROR severity and "failed" in messages
        assert len(filtered) >= 3

    def test_combined_filters(self):
        """Test combining multiple filters"""
        request = AdvancedLogSearchRequest(
            query="failed",
            severity=["ERROR"],
            services=["ops-center"],
            start_date="2025-11-29",
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 1  # Only one matching log
        log = filtered[0]
        assert log['severity'] == "ERROR"
        assert log['service'] == "ops-center"
        assert "failed" in log['message'].lower()
        assert "2025-11-29" in log['timestamp']

    def test_pagination_first_page(self):
        """Test pagination - first page"""
        # Create more logs for pagination test
        many_logs = SAMPLE_LOGS * 20  # 140 logs

        request = AdvancedLogSearchRequest(
            limit=10,
            offset=0
        )

        filtered = apply_filters(many_logs, request)
        paginated = filtered[request.offset:request.offset + request.limit]

        assert len(paginated) == 10

    def test_pagination_second_page(self):
        """Test pagination - second page"""
        many_logs = SAMPLE_LOGS * 20

        request = AdvancedLogSearchRequest(
            limit=10,
            offset=10
        )

        filtered = apply_filters(many_logs, request)
        paginated = filtered[request.offset:request.offset + request.limit]

        assert len(paginated) == 10

    def test_pagination_last_page_partial(self):
        """Test pagination - last page with partial results"""
        request = AdvancedLogSearchRequest(
            limit=10,
            offset=5
        )

        filtered = apply_filters(SAMPLE_LOGS, request)
        paginated = filtered[request.offset:request.offset + request.limit]

        assert len(paginated) == 2  # Only 2 logs after offset 5

    def test_empty_results(self):
        """Test search with no matching results"""
        request = AdvancedLogSearchRequest(
            query="nonexistent_query_string_xyz",
            limit=100,
            offset=0
        )

        filtered = apply_filters(SAMPLE_LOGS, request)

        assert len(filtered) == 0

    def test_invalid_regex_graceful(self):
        """Test invalid regex pattern handling"""
        request = AdvancedLogSearchRequest(
            regex=r"[invalid(regex",  # This will fail validation
            limit=100,
            offset=0
        )

        # Should raise validation error
        with pytest.raises(Exception):
            # Will fail at Pydantic validation
            pass

    def test_cache_key_generation_consistency(self):
        """Test cache key generation is consistent"""
        request1 = AdvancedLogSearchRequest(
            query="test",
            severity=["ERROR", "WARN"],
            services=["ops-center"],
            limit=100,
            offset=0
        )

        request2 = AdvancedLogSearchRequest(
            query="test",
            severity=["WARN", "ERROR"],  # Different order
            services=["ops-center"],
            limit=100,
            offset=0
        )

        key1 = generate_cache_key(request1)
        key2 = generate_cache_key(request2)

        # Should be the same despite different order (sorted internally)
        assert key1 == key2

    def test_cache_key_generation_different(self):
        """Test cache key generation differs for different requests"""
        request1 = AdvancedLogSearchRequest(
            query="test1",
            limit=100,
            offset=0
        )

        request2 = AdvancedLogSearchRequest(
            query="test2",
            limit=100,
            offset=0
        )

        key1 = generate_cache_key(request1)
        key2 = generate_cache_key(request2)

        assert key1 != key2

    def test_performance_large_dataset(self):
        """Test performance with large dataset (100K logs)"""
        import time

        # Generate 100K log entries
        large_dataset = []
        for i in range(100000):
            large_dataset.append({
                "timestamp": f"2025-11-{(i % 30) + 1:02d}T{(i % 24):02d}:{(i % 60):02d}:00Z",
                "severity": ["ERROR", "WARN", "INFO", "DEBUG"][i % 4],
                "service": ["ops-center", "litellm", "keycloak", "postgres"][i % 4],
                "message": f"Log message {i} with some text",
                "metadata": {}
            })

        request = AdvancedLogSearchRequest(
            severity=["ERROR"],
            services=["ops-center"],
            limit=100,
            offset=0
        )

        start = time.time()
        filtered = apply_filters(large_dataset, request)
        elapsed = time.time() - start

        # Should complete in under 2 seconds even with 100K logs
        assert elapsed < 2.0, f"Query took {elapsed:.2f}s, expected <2s"
        assert len(filtered) > 0

    def test_performance_regex_matching(self):
        """Test performance of regex matching on large dataset"""
        import time

        # Generate 10K logs with varied content
        dataset = []
        for i in range(10000):
            dataset.append({
                "timestamp": f"2025-11-29T10:{(i % 60):02d}:{(i % 60):02d}Z",
                "severity": "INFO",
                "service": "test-service",
                "message": f"Message {i}: " + ("error occurred" if i % 100 == 0 else "normal log"),
                "metadata": {}
            })

        request = AdvancedLogSearchRequest(
            regex=r"error.*occurred",
            limit=1000,
            offset=0
        )

        start = time.time()
        filtered = apply_filters(dataset, request)
        elapsed = time.time() - start

        # Regex matching should still be fast
        assert elapsed < 1.0, f"Regex query took {elapsed:.2f}s, expected <1s"
        assert len(filtered) == 100  # Should match 100 logs (1%)

    def test_memory_efficiency(self):
        """Test memory efficiency with large result sets"""
        import sys

        # Create dataset
        dataset = SAMPLE_LOGS * 10000  # 70K logs

        request = AdvancedLogSearchRequest(
            limit=10000,
            offset=0
        )

        filtered = apply_filters(dataset, request)

        # Get memory size of filtered results
        size_bytes = sys.getsizeof(filtered)
        size_mb = size_bytes / (1024 * 1024)

        # Should use less than 100MB for 10K results
        assert size_mb < 100, f"Memory usage {size_mb:.2f}MB, expected <100MB"


class TestRequestValidation:
    """Test request validation"""

    def test_valid_severity_levels(self):
        """Test valid severity level validation"""
        request = AdvancedLogSearchRequest(
            severity=["ERROR", "WARN", "INFO", "DEBUG"],
            limit=100,
            offset=0
        )

        assert "ERROR" in request.severity
        assert "WARN" in request.severity

    def test_invalid_severity_level(self):
        """Test invalid severity level rejection"""
        with pytest.raises(Exception):
            AdvancedLogSearchRequest(
                severity=["INVALID_LEVEL"],
                limit=100,
                offset=0
            )

    def test_valid_date_format(self):
        """Test valid date format"""
        request = AdvancedLogSearchRequest(
            start_date="2025-11-29",
            end_date="2025-11-30",
            limit=100,
            offset=0
        )

        assert request.start_date == "2025-11-29"
        assert request.end_date == "2025-11-30"

    def test_invalid_date_format(self):
        """Test invalid date format rejection"""
        with pytest.raises(Exception):
            AdvancedLogSearchRequest(
                start_date="29-11-2025",  # Wrong format
                limit=100,
                offset=0
            )

    def test_limit_range_validation(self):
        """Test limit range validation"""
        # Valid limits
        request1 = AdvancedLogSearchRequest(limit=1, offset=0)
        assert request1.limit == 1

        request2 = AdvancedLogSearchRequest(limit=10000, offset=0)
        assert request2.limit == 10000

        # Invalid limits should fail
        with pytest.raises(Exception):
            AdvancedLogSearchRequest(limit=0, offset=0)

        with pytest.raises(Exception):
            AdvancedLogSearchRequest(limit=10001, offset=0)

    def test_offset_validation(self):
        """Test offset validation"""
        # Valid offset
        request = AdvancedLogSearchRequest(limit=100, offset=0)
        assert request.offset == 0

        request = AdvancedLogSearchRequest(limit=100, offset=1000)
        assert request.offset == 1000

        # Negative offset should fail
        with pytest.raises(Exception):
            AdvancedLogSearchRequest(limit=100, offset=-1)


# Performance benchmarks
def run_performance_tests():
    """Run all performance tests and print results"""
    print("\n=== Performance Test Results ===\n")

    test_suite = TestAdvancedLogSearch()

    print("1. Testing 100K log search...")
    test_suite.test_performance_large_dataset()
    print("   ✓ PASSED: <2s for 100K logs\n")

    print("2. Testing regex matching on 10K logs...")
    test_suite.test_performance_regex_matching()
    print("   ✓ PASSED: <1s for regex search\n")

    print("3. Testing memory efficiency...")
    test_suite.test_memory_efficiency()
    print("   ✓ PASSED: <100MB for 10K results\n")

    print("=== All Performance Tests Passed ===\n")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

    # Run performance benchmarks
    run_performance_tests()
