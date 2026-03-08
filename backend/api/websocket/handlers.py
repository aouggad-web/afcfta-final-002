"""
AfCFTA Platform - WebSocket Real-time Handlers
================================================
Provides live investment alerts, tariff updates, calculation progress,
and regional metrics via WebSocket connections.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket Real-time"])

# Channel definitions matching the problem statement
WEBSOCKET_CHANNELS: Dict[str, Dict[str, Any]] = {
    "investment_alerts": {
        "description": "Real-time investment opportunity notifications",
        "filters": ["user_criteria", "sector_preferences", "risk_tolerance"],
        "frequency": "immediate",
    },
    "tariff_updates": {
        "description": "Live tariff changes across regions",
        "scope": "global_or_country_specific",
        "frequency": "as_updated",
    },
    "calculation_progress": {
        "description": "Progress updates for bulk operations",
        "use_case": "large_dataset_processing",
        "frequency": "percentage_milestones",
    },
    "regional_metrics": {
        "description": "Live regional performance indicators",
        "metrics": ["trade_volumes", "investment_flows", "policy_changes"],
        "frequency": "hourly_updates",
    },
    "system_notifications": {
        "description": "Platform updates and maintenance alerts",
        "scope": "all_users_or_targeted",
        "frequency": "event_driven",
    },
}


# =============================================================================
# Connection Manager
# =============================================================================

class ConnectionManager:
    """
    Manages active WebSocket connections with channel-based pub/sub.
    """

    def __init__(self) -> None:
        # channel -> set of WebSockets
        self._channels: Dict[str, Set[WebSocket]] = {ch: set() for ch in WEBSOCKET_CHANNELS}
        # websocket -> metadata
        self._meta: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        channel: str,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> None:
        await websocket.accept()
        if channel not in self._channels:
            self._channels[channel] = set()
        self._channels[channel].add(websocket)
        self._meta[websocket] = {
            "channel": channel,
            "user_id": user_id,
            "filters": filters or {},
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "connection_id": str(uuid.uuid4()),
        }
        logger.info(f"[WS] Client connected to '{channel}' (user={user_id})")
        await self._send(websocket, {
            "type": "connection_ack",
            "channel": channel,
            "connection_id": self._meta[websocket]["connection_id"],
            "message": f"Connected to {channel}",
        })

    def disconnect(self, websocket: WebSocket) -> None:
        meta = self._meta.pop(websocket, {})
        channel = meta.get("channel")
        if channel and channel in self._channels:
            self._channels[channel].discard(websocket)
        logger.info(f"[WS] Client disconnected from '{channel}'")

    @staticmethod
    async def _send(websocket: WebSocket, data: Dict[str, Any]) -> None:
        try:
            await websocket.send_json(data)
        except Exception:
            pass

    async def broadcast(self, channel: str, data: Dict[str, Any]) -> int:
        """Broadcast a message to all subscribers of a channel."""
        sockets = list(self._channels.get(channel, set()))
        count = 0
        for ws in sockets:
            await self._send(ws, {"channel": channel, "timestamp": _now(), **data})
            count += 1
        return count

    async def send_to_user(self, user_id: str, data: Dict[str, Any]) -> int:
        """Send a targeted message to all connections for a given user."""
        count = 0
        for ws, meta in list(self._meta.items()):
            if meta.get("user_id") == user_id:
                await self._send(ws, {"timestamp": _now(), **data})
                count += 1
        return count

    def active_connections(self) -> Dict[str, int]:
        return {ch: len(sockets) for ch, sockets in self._channels.items()}

    def total_connections(self) -> int:
        return len(self._meta)


manager = ConnectionManager()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# WebSocket endpoints
# =============================================================================

@router.websocket("/investment-alerts")
async def investment_alerts_ws(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    risk_tolerance: Optional[str] = Query(None),
):
    """
    Real-time investment opportunity alerts.
    Send a ping message {"type": "ping"} to keep the connection alive.
    """
    filters = {"sector": sector, "risk_tolerance": risk_tolerance}
    await manager.connect(websocket, "investment_alerts", user_id=user_id, filters=filters)
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": _now()})
            elif msg.get("type") == "subscribe":
                # Update subscription filters
                manager._meta[websocket]["filters"].update(msg.get("filters", {}))
                await websocket.send_json({"type": "subscribed", "timestamp": _now()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/tariff-updates")
async def tariff_updates_ws(
    websocket: WebSocket,
    countries: Optional[str] = Query(None, description="Comma-separated country codes"),
):
    """
    Live tariff change notifications.
    Optional `countries` filter (e.g. ?countries=DZA,MAR).
    """
    country_list = [c.strip() for c in countries.split(",")] if countries else []
    filters = {"countries": country_list}
    await manager.connect(websocket, "tariff_updates", filters=filters)
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": _now()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/calculation-progress/{operation_id}")
async def calculation_progress_ws(websocket: WebSocket, operation_id: str):
    """
    Stream progress updates for a long-running bulk operation.
    Automatically closes when the operation reaches 100%.
    """
    await manager.connect(
        websocket, "calculation_progress",
        filters={"operation_id": operation_id}
    )
    try:
        # Simulate progress streaming (real impl listens to a Redis pub/sub key)
        for progress in range(0, 101, 10):
            await asyncio.sleep(0.5)
            payload = {
                "type": "progress",
                "operationId": operation_id,
                "progressPercent": progress,
                "status": "completed" if progress == 100 else "in_progress",
            }
            try:
                await websocket.send_json(payload)
            except Exception:
                break
            if progress == 100:
                break
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


@router.websocket("/regional-metrics")
async def regional_metrics_ws(
    websocket: WebSocket,
    bloc: Optional[str] = Query(None),
    interval_s: int = Query(30, ge=5, le=3600),
):
    """
    Live regional performance metrics.
    Pushes updated data every `interval_s` seconds (default 30s).
    """
    await manager.connect(websocket, "regional_metrics", filters={"bloc": bloc})
    try:
        while True:
            try:
                from intelligence.analytics.regional_analytics import get_regional_analytics
                analytics = get_regional_analytics()
                if bloc:
                    data = analytics.get_bloc_summary(bloc.upper())
                else:
                    data = {"blocs": analytics.get_all_blocs()}
                await websocket.send_json({
                    "type": "metrics_update",
                    "timestamp": _now(),
                    "data": data,
                })
            except Exception as exc:
                logger.warning(f"[WS] Regional metrics error: {exc}")
            await asyncio.sleep(interval_s)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/system-notifications")
async def system_notifications_ws(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
):
    """Platform-wide system notifications and maintenance alerts."""
    await manager.connect(websocket, "system_notifications", user_id=user_id)
    try:
        # Send initial platform status
        await websocket.send_json({
            "type": "system_status",
            "status": "operational",
            "version": "3.0.0",
            "timestamp": _now(),
            "active_connections": manager.total_connections(),
        })
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": _now(),
                    "active_connections": manager.total_connections(),
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# =============================================================================
# HTTP status endpoint for the WebSocket manager
# =============================================================================

@router.get("/status")
async def websocket_status():
    """Return current WebSocket connection statistics."""
    return {
        "active_connections": manager.active_connections(),
        "total_connections": manager.total_connections(),
        "channels": list(WEBSOCKET_CHANNELS.keys()),
        "channel_descriptions": {
            ch: info["description"] for ch, info in WEBSOCKET_CHANNELS.items()
        },
        "timestamp": _now(),
    }
