"""WebSocket stream for browser clients."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.metrics.store import MetricsStore


def create_websocket_router(store: MetricsStore, interval_seconds: float) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws/metrics")
    async def metrics_socket(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                await websocket.send_json(store.snapshot())
                await asyncio.sleep(interval_seconds)
        except (WebSocketDisconnect, RuntimeError):
            return

    return router

