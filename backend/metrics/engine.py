"""Public inference-metrics hook used by engines and adapters."""

from __future__ import annotations

from math import isfinite
from typing import Any

from .store import MetricsStore, store


NUMERIC_FIELDS = {
    "throughput_tps",
    "input_tokens",
    "output_tokens",
    "batch_size",
    "active_requests",
    "ttft_ms",
    "tpot_ms",
    "kv_cache_used_gb",
    "kv_cache_total_gb",
    "kv_cache_usage_pct",
    "prefill_latency_ms",
    "decode_latency_ms",
    "stage_index", "stage_count", "stage_progress_pct", "progress_pct",
    "completed_items", "total_items", "samples_per_second", "batches_per_second",
    "e2e_latency_ms", "vision_latency_ms", "compression_latency_ms",
    "cache_reduction_x", "gpu_basis_gb", "cpu_basis_gb", "peak_vram_gb",
    "accuracy", "correct_samples", "evaluated_samples", "unparsable_samples",
    "visual_tokens", "text_tokens", "stage_output_tokens", "error_samples",
    "empty_answers", "eta_seconds",
}
TEXT_FIELDS = {"status", "model_name", "engine_name", "task_id", "task_name", "run_name",
               "dataset_name", "method_name", "protocol_name", "stage_name", "stage_label"}
OBJECT_FIELDS = {"stages", "custom_metrics"}
ALIASES = {
    "throughput": "throughput_tps",
    "tokens_per_second": "throughput_tps",
    "ttft": "ttft_ms",
    "tpot": "tpot_ms",
    "kv_cache_used": "kv_cache_used_gb",
    "kv_cache_total": "kv_cache_total_gb",
    "prefill_latency": "prefill_latency_ms",
    "decode_latency": "decode_latency_ms",
}


class EngineMetrics:
    """Small stable API that custom inference code can call directly."""

    def __init__(self, metrics_store: MetricsStore = store) -> None:
        self.store = metrics_store

    def update(self, **values: Any) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        unknown: list[str] = []
        for original_key, value in values.items():
            key = ALIASES.get(original_key, original_key)
            if key in NUMERIC_FIELDS:
                if value is not None:
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        raise TypeError(f"{original_key} must be numeric or None")
                    if not isfinite(float(value)) or value < 0:
                        raise ValueError(f"{original_key} must be finite and non-negative")
                normalized[key] = value
            elif key in TEXT_FIELDS:
                if value is not None and not isinstance(value, str):
                    raise TypeError(f"{original_key} must be a string or None")
                normalized[key] = value
            elif key in OBJECT_FIELDS:
                if key == "stages" and not isinstance(value, list):
                    raise TypeError("stages must be a list")
                if key == "custom_metrics" and not isinstance(value, dict):
                    raise TypeError("custom_metrics must be an object")
                normalized[key] = value
            else:
                unknown.append(original_key)
        if unknown:
            raise KeyError(f"Unknown inference metrics: {', '.join(sorted(unknown))}")

        used = normalized.get("kv_cache_used_gb")
        total = normalized.get("kv_cache_total_gb")
        if used is not None and total:
            normalized.setdefault("kv_cache_usage_pct", min(100.0, used / total * 100.0))
        self.store.update("inference", normalized)
        return normalized


metrics = EngineMetrics()
