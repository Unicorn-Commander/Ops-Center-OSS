#!/usr/bin/env python3
"""
Performance Benchmarking Suite for Billing API
===============================================

Measures baseline performance and tracks improvements.

Usage:
    python benchmark.py --endpoint all
    python benchmark.py --endpoint /credits/balance --iterations 1000
    python benchmark.py --compare baseline.json
"""

import asyncio
import httpx
import time
import statistics
import json
import sys
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse


@dataclass
class BenchmarkResult:
    """Results from a single benchmark"""
    endpoint: str
    method: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    p50: float
    p95: float
    p99: float
    success_count: int
    error_count: int
    requests_per_second: float
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)

    def print_summary(self):
        """Print formatted summary"""
        print(f"\n{'='*60}")
        print(f"Benchmark: {self.method} {self.endpoint}")
        print(f"{'='*60}")
        print(f"Iterations:    {self.iterations}")
        print(f"Total Time:    {self.total_time:.2f}s")
        print(f"Success:       {self.success_count}/{self.iterations} " +
              f"({self.success_count/self.iterations*100:.1f}%)")
        print(f"\nLatency Statistics:")
        print(f"  Average:     {self.avg_time:.2f}ms")
        print(f"  Min:         {self.min_time:.2f}ms")
        print(f"  Max:         {self.max_time:.2f}ms")
        print(f"  p50:         {self.p50:.2f}ms")
        print(f"  p95:         {self.p95:.2f}ms")
        print(f"  p99:         {self.p99:.2f}ms")
        print(f"\nThroughput:    {self.requests_per_second:.2f} req/s")
        print(f"{'='*60}\n")


