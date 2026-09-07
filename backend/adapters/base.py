"""Base protocol for polling inference engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EngineMetricsAdapter(ABC):
    """Implement this class for vLLM, SGLang, or a custom engine."""

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """Return one normalized inference metric sample."""
        raise NotImplementedError

    def close(self) -> None:
        """Release adapter resources when the monitor stops."""

