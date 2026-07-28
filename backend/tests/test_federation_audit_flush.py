"""
RoutingAuditLog must flush a low-traffic trickle on a timer, not only when
the 50-entry buffer fills. Otherwise sparse entries stay invisible to audit
queries and are lost on restart.
"""

import asyncio

import pytest

from federation.resilience import RoutingAuditLog


class FakeConn:
    def __init__(self, sink):
        self.sink = sink

    async def executemany(self, query, rows):
        self.sink.extend(rows)


class FakeAcquire:
    def __init__(self, sink):
        self.sink = sink

    async def __aenter__(self):
        return FakeConn(self.sink)

    async def __aexit__(self, *a):
        return False


class FakePool:
    def __init__(self):
        self.rows = []

    def acquire(self):
        return FakeAcquire(self.rows)


async def _log_one(audit, rid="r1"):
    await audit.log_decision(
        request_id=rid, service_type="llm", model="m", user_id="u",
        user_tier="pro", candidates_found=1, candidates_after_constraints=1,
        outcome="routed",
    )


@pytest.mark.asyncio
async def test_timer_flushes_sub_threshold_buffer():
    pool = FakePool()
    audit = RoutingAuditLog(db_pool=pool)
    audit._buffer_max_age = 0.05  # fast timer for the test

    await _log_one(audit)  # one entry — far below the 50-count threshold
    assert len(pool.rows) == 0, "should not flush immediately on a single entry"
    assert audit._flush_task is not None, "background flusher should have started"

    await asyncio.sleep(0.12)  # let the periodic flush fire
    assert len(pool.rows) == 1, "timer must flush the trickle"
    assert audit._buffer == []

    audit._flush_task.cancel()


@pytest.mark.asyncio
async def test_count_flush_still_immediate():
    pool = FakePool()
    audit = RoutingAuditLog(db_pool=pool)
    audit._buffer_limit = 3
    audit._buffer_max_age = 0  # disable timer — exercise count path only

    for i in range(3):
        await _log_one(audit, rid=f"r{i}")
    assert len(pool.rows) == 3, "count threshold flushes synchronously"
    assert audit._flush_task is None, "timer disabled → no background task"
