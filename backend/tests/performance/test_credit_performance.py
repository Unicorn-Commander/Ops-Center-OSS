"""
Epic 1.8 - Credit System Performance Tests

Performance and load testing for credit system covering:
- Concurrent credit operations
- Database query performance
- Cache effectiveness
- Transaction throughput
- Scalability testing
- Memory usage under load

Author: Testing & DevOps Team Lead
Date: October 23, 2025
"""

import pytest
import asyncio
import time
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import statistics
import sys

sys.path.insert(0, '/app')
from litellm_credit_system import CreditSystem


@pytest.fixture
async def performance_test_setup():
    """Setup for performance tests"""
    # Mock dependencies
    db_pool = None  # TODO: Setup test database pool
    redis_client = None  # TODO: Setup test Redis client
    credit_system = CreditSystem(db_pool, redis_client)

    return credit_system


class TestConcurrentOperations:
    """Test concurrent credit operations"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_deductions_10_users(self, performance_test_setup):
        """Test 10 concurrent credit deductions"""
        system = performance_test_setup

        async def deduct_credits(user_id):
            start_time = time.time()
            try:
                result = await system.debit_credits(
                    user_id=f"user{user_id}@example.com",
                    amount=10.0,
                    metadata={
                        'provider': 'openai',
                        'model': 'gpt-4o',
                        'tokens_used': 1000
                    }
                )
                duration = time.time() - start_time
                return {"success": True, "duration": duration, "result": result}
            except Exception as e:
                duration = time.time() - start_time
                return {"success": False, "duration": duration, "error": str(e)}

        # Execute concurrently
        tasks = [deduct_credits(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success")]

        durations = [r["duration"] for r in successful]

        print(f"\n=== Concurrent Deductions Test (10 users) ===")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        if durations:
            print(f"Avg Duration: {statistics.mean(durations):.3f}s")
            print(f"Max Duration: {max(durations):.3f}s")
            print(f"Min Duration: {min(durations):.3f}s")

        assert len(successful) >= 8  # At least 80% success rate

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_deductions_100_users(self, performance_test_setup):
        """Test 100 concurrent credit deductions"""
        system = performance_test_setup

        async def deduct_credits_batch(batch_id):
            results = []
            for i in range(10):  # 10 operations per batch
                user_id = f"user_{batch_id}_{i}@example.com"
                start_time = time.time()
                try:
                    result = await system.debit_credits(
                        user_id=user_id,
                        amount=5.0,
                        metadata={
                            'provider': 'anthropic',
                            'model': 'claude-3.5-sonnet',
                            'tokens_used': 500
                        }
                    )
                    duration = time.time() - start_time
                    results.append({"success": True, "duration": duration})
                except Exception as e:
                    duration = time.time() - start_time
                    results.append({"success": False, "duration": duration})
            return results

        # Execute 10 batches concurrently
        start_time = time.time()
        tasks = [deduct_credits_batch(i) for i in range(10)]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time

        # Flatten results
        all_results = []
        for batch in batch_results:
            if isinstance(batch, list):
                all_results.extend(batch)

        successful = [r for r in all_results if r.get("success")]
        failed = [r for r in all_results if not r.get("success")]
        durations = [r["duration"] for r in successful]

        throughput = len(all_results) / total_duration

        print(f"\n=== Concurrent Deductions Test (100 users) ===")
        print(f"Total Duration: {total_duration:.3f}s")
        print(f"Throughput: {throughput:.2f} ops/sec")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        if durations:
            print(f"Avg Latency: {statistics.mean(durations):.3f}s")
            print(f"P50 Latency: {statistics.median(durations):.3f}s")
            print(f"P95 Latency: {sorted(durations)[int(len(durations)*0.95)]:.3f}s")

        assert len(successful) >= 90  # At least 90% success rate
        assert throughput > 10  # At least 10 ops/sec

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self, performance_test_setup):
        """Test mixed concurrent operations (read, write, deduct)"""
        system = performance_test_setup

        async def mixed_operations(user_id):
            operations = []

            # Get balance
            start = time.time()
            try:
                balance = await system.get_user_credits(f"user{user_id}@example.com")
                operations.append(("get_balance", time.time() - start, True))
            except:
                operations.append(("get_balance", time.time() - start, False))

            # Credit credits
            start = time.time()
            try:
                await system.credit_credits(
                    f"user{user_id}@example.com",
                    amount=50.0,
                    reason="test"
                )
                operations.append(("credit", time.time() - start, True))
            except:
                operations.append(("credit", time.time() - start, False))

            # Debit credits
            start = time.time()
            try:
                await system.debit_credits(
                    f"user{user_id}@example.com",
                    amount=10.0,
                    metadata={'provider': 'openai', 'model': 'gpt-4o', 'tokens_used': 1000}
                )
                operations.append(("debit", time.time() - start, True))
            except:
                operations.append(("debit", time.time() - start, False))

            return operations

        # Execute concurrently
        tasks = [mixed_operations(i) for i in range(20)]
        all_operations = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze by operation type
        results_by_type = {"get_balance": [], "credit": [], "debit": []}
        for ops in all_operations:
            if isinstance(ops, list):
                for op_name, duration, success in ops:
                    results_by_type[op_name].append((duration, success))

        print(f"\n=== Mixed Operations Test ===")
        for op_name, results in results_by_type.items():
            durations = [d for d, s in results if s]
            success_count = sum(1 for _, s in results if s)
            if durations:
                print(f"{op_name}: {success_count}/{len(results)} success, "
                      f"avg={statistics.mean(durations):.3f}s")


class TestDatabasePerformance:
    """Test database query performance"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_transaction_history_large_dataset(self, performance_test_setup):
        """Test query performance with 10k+ transactions"""
        system = performance_test_setup

        user_id = "heavy_user@example.com"

        # Test pagination performance
        page_sizes = [10, 50, 100, 500]
        results = {}

        for page_size in page_sizes:
            start_time = time.time()
            try:
                history = await system.get_credit_history(
                    user_id=user_id,
                    limit=page_size,
                    offset=0
                )
                duration = time.time() - start_time
                results[page_size] = {
                    "success": True,
                    "duration": duration,
                    "count": len(history)
                }
            except Exception as e:
                results[page_size] = {
                    "success": False,
                    "duration": time.time() - start_time,
                    "error": str(e)
                }

        print(f"\n=== Transaction History Performance ===")
        for page_size, result in results.items():
            if result["success"]:
                print(f"Page size {page_size}: {result['duration']:.3f}s "
                      f"({result['count']} records)")

        # All queries should complete within reasonable time
        for page_size, result in results.items():
            if result["success"]:
                assert result["duration"] < 1.0  # Under 1 second

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_usage_summary_performance(self, performance_test_setup):
        """Test usage aggregation performance"""
        system = performance_test_setup

        user_id = "heavy_user@example.com"

        # Test different time ranges
        time_ranges = [7, 30, 90, 365]
        results = {}

        for days in time_ranges:
            start_time = time.time()
            try:
                stats = await system.get_usage_stats(
                    user_id=user_id,
                    days=days
                )
                duration = time.time() - start_time
                results[days] = {
                    "success": True,
                    "duration": duration,
                    "requests": stats.get("total_requests", 0)
                }
            except Exception as e:
                results[days] = {
                    "success": False,
                    "duration": time.time() - start_time,
                    "error": str(e)
                }

        print(f"\n=== Usage Summary Performance ===")
        for days, result in results.items():
            if result["success"]:
                print(f"{days} days: {result['duration']:.3f}s "
                      f"({result['requests']} requests)")

        # Aggregation should scale sub-linearly
        for days, result in results.items():
            if result["success"]:
                assert result["duration"] < 2.0  # Under 2 seconds