class BillingBenchmark:
    """Benchmark runner for billing endpoints"""

    def __init__(self, base_url: str = "http://localhost:8084"):
        self.base_url = base_url
        self.headers = {
            "Authorization": "Bearer test_token_benchmark",
            "Cookie": "session_token=test_session_benchmark",
            "Content-Type": "application/json",
        }

    async def benchmark_endpoint(
        self,
        method: str,
        path: str,
        iterations: int = 1000,
        payload: Dict = None
    ) -> BenchmarkResult:
        """Benchmark a single endpoint"""
        times: List[float] = []
        success_count = 0
        error_count = 0

        print(f"Benchmarking {method} {path} ({iterations} iterations)...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            start_time = time.time()

            for i in range(iterations):
                if i % 100 == 0:
                    print(f"  Progress: {i}/{iterations} ({i/iterations*100:.1f}%)", end="\r")

                req_start = time.perf_counter()

                try:
                    if method == "GET":
                        response = await client.get(
                            f"{self.base_url}{path}",
                            headers=self.headers
                        )
                    elif method == "POST":
                        response = await client.post(
                            f"{self.base_url}{path}",
                            headers=self.headers,
                            json=payload or {}
                        )
                    else:
                        raise ValueError(f"Unsupported method: {method}")

                    req_time = (time.perf_counter() - req_start) * 1000  # Convert to ms

                    if response.status_code < 400:
                        success_count += 1
                        times.append(req_time)
                    else:
                        error_count += 1

                except Exception as e:
                    error_count += 1
                    print(f"\nError on iteration {i}: {e}")

            total_time = time.time() - start_time

        # Calculate statistics
        if not times:
            print("✗ All requests failed!")
            return None

        times.sort()

        result = BenchmarkResult(
            endpoint=path,
            method=method,
            iterations=iterations,
            total_time=total_time,
            avg_time=statistics.mean(times),
            min_time=min(times),
            max_time=max(times),
            p50=times[int(len(times) * 0.50)],
            p95=times[int(len(times) * 0.95)],
            p99=times[int(len(times) * 0.99)],
            success_count=success_count,
            error_count=error_count,
            requests_per_second=iterations / total_time,
            timestamp=datetime.now().isoformat()
        )

        return result

    async def run_all_benchmarks(self, iterations: int = 1000) -> List[BenchmarkResult]:
        """Run benchmarks on all critical endpoints"""
        benchmarks = [
            # Credit API (hottest paths)
            ("GET", "/api/v1/credits/balance"),
            ("GET", "/api/v1/credits/usage/summary"),
            ("GET", "/api/v1/credits/transactions?limit=20"),

            # Organization Billing API
            ("GET", "/api/v1/org-billing/organizations/org_1234/subscription"),
            ("GET", "/api/v1/org-billing/organizations/org_1234/credit-pool"),
            ("GET", "/api/v1/org-billing/organizations/org_1234/members"),

            # Analytics (admin endpoints)
            ("GET", "/api/v1/org-billing/analytics/platform"),
            ("GET", "/api/v1/org-billing/analytics/revenue-trends?period=30d"),
        ]

        results = []

        for method, path in benchmarks:
            result = await self.benchmark_endpoint(method, path, iterations)
            if result:
                result.print_summary()
                results.append(result)

        return results

    def save_results(self, results: List[BenchmarkResult], filename: str):
        """Save benchmark results to JSON file"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "results": [r.to_dict() for r in results]
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✓ Results saved to {filename}")

    def compare_results(self, baseline_file: str, current_results: List[BenchmarkResult]):
        """Compare current results with baseline"""
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)

        baseline_map = {
            f"{r['method']} {r['endpoint']}": r
            for r in baseline_data['results']
        }

        print(f"\n{'='*80}")
        print("Performance Comparison vs Baseline")
        print(f"{'='*80}")
        print(f"{'Endpoint':<50} {'Baseline':<12} {'Current':<12} {'Change':<10}")
        print(f"{'-'*80}")

        for result in current_results:
            key = f"{result.method} {result.endpoint}"
            baseline = baseline_map.get(key)

            if not baseline:
                print(f"{key:<50} {'N/A':<12} {result.avg_time:>10.2f}ms {'NEW':<10}")
                continue

            baseline_avg = baseline['avg_time']
            current_avg = result.avg_time
            change_pct = ((current_avg - baseline_avg) / baseline_avg) * 100

            status = "✓ FASTER" if change_pct < 0 else "✗ SLOWER"
            color = "\033[92m" if change_pct < 0 else "\033[91m"  # Green/Red
            reset = "\033[0m"

            print(
                f"{key:<50} {baseline_avg:>10.2f}ms {current_avg:>10.2f}ms "
                f"{color}{change_pct:>+8.1f}% {status}{reset}"
            )

        print(f"{'='*80}\n")


async def main():
    parser = argparse.ArgumentParser(description="Benchmark billing API performance")
    parser.add_argument("--endpoint", default="all", help="Specific endpoint or 'all'")
    parser.add_argument("--iterations", type=int, default=1000, help="Number of requests")
    parser.add_argument("--base-url", default="http://localhost:8084", help="API base URL")
    parser.add_argument("--output", default="benchmark_results.json", help="Output file")
    parser.add_argument("--compare", help="Baseline file to compare against")

    args = parser.parse_args()

    benchmark = BillingBenchmark(base_url=args.base_url)

    if args.endpoint == "all":
        print(f"Running full benchmark suite ({args.iterations} iterations per endpoint)")
        results = await benchmark.run_all_benchmarks(args.iterations)
    else:
        print(f"Benchmarking {args.endpoint}")
        result = await benchmark.benchmark_endpoint("GET", args.endpoint, args.iterations)
        results = [result] if result else []

    if results:
        # Print overall summary
        print(f"\n{'='*60}")
        print("Overall Performance Summary")
        print(f"{'='*60}")

        all_times = []
        total_requests = 0
        total_errors = 0

        for r in results:
            total_requests += r.iterations
            total_errors += r.error_count
            if r.p95 < 100:
                status = "✓ EXCELLENT"
            elif r.p95 < 200:
                status = "✓ GOOD"
            elif r.p95 < 500:
                status = "⚠ ACCEPTABLE"
            else:
                status = "✗ NEEDS OPTIMIZATION"

            print(f"{r.endpoint:<50} p95: {r.p95:>6.2f}ms  {status}")

        print(f"\nTotal Requests: {total_requests}")
        print(f"Total Errors:   {total_errors} ({total_errors/total_requests*100:.2f}%)")
        print(f"{'='*60}\n")

        # Save results
        benchmark.save_results(results, args.output)

        # Compare with baseline if provided
        if args.compare:
            benchmark.compare_results(args.compare, results)


if __name__ == "__main__":
    asyncio.run(main())
