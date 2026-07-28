"""
Per-(app, model) included-vs-metered policy resolver.

Contract: default metered (no rows / no match / error), explicit "included"
rows mark bundled inference, most-specific match wins (exact > prefix > '*'),
and resolution never raises.
"""

import pytest

import inference_policy
from inference_policy import resolve_inference_policy, INCLUDED, METERED


class FakeConn:
    def __init__(self, rows):
        self._rows = rows

    async def fetch(self, query):
        return self._rows


class FakeAcquire:
    def __init__(self, rows):
        self._rows = rows

    async def __aenter__(self):
        return FakeConn(self._rows)

    async def __aexit__(self, *a):
        return False


class FakePool:
    def __init__(self, rows):
        self.rows = rows

    def acquire(self):
        return FakeAcquire(self.rows)


def pool(rows):
    inference_policy._reset_cache_for_tests()
    return FakePool([dict(app=a, model=m, policy=p) for (a, m, p) in rows])


@pytest.mark.asyncio
async def test_default_metered_with_no_rows():
    assert await resolve_inference_policy("meeting-ops", "gpt-4o", pool([])) == METERED


@pytest.mark.asyncio
async def test_no_app_or_model_is_metered():
    assert await resolve_inference_policy(None, "gpt-4o", pool([])) == METERED
    assert await resolve_inference_policy("meeting-ops", None, pool([])) == METERED


@pytest.mark.asyncio
async def test_exact_match_included():
    p = pool([("meeting-ops", "Parakeet-STT", "included")])
    assert await resolve_inference_policy("meeting-ops", "Parakeet-STT", p) == INCLUDED
    # different app → not covered
    inference_policy._reset_cache_for_tests()
    assert await resolve_inference_policy("brand-ops", "Parakeet-STT", p) == METERED


@pytest.mark.asyncio
async def test_prefix_wildcard():
    p = pool([("meeting-ops", "Qwen3.6-*", "included")])
    assert await resolve_inference_policy("meeting-ops", "Qwen3.6-35B-A3B", p) == INCLUDED
    inference_policy._reset_cache_for_tests()
    assert await resolve_inference_policy("meeting-ops", "gpt-4o", p) == METERED


@pytest.mark.asyncio
async def test_most_specific_wins():
    # app-wildcard says included, but an exact row meters gpt-4o → exact wins
    p = pool([
        ("meeting-ops", "*", "included"),
        ("meeting-ops", "gpt-4o", "metered"),
    ])
    assert await resolve_inference_policy("meeting-ops", "gpt-4o", p) == METERED
    inference_policy._reset_cache_for_tests()
    # a non-overridden model falls to the wildcard 'included'
    p2 = pool([
        ("meeting-ops", "*", "included"),
        ("meeting-ops", "gpt-4o", "metered"),
    ])
    assert await resolve_inference_policy("meeting-ops", "Qwen3.6-35B", p2) == INCLUDED


@pytest.mark.asyncio
async def test_prefix_beats_wildcard_exact_beats_prefix():
    p = pool([
        ("mo", "*", "metered"),
        ("mo", "Qwen3.6-*", "included"),
        ("mo", "Qwen3.6-VL", "metered"),
    ])
    assert await resolve_inference_policy("mo", "Qwen3.6-35B", p) == INCLUDED   # prefix > wildcard
    inference_policy._reset_cache_for_tests()
    p = pool([
        ("mo", "*", "metered"),
        ("mo", "Qwen3.6-*", "included"),
        ("mo", "Qwen3.6-VL", "metered"),
    ])
    assert await resolve_inference_policy("mo", "Qwen3.6-VL", p) == METERED     # exact > prefix


@pytest.mark.asyncio
async def test_never_raises_on_db_error():
    class BoomPool:
        def acquire(self):
            raise RuntimeError("db down")
    inference_policy._reset_cache_for_tests()
    assert await resolve_inference_policy("mo", "gpt-4o", BoomPool()) == METERED
