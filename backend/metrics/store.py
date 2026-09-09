"""Thread-safe in-memory storage for the latest monitoring sample."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from collections import deque
from typing import Any


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class MetricsStore:
    """Keeps the newest values from independent metric producers."""

    def __init__(self, history_limit: int = 20000, log_limit: int = 2000) -> None:
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
                "visual_tokens": None,
                "text_tokens": None,
                "stage_output_tokens": None,
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
                "task_id": None,
                "task_name": "No active task",
                "run_name": None,
                "dataset_name": None,
                "method_name": None,
                "protocol_name": None,
                "stage_name": None,
                "stage_label": None,
                "stage_index": None,
                "stage_count": None,
                "stage_progress_pct": None,
                "progress_pct": None,
                "completed_items": None,
                "total_items": None,
                "samples_per_second": None,
                "batches_per_second": None,
                "e2e_latency_ms": None,
                "vision_latency_ms": None,
                "compression_latency_ms": None,
                "cache_reduction_x": None,
                "gpu_basis_gb": None,
                "cpu_basis_gb": None,
                "peak_vram_gb": None,
                "accuracy": None,
                "correct_samples": None,
                "evaluated_samples": None,
                "unparsable_samples": None,
                "error_samples": None,
                "empty_answers": None,
                "eta_seconds": None,
                "stages": [],
                "custom_metrics": {},
            },
            "evaluation": {
                "status": "not_configured",
                "benchmark": None,
                "metric_name": None,
                "score": None,
                "samples": None,
            },
        }
        self._history: deque[dict[str, Any]] = deque(maxlen=history_limit)
        self._logs: deque[dict[str, Any]] = deque(maxlen=log_limit)

    def update(self, section: str, values: dict[str, Any]) -> None:
        if section not in {"gpu", "inference", "evaluation"}:
            raise KeyError(f"Unknown metrics section: {section}")
        with self._lock:
            self._data[section].update(values)
            self._revision += 1
            self._data["revision"] = self._revision
            self._data["timestamp"] = utc_timestamp()
            self._history.append(deepcopy(self._data))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._data)

    def history(self, limit: int = 1000, task_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            rows = list(self._history)
            if task_id:
                rows = [row for row in rows if row.get("inference", {}).get("task_id") == task_id]
            return deepcopy(rows[-max(1, min(limit, 20000)):])

    def add_log(self, values: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            row = {"timestamp": utc_timestamp(), "level": "info", "source": "runner", **values}
            self._logs.append(row)
            return deepcopy(row)

    def logs(self, limit: int = 300, task_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            rows = list(self._logs)
            if task_id:
                rows = [row for row in rows if row.get("task_id") == task_id]
            return deepcopy(rows[-max(1, min(limit, 2000)):])


store = MetricsStore()
