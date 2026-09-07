"""NVIDIA GPU telemetry collection through NVML."""

from __future__ import annotations

from typing import Any


class GpuMetricsCollector:
    def __init__(self, index: int = 0, enabled: bool = True) -> None:
        self.index = index
        self.enabled = enabled
        self._nvml: Any = None
        self._handle: Any = None
        self.error: str | None = None

    def start(self) -> None:
        if not self.enabled:
            self.error = "GPU collection disabled"
            return
        try:
            import pynvml

            pynvml.nvmlInit()
            self._nvml = pynvml
            self._handle = pynvml.nvmlDeviceGetHandleByIndex(self.index)
        except Exception as exc:  # Hardware and driver failures must not stop the app.
            self.error = str(exc)
            self._handle = None

    def stop(self) -> None:
        if self._nvml is not None:
            try:
                self._nvml.nvmlShutdown()
            except Exception:
                pass

    def collect(self) -> dict[str, Any]:
        if self._handle is None or self._nvml is None:
            return {
                "available": False,
                "name": "GPU unavailable",
                "index": self.index,
                "error": self.error,
            }
        try:
            nvml = self._nvml
            memory = nvml.nvmlDeviceGetMemoryInfo(self._handle)
            utilization = nvml.nvmlDeviceGetUtilizationRates(self._handle)
            name = nvml.nvmlDeviceGetName(self._handle)
            if isinstance(name, bytes):
                name = name.decode("utf-8", errors="replace")
            used_gb = memory.used / 1024**3
            total_gb = memory.total / 1024**3
            return {
                "available": True,
                "name": name,
                "index": self.index,
                "utilization_pct": float(utilization.gpu),
                "memory_used_gb": used_gb,
                "memory_total_gb": total_gb,
                "memory_utilization_pct": used_gb / total_gb * 100 if total_gb else 0,
                "power_w": nvml.nvmlDeviceGetPowerUsage(self._handle) / 1000,
                "temperature_c": float(
                    nvml.nvmlDeviceGetTemperature(self._handle, nvml.NVML_TEMPERATURE_GPU)
                ),
                "gpu_clock_mhz": float(
                    nvml.nvmlDeviceGetClockInfo(self._handle, nvml.NVML_CLOCK_GRAPHICS)
                ),
                "memory_clock_mhz": float(
                    nvml.nvmlDeviceGetClockInfo(self._handle, nvml.NVML_CLOCK_MEM)
                ),
                "error": None,
            }
        except Exception as exc:
            self.error = str(exc)
            return {
                "available": False,
                "name": "GPU read error",
                "index": self.index,
                "error": self.error,
            }