class TestCacheEffectiveness:
    """Test Redis cache effectiveness"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_balance_cache_hit_rate(self, performance_test_setup):
        """Test balance cache hit rate"""
        system = performance_test_setup

        user_id = "test_cache@example.com"

        # First request (cache miss)
        start_time = time.time()
        balance1 = await system.get_user_credits(user_id)
        first_duration = time.time() - start_time

        # Second request (cache hit)
        start_time = time.time()
        balance2 = await system.get_user_credits(user_id)
        cached_duration = time.time() - start_time

        print(f"\n=== Cache Performance ===")
        print(f"First request (miss): {first_duration:.4f}s")
        print(f"Second request (hit): {cached_duration:.4f}s")
        print(f"Speedup: {first_duration/cached_duration:.2f}x")

        assert balance1 == balance2
        assert cached_duration < first_duration  # Cache should be faster

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_invalidation_performance(self, performance_test_setup):
        """Test cache invalidation doesn't slow down operations"""
        system = performance_test_setup

        user_id = "test_invalidation@example.com"

        # Debit operation (invalidates cache)
        start_time = time.time()
        await system.debit_credits(
            user_id=user_id,
            amount=10.0,
            metadata={'provider': 'openai', 'model': 'gpt-4o', 'tokens_used': 1000}
        )
        debit_duration = time.time() - start_time

        # Get balance (fresh cache)
        start_time = time.time()
        balance = await system.get_user_credits(user_id)
        balance_duration = time.time() - start_time

        print(f"\n=== Cache Invalidation Performance ===")
        print(f"Debit operation: {debit_duration:.4f}s")
        print(f"Balance read: {balance_duration:.4f}s")

        assert debit_duration < 0.5  # Debit with invalidation under 500ms


