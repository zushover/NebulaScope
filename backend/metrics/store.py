"""Thread-safe in-memory storage for the latest monitoring sample."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Any


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class MetricsStore:
    """Keeps the newest values from independent metric producers."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._revision = 0
        self._data: dict[str, Any] = {
            "timestamp": utc_timestamp(),
            "revision": 0,
            "gpu": {
                "available": False,
                "name": "No NVIDIA GPU detected",
                "index": 0,
                "utilization_pct": None,
                "memory_used_gb": None,
                "memory_total_gb": None,
                "memory_utilization_pct": None,
                "power_w": None,
                "temperature_c": None,
                "gpu_clock_mhz": None,
                "memory_clock_mhz": None,
            },
            "inference": {
                "status": "idle",
                "model_name": "Not connected",
                "engine_name": None,
                "throughput_tps": None,
                "input_tokens": None,
                "output_tokens": None,
                "batch_size": None,
                "active_requests": None,
                "ttft_ms": None,
                "tpot_ms": None,
                "kv_cache_used_gb": None,
                "kv_cache_total_gb": None,
                "kv_cache_usage_pct": None,
                "prefill_latency_ms": None,
                "decode_latency_ms": None,
            },
            "evaluation": {
                "status": "not_configured",
                "benchmark": None,
                "metric_name": None,
                "score": None,
                "samples": None,
            },
        }

    def update(self, section: str, values: dict[str, Any]) -> None:
        if section not in {"gpu", "inference", "evaluation"}:
            raise KeyError(f"Unknown metrics section: {section}")
        with self._lock:
            self._data[section].update(values)
            self._revision += 1
            self._data["revision"] = self._revision
            self._data["timestamp"] = utc_timestamp()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._data)


store = MetricsStore()

