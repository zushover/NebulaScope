"""Plausible inference telemetry for dashboard development."""

from __future__ import annotations

import math
import random
import time
from typing import Any

from .base import EngineMetricsAdapter


class MockInferenceAdapter(EngineMetricsAdapter):
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._started = time.monotonic()
        self._input_tokens = 12_480
        self._output_tokens = 3_260

    def get_metrics(self) -> dict[str, Any]:
        elapsed = time.monotonic() - self._started
        wave = math.sin(elapsed / 5.0)
        throughput = max(20.0, 142 + wave * 25 + self._rng.uniform(-8, 8))
        batch_size = max(1, round(7 + wave * 2 + self._rng.uniform(-1, 1)))
        active_requests = max(1, batch_size - self._rng.randint(0, 2))
        kv_total = 12.0
        kv_used = min(kv_total, max(1.2, 6.1 + wave * 2.1 + self._rng.uniform(-0.25, 0.25)))
        self._input_tokens += self._rng.randint(0, 180)
        self._output_tokens += round(throughput * 0.75)
        return {
            "status": "running",
            "model_name": "Qwen2.5-VL (mock)",
            "engine_name": "MockAdapter",
            "throughput_tps": throughput,
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
            "batch_size": batch_size,
            "active_requests": active_requests,
            "ttft_ms": max(15.0, 43 + wave * 9 + self._rng.uniform(-3, 3)),
            "tpot_ms": max(2.0, 7.2 - wave * 0.8 + self._rng.uniform(-0.35, 0.35)),
            "kv_cache_used_gb": kv_used,
            "kv_cache_total_gb": kv_total,
            "kv_cache_usage_pct": kv_used / kv_total * 100,
            "prefill_latency_ms": max(20.0, 88 + wave * 16 + self._rng.uniform(-5, 5)),
            "decode_latency_ms": max(4.0, 28 - wave * 4 + self._rng.uniform(-2, 2)),
        }

