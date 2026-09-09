"""NebulaScope application entry point."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.adapters.base import EngineMetricsAdapter
from backend.adapters.mock import MockInferenceAdapter
from backend.api.websocket import create_websocket_router
from backend.metrics.engine import EngineMetrics
from backend.metrics.evaluation import EvaluationMetrics
from backend.metrics.gpu import GpuMetricsCollector
from backend.metrics.store import MetricsStore, store as default_store


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def create_app(
    *,
    mock: bool = False,
    gpu_index: int = 0,
    gpu_enabled: bool = True,
    interval_seconds: float = 0.75,
    metrics_store: MetricsStore | None = None,
    adapter: EngineMetricsAdapter | None = None,
) -> FastAPI:
    active_store = metrics_store or default_store
    engine_metrics = EngineMetrics(active_store)
    evaluation_metrics = EvaluationMetrics(active_store)
    gpu = GpuMetricsCollector(gpu_index, enabled=gpu_enabled)
    engine_adapter = adapter or (MockInferenceAdapter() if mock else None)

    async def collect_loop() -> None:
        while True:
            active_store.update("gpu", gpu.collect())
            if engine_adapter is not None:
                try:
                    engine_metrics.update(**engine_adapter.get_metrics())
                except Exception as exc:
                    active_store.update(
                        "inference", {"status": "error", "engine_name": type(engine_adapter).__name__, "error": str(exc)}
                    )
            await asyncio.sleep(interval_seconds)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        gpu.start()
        task = asyncio.create_task(collect_loop())
        try:
            yield
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            gpu.stop()
            if engine_adapter is not None:
                engine_adapter.close()

    app = FastAPI(
        title="NebulaScope",
        description="Local LLM/VLM inference telemetry",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.metrics_store = active_store
    app.state.engine_metrics = engine_metrics
    app.include_router(create_websocket_router(active_store, interval_seconds))

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "NebulaScope"}

    @app.get("/api/metrics")
    async def current_metrics() -> dict[str, Any]:
        return active_store.snapshot()

    @app.get("/api/history")
    async def history(limit: int = 2000, task_id: str | None = None) -> dict[str, Any]:
        return {"samples": active_store.history(limit=limit, task_id=task_id)}

    @app.get("/api/logs")
    async def logs(limit: int = 300, task_id: str | None = None) -> dict[str, Any]:
        return {"logs": active_store.logs(limit=limit, task_id=task_id)}

    @app.post("/api/logs")
    async def publish_log(request: Request) -> dict[str, Any]:
        payload = await request.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("message"), str):
            raise HTTPException(status_code=422, detail="message must be a string")
        return {"accepted": active_store.add_log(payload)}

    @app.post("/api/metrics/inference")
    async def publish_inference(request: Request) -> dict[str, Any]:
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                raise TypeError("Request body must be a JSON object")
            updated = engine_metrics.update(**payload)
            return {"accepted": updated}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/metrics/evaluation")
    async def publish_evaluation(request: Request) -> dict[str, Any]:
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                raise TypeError("Request body must be a JSON object")
            updated = evaluation_metrics.update(**payload)
            return {"accepted": updated}
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    async def dashboard() -> FileResponse:
        return FileResponse(FRONTEND / "index.html")

    return app


app = create_app(mock=os.getenv("NEBULASCOPE_MOCK", "").lower() in {"1", "true", "yes"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NebulaScope local inference monitor")
    parser.add_argument("--mock", action="store_true", help="simulate inference metrics")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--gpu-index", type=int, default=0)
    parser.add_argument("--interval", type=float, default=0.75, help="sampling interval in seconds")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    uvicorn.run(
        create_app(
            mock=args.mock,
            gpu_index=args.gpu_index,
            interval_seconds=max(0.25, args.interval),
        ),
        host=args.host,
        port=args.port,
    )
