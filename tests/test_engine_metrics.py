import pytest

from backend.metrics.engine import EngineMetrics
from backend.metrics.store import MetricsStore


def test_aliases_and_derived_kv_percentage() -> None:
    store = MetricsStore()
    metrics = EngineMetrics(store)
    metrics.update(throughput=120.5, kv_cache_used=6, kv_cache_total=12, ttft=41)
    current = store.snapshot()["inference"]
    assert current["throughput_tps"] == 120.5
    assert current["kv_cache_usage_pct"] == 50
    assert current["ttft_ms"] == 41


def test_unknown_or_negative_metrics_are_rejected() -> None:
    metrics = EngineMetrics(MetricsStore())
    with pytest.raises(KeyError):
        metrics.update(magic_metric=1)
    with pytest.raises(ValueError):
        metrics.update(throughput=-1)

