from backend.adapters.mock import MockInferenceAdapter


def test_mock_adapter_returns_complete_plausible_sample() -> None:
    sample = MockInferenceAdapter(seed=7).get_metrics()
    assert sample["status"] == "running"
    assert sample["throughput_tps"] > 0
    assert 0 <= sample["kv_cache_usage_pct"] <= 100
    assert sample["kv_cache_used_gb"] <= sample["kv_cache_total_gb"]
    assert sample["ttft_ms"] > 0
    assert sample["tpot_ms"] > 0