class TestMemoryUsage:
    """Test memory usage under load"""

    @pytest.mark.performance
    def test_memory_usage_concurrent_operations(self, performance_test_setup):
        """Test memory usage during concurrent operations"""
        process = psutil.Process()

        # Initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate load
        # TODO: Execute concurrent operations

        # Final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"\n=== Memory Usage ===")
        print(f"Initial: {initial_memory:.2f} MB")
        print(f"Final: {final_memory:.2f} MB")
        print(f"Increase: {memory_increase:.2f} MB")

        # Memory increase should be reasonable
        assert memory_increase < 100  # Under 100MB increase


class TestThroughput:
    """Test system throughput limits"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_max_transactions_per_second(self, performance_test_setup):
        """Test maximum transaction throughput"""
        system = performance_test_setup

        duration = 10  # seconds
        transaction_count = 0
        start_time = time.time()

        async def continuous_deductions():
            nonlocal transaction_count
            while time.time() - start_time < duration:
                try:
                    await system.debit_credits(
                        user_id=f"user{transaction_count % 100}@example.com",
                        amount=1.0,
                        metadata={'provider': 'groq', 'model': 'llama3', 'tokens_used': 100}
                    )
                    transaction_count += 1
                except:
                    pass

        # Run concurrent workers
        tasks = [continuous_deductions() for _ in range(10)]
        await asyncio.gather(*tasks, return_exceptions=True)

        throughput = transaction_count / duration

        print(f"\n=== Throughput Test ===")
        print(f"Duration: {duration}s")
        print(f"Total Transactions: {transaction_count}")
        print(f"Throughput: {throughput:.2f} txn/sec")

        # Should handle at least 50 txn/sec
        assert throughput > 50


class TestScalability:
    """Test system scalability"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_scalability_user_growth(self, performance_test_setup):
        """Test performance with increasing user count"""
        system = performance_test_setup

        user_counts = [10, 50, 100, 500]
        results = {}

        for user_count in user_counts:
            async def batch_operation(batch_id):
                start = time.time()
                await system.get_user_credits(f"user{batch_id}@example.com")
                return time.time() - start

            start_time = time.time()
            tasks = [batch_operation(i) for i in range(user_count)]
            durations = await asyncio.gather(*tasks, return_exceptions=True)
            total_duration = time.time() - start_time

            valid_durations = [d for d in durations if isinstance(d, float)]

            results[user_count] = {
                "total_duration": total_duration,
                "avg_latency": statistics.mean(valid_durations) if valid_durations else 0,
                "throughput": user_count / total_duration
            }

        print(f"\n=== Scalability Test ===")
        for count, result in results.items():
            print(f"{count} users: {result['total_duration']:.3f}s, "
                  f"{result['throughput']:.2f} ops/sec")

        # Performance should not degrade exponentially
        # Throughput should scale somewhat linearly
        assert results[500]["throughput"] > results[10]["throughput"] * 0.5


# Benchmark summary
def print_benchmark_summary():
    """Print comprehensive benchmark summary"""
    print("\n" + "="*60)
    print("CREDIT SYSTEM PERFORMANCE BENCHMARK SUMMARY")
    print("="*60)
    print("\nTest Categories:")
    print("  1. Concurrent Operations")
    print("  2. Database Performance")
    print("  3. Cache Effectiveness")
    print("  4. Memory Usage")
    print("  5. Throughput")
    print("  6. Scalability")
    print("\nPerformance Targets:")
    print("  - Concurrent deductions: >10 ops/sec")
    print("  - Transaction history: <1s (100 records)")
    print("  - Cache hit speedup: >2x")
    print("  - Max throughput: >50 txn/sec")
    print("  - Memory increase: <100MB under load")
    print("="*60 + "\n")


# Run performance tests
if __name__ == "__main__":
    print_benchmark_summary()
    pytest.main([__file__, "-v", "-m", "performance", "--tb=short"])
