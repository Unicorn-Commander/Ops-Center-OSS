"""
Performance tests for LLM Routing Engine.

Tests routing latency, concurrent request handling, cache performance,
and database query optimization.
"""
import pytest
import asyncio
import time
from datetime import datetime
import statistics
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from modules.llm_routing_engine import LLMRoutingEngine
from tests.fixtures.llm_test_data import MOCK_PROVIDERS


class TestRoutingLatency:
    """Test routing engine performance."""

    @pytest.fixture
    def routing_engine(self, mock_db_session):
        """Initialize routing engine."""
        return LLMRoutingEngine(db_session=mock_db_session)

    @pytest.fixture
    def perf_results(self):
        """Store performance test results."""
        return {
            "routing_latency": [],
            "concurrent_throughput": [],
            "cache_performance": [],
            "db_query_times": []
        }

    # Test: Routing Decision Latency
    @pytest.mark.asyncio
    async def test_routing_latency_single_decision(self, routing_engine, perf_results):
        """Test latency of single routing decision."""
        latencies = []

        for _ in range(100):
            start_time = time.perf_counter()

            await routing_engine.select_model(
                power_level="balanced",
                user_id="user-123",
                providers=MOCK_PROVIDERS
            )

            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

        avg_latency = statistics.mean(latencies)
        p50_latency = statistics.median(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]

        perf_results["routing_latency"] = {
            "avg": avg_latency,
            "p50": p50_latency,
            "p95": p95_latency,
            "p99": p99_latency,
            "min": min(latencies),
            "max": max(latencies)
        }

        print(f"\n=== Routing Latency (100 decisions) ===")
        print(f"Average: {avg_latency:.2f}ms")
        print(f"P50: {p50_latency:.2f}ms")
        print(f"P95: {p95_latency:.2f}ms")
        print(f"P99: {p99_latency:.2f}ms")

        # Performance assertions
        assert avg_latency < 100, f"Average latency {avg_latency:.2f}ms exceeds 100ms threshold"
        assert p95_latency < 200, f"P95 latency {p95_latency:.2f}ms exceeds 200ms threshold"

    @pytest.mark.asyncio
    async def test_routing_latency_by_power_level(self, routing_engine):
        """Test if routing latency varies by power level."""
        results = {}

        for power_level in ["eco", "balanced", "precision"]:
            latencies = []

            for _ in range(50):
                start_time = time.perf_counter()

                await routing_engine.select_model(
                    power_level=power_level,
                    user_id="user-123",
                    providers=MOCK_PROVIDERS
                )

                latency_ms = (time.perf_counter() - start_time) * 1000
                latencies.append(latency_ms)

            results[power_level] = statistics.mean(latencies)

        print(f"\n=== Routing Latency by Power Level ===")
        for level, latency in results.items():
            print(f"{level.capitalize()}: {latency:.2f}ms")

        # All power levels should have similar latency
        assert all(lat < 150 for lat in results.values())

    # Test: Concurrent Request Handling
    @pytest.mark.asyncio
    async def test_concurrent_throughput(self, routing_engine, perf_results):
        """Test system throughput with concurrent requests."""
        concurrent_levels = [10, 50, 100, 200]
        results = {}

        for concurrency in concurrent_levels:
            start_time = time.perf_counter()

            tasks = [
                routing_engine.select_model(
                    power_level="balanced",
                    user_id=f"user-{i}",
                    providers=MOCK_PROVIDERS
                )
                for i in range(concurrency)
            ]

            await asyncio.gather(*tasks)

            end_time = time.perf_counter()
            duration = end_time - start_time
            throughput = concurrency / duration

            results[concurrency] = {
                "duration": duration,
                "throughput": throughput
            }

        perf_results["concurrent_throughput"] = results

        print(f"\n=== Concurrent Request Throughput ===")
        for concurrency, data in results.items():
            print(f"{concurrency} concurrent: {data['throughput']:.2f} req/sec ({data['duration']:.3f}s total)")

        # Should handle at least 100 requests/sec
        assert results[100]["throughput"] > 100, "Throughput below 100 req/sec"

    @pytest.mark.asyncio
    async def test_sustained_load(self, routing_engine):
        """Test performance under sustained load."""
        duration_seconds = 10
        requests_per_second = 100

        start_time = time.perf_counter()
        total_requests = 0
        errors = 0

        while time.perf_counter() - start_time < duration_seconds:
            batch_start = time.perf_counter()

            tasks = [
                routing_engine.select_model(
                    power_level="balanced",
                    user_id=f"user-{i}",
                    providers=MOCK_PROVIDERS
                )
                for i in range(requests_per_second)
            ]

            try:
                await asyncio.gather(*tasks)
                total_requests += requests_per_second
            except Exception:
                errors += 1

            # Sleep to maintain rate
            elapsed = time.perf_counter() - batch_start
            if elapsed < 1.0:
                await asyncio.sleep(1.0 - elapsed)

        total_duration = time.perf_counter() - start_time
        actual_throughput = total_requests / total_duration

        print(f"\n=== Sustained Load Test ({duration_seconds}s) ===")
        print(f"Total requests: {total_requests}")
        print(f"Errors: {errors}")
        print(f"Avg throughput: {actual_throughput:.2f} req/sec")

        assert errors == 0, f"Had {errors} errors during sustained load"
        assert actual_throughput > 80, f"Throughput {actual_throughput:.2f} below target"

    # Test: Cache Performance
    @pytest.mark.asyncio
    async def test_byok_cache_performance(self, routing_engine, perf_results):
        """Test BYOK key caching improves performance."""
        from modules.byok_manager import BYOKManager
        from unittest.mock import MagicMock

        mock_keycloak = MagicMock()
        byok_manager = BYOKManager(keycloak_admin=mock_keycloak)

        user_id = "user-123"
        provider_id = "provider-1"

        # Mock Keycloak response
        encrypted_key = byok_manager.encrypt_key("sk-test-key")
        mock_keycloak.get_user.return_value = {
            "id": user_id,
            "attributes": {
                "llm_api_keys": [
                    {
                        "key_id": "key-1",
                        "provider_id": provider_id,
                        "encrypted_key": encrypted_key,
                        "is_active": True
                    }
                ]
            }
        }

        # First call (cold cache)
        cold_start = time.perf_counter()
        await byok_manager.get_user_key(user_id, provider_id)
        cold_time = (time.perf_counter() - cold_start) * 1000

        # Subsequent calls (warm cache)
        warm_times = []
        for _ in range(100):
            warm_start = time.perf_counter()
            await byok_manager.get_user_key(user_id, provider_id)
            warm_time = (time.perf_counter() - warm_start) * 1000
            warm_times.append(warm_time)

        avg_warm_time = statistics.mean(warm_times)

        perf_results["cache_performance"] = {
            "cold_cache_ms": cold_time,
            "warm_cache_avg_ms": avg_warm_time,
            "speedup": cold_time / avg_warm_time if avg_warm_time > 0 else 0
        }

        print(f"\n=== BYOK Cache Performance ===")
        print(f"Cold cache: {cold_time:.2f}ms")
        print(f"Warm cache (avg): {avg_warm_time:.2f}ms")
        print(f"Speedup: {cold_time / avg_warm_time if avg_warm_time > 0 else 0:.1f}x")

        # Cache should provide at least 2x speedup
        if avg_warm_time > 0:
            assert cold_time / avg_warm_time > 2, "Cache not providing sufficient speedup"

    # Test: Database Query Performance
    @pytest.mark.asyncio
    async def test_provider_query_performance(self, mock_db_session, perf_results):
        """Test database query performance for provider lookups."""
        mock_db_session.query().filter().all.return_value = MOCK_PROVIDERS

        query_times = []

        for _ in range(100):
            start_time = time.perf_counter()

            # Simulate provider query
            mock_db_session.query().filter().all()

            query_time = (time.perf_counter() - start_time) * 1000
            query_times.append(query_time)

        avg_query_time = statistics.mean(query_times)
        p95_query_time = sorted(query_times)[int(len(query_times) * 0.95)]

        perf_results["db_query_times"] = {
            "avg": avg_query_time,
            "p95": p95_query_time,
            "p99": sorted(query_times)[int(len(query_times) * 0.99)]
        }

        print(f"\n=== Database Query Performance ===")
        print(f"Average: {avg_query_time:.2f}ms")
        print(f"P95: {p95_query_time:.2f}ms")

        # Database queries should be very fast
        assert avg_query_time < 50, f"Average query time {avg_query_time:.2f}ms too slow"

    @pytest.mark.asyncio
    async def test_usage_logging_performance(self, routing_engine, mock_db_session):
        """Test performance impact of usage logging."""
        from modules.llm_routing_engine import RoutingDecision

        decision = RoutingDecision(
            provider_id="provider-1",
            provider_name="OpenAI",
            provider_type="openai",
            model_id="gpt-4o",
            power_level="balanced",
            cost_per_1k_tokens=0.005,
            used_byok=False
        )

        log_times = []

        for i in range(100):
            start_time = time.perf_counter()

            await routing_engine.log_usage(
                user_id=f"user-{i}",
                decision=decision,
                prompt_tokens=100,
                completion_tokens=200,
                latency_ms=500,
                status="success"
            )

            log_time = (time.perf_counter() - start_time) * 1000
            log_times.append(log_time)

        avg_log_time = statistics.mean(log_times)

        print(f"\n=== Usage Logging Performance ===")
        print(f"Average: {avg_log_time:.2f}ms")
        print(f"P95: {sorted(log_times)[95]:.2f}ms")

        # Logging should not add significant latency
        assert avg_log_time < 100, f"Logging latency {avg_log_time:.2f}ms too high"

    # Test: Memory Usage
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, routing_engine):
        """Test memory usage under load."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Generate load
        tasks = [
            routing_engine.select_model(
                power_level="balanced",
                user_id=f"user-{i}",
                providers=MOCK_PROVIDERS
            )
            for i in range(1000)
        ]

        await asyncio.gather(*tasks)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"\n=== Memory Usage ===")
        print(f"Initial: {initial_memory:.2f} MB")
        print(f"Final: {final_memory:.2f} MB")
        print(f"Increase: {memory_increase:.2f} MB")

        # Memory increase should be reasonable (<50MB for 1000 requests)
        assert memory_increase < 50, f"Memory increase {memory_increase:.2f}MB too high"

    # Test: End-to-End Latency
    @pytest.mark.asyncio
    async def test_end_to_end_request_latency(self, routing_engine, mock_db_session):
        """Test complete end-to-end request latency."""
        from modules.llm_routing_engine import RoutingDecision

        e2e_times = []

        for i in range(50):
            start_time = time.perf_counter()

            # 1. Select model (routing)
            decision = await routing_engine.select_model(
                power_level="balanced",
                user_id=f"user-{i}",
                providers=MOCK_PROVIDERS
            )

            # 2. Simulate LLM call (mock)
            await asyncio.sleep(0.5)  # Simulate 500ms LLM response

            # 3. Log usage
            await routing_engine.log_usage(
                user_id=f"user-{i}",
                decision=decision,
                prompt_tokens=100,
                completion_tokens=200,
                latency_ms=500,
                status="success"
            )

            e2e_time = (time.perf_counter() - start_time) * 1000
            e2e_times.append(e2e_time)

        avg_e2e = statistics.mean(e2e_times)
        overhead = avg_e2e - 500  # Subtract simulated LLM time

        print(f"\n=== End-to-End Latency ===")
        print(f"Average E2E: {avg_e2e:.2f}ms")
        print(f"Average overhead: {overhead:.2f}ms")
        print(f"Overhead %: {(overhead / avg_e2e * 100):.1f}%")

        # Routing + logging overhead should be minimal (<10% of total)
        assert overhead < 100, f"System overhead {overhead:.2f}ms too high"


def save_performance_report(results: dict):
    """Save performance test results to JSON file."""
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "results": results,
        "summary": {
            "routing_latency_p95": results.get("routing_latency", {}).get("p95"),
            "concurrent_throughput_100": results.get("concurrent_throughput", {}).get(100, {}).get("throughput"),
            "cache_speedup": results.get("cache_performance", {}).get("speedup"),
            "db_query_p95": results.get("db_query_times", {}).get("p95")
        }
    }

    output_path = "/tmp/epic_3_1_performance_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Performance report saved to {output_path}")


# Run tests with: pytest -v -s tests/performance/test_routing_latency.py
# For full report: pytest -v -s tests/performance/test_routing_latency.py --tb=short
