"""
Regression test: the credit middleware must NOT re-debit a response the
endpoint handler already settled.

The chat/completions and image/generations handlers are the authoritative
debit point — they deduct org/individual credits and meter usage, then stamp
_metadata.credits_settled=True. Federation-served responses are billed by the
publisher and stamp _metadata.gateway_metered=True. In both cases the
middleware must skip its own deduction (returning None) while leaving the
response body intact for the client.

Endpoints with no handler-side debit (e.g. embeddings) omit both flags and
must still be billed by the middleware.
"""

import json

import pytest

from credit_deduction_middleware import CreditDeductionMiddleware


class FakeResponse:
    """Minimal Response stand-in with a consumable async body_iterator."""

    def __init__(self, payload: dict, content_type: str = "application/json"):
        self._body = json.dumps(payload).encode()
        self.headers = {"content-type": content_type}

        async def _iter():
            yield self._body

        self.body_iterator = _iter()

    async def read_body(self) -> bytes:
        out = b""
        async for chunk in self.body_iterator:
            out += chunk
        return out


def _mw():
    return CreditDeductionMiddleware(app=None)


@pytest.mark.asyncio
async def test_skips_when_handler_settled_credits():
    """credits_settled → middleware returns None and preserves the body."""
    mw = _mw()
    payload = {
        "choices": [{"message": {"content": "hi"}}],
        "usage": {"total_tokens": 1234},
        "_metadata": {"cost_incurred": 9.0, "credits_settled": True},
    }
    resp = FakeResponse(payload)
    result = await mw._extract_actual_cost(request=None, response=resp)
    assert result is None, "handler-settled response must not be re-debited"
    # Body must still be readable by the client after the peek.
    assert json.loads(await resp.read_body())["usage"]["total_tokens"] == 1234


@pytest.mark.asyncio
async def test_skips_when_gateway_metered():
    """Federation-served (gateway_metered) responses are billed by publisher."""
    mw = _mw()
    payload = {
        "choices": [{"message": {"content": "hi"}}],
        "usage": {"total_tokens": 500},
        "_metadata": {"gateway_metered": True, "cost_incurred": 0.0},
    }
    resp = FakeResponse(payload)
    result = await mw._extract_actual_cost(request=None, response=resp)
    assert result is None
    assert json.loads(await resp.read_body())["usage"]["total_tokens"] == 500


@pytest.mark.asyncio
async def test_still_debits_when_unsettled():
    """No settlement flag (e.g. embeddings) → middleware extracts a cost."""
    mw = _mw()
    payload = {
        "model": "openai/text-embedding-3-small",
        "usage": {"total_tokens": 1000},
        # no _metadata block at all
    }
    resp = FakeResponse(payload)
    result = await mw._extract_actual_cost(request=None, response=resp)
    assert result is not None, "unsettled responses must still be billed"
    credits_used, tokens_used, provider = result
    assert tokens_used == 1000
    assert provider == "openai"
    assert credits_used > 0
