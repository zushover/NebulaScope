"""Minimal quality-metrics interface reserved for benchmark integrations."""

from __future__ import annotations

from typing import Any

from .store import MetricsStore, store


class EvaluationMetrics:
    def __init__(self, metrics_store: MetricsStore = store) -> None:
        self.store = metrics_store

    def update(
        self,
        *,
        benchmark: str,
        score: float,
        metric_name: str = "accuracy",
        samples: int | None = None,
        status: str = "complete",
    ) -> dict[str, Any]:
        if not 0 <= score <= 1:
            raise ValueError("score must be between 0 and 1")
        values = {
            "benchmark": benchmark,
            "score": score,
            "metric_name": metric_name,
            "samples": samples,
            "status": status,
        }
        self.store.update("evaluation", values)
        return values


evaluation_metrics = EvaluationMetrics()

