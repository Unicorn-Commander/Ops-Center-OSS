#!/usr/bin/env python3
"""
Register the non-LLM compute billable metrics in Lago (idempotent).

Creates the billable metrics that metered_compute_api.py emits:
    embeddings_tokens   sum_agg on  tokens
    rerank_searches     sum_agg on  searches
    stt_audio_seconds   sum_agg on  audio_seconds
    tts_characters      sum_agg on  characters

Run inside the ops-center-direct container:
    docker exec ops-center-direct python3 /app/scripts/register_metering_metrics.py

Re-running is safe: existing metrics are detected and skipped. Attaching a
charge/price for each metric to a plan is done in the Lago UI/plan config
(Lago is the source of truth for price); this script only ensures the metric
codes exist so events are accepted.
"""

import asyncio
import os
import sys

import httpx

sys.path.insert(0, "/app")

LAGO_API_URL = os.getenv("LAGO_API_URL", "http://unicorn-lago-api:3000")


def _api_key() -> str:
    key = os.getenv("LAGO_API_KEY", "")
    if not key:
        try:
            from get_credential import get_credential
            key = get_credential("LAGO_API_KEY", "")
        except Exception:
            key = ""
    return key


METRICS = [
    {"code": "embeddings_tokens", "name": "Embeddings (tokens)",   "field_name": "tokens"},
    {"code": "rerank_searches",   "name": "Reranking (searches)",  "field_name": "searches"},
    {"code": "stt_audio_seconds", "name": "STT (audio seconds)",   "field_name": "audio_seconds"},
    {"code": "tts_characters",    "name": "TTS (characters)",      "field_name": "characters"},
]


async def main() -> int:
    key = _api_key()
    if not key:
        print("ERROR: LAGO_API_KEY not configured", file=sys.stderr)
        return 1

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Existing codes
        existing = set()
        try:
            r = await client.get(f"{LAGO_API_URL}/api/v1/billable_metrics?per_page=200", headers=headers)
            if r.status_code == 200:
                for m in r.json().get("billable_metrics", []):
                    existing.add(m.get("code"))
        except Exception as exc:
            print(f"WARN: could not list existing metrics ({exc}); will attempt creates")

        created, skipped, failed = 0, 0, 0
        for m in METRICS:
            if m["code"] in existing:
                print(f"skip   {m['code']} (exists)")
                skipped += 1
                continue
            payload = {"billable_metric": {
                "name": m["name"],
                "code": m["code"],
                "aggregation_type": "sum_agg",
                "field_name": m["field_name"],
                "recurring": False,
            }}
            try:
                r = await client.post(f"{LAGO_API_URL}/api/v1/billable_metrics", headers=headers, json=payload)
                if r.status_code in (200, 201):
                    print(f"create {m['code']} (sum_agg/{m['field_name']})")
                    created += 1
                elif r.status_code == 422 and "already" in r.text.lower():
                    print(f"skip   {m['code']} (already exists)")
                    skipped += 1
                else:
                    print(f"FAIL   {m['code']}: HTTP {r.status_code} {r.text[:200]}", file=sys.stderr)
                    failed += 1
            except Exception as exc:
                print(f"FAIL   {m['code']}: {exc}", file=sys.stderr)
                failed += 1

        print(f"\nDone: {created} created, {skipped} skipped, {failed} failed.")
        print("Next: attach a charge/price for each metric to the relevant Lago plan(s).")
        return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
