"""
app/routers/ws_router.py
━━━━━━━━━━━━━━━━━━━━━━━
Real-time WebSocket endpoint for the VoiceAgent AI live dashboard.

Architecture:
  • Each authenticated browser tab connects to /api/ws/dashboard?token=<jwt>
  • The server pushes JSON events whenever a call, booking, or campaign state
    changes — no polling required.
  • Events are fanned out via Redis pub/sub so every API worker instance
    (behind a load-balancer) sees all events.
  • If Redis is unavailable the endpoint falls back to in-process broadcasting
    using a module-level ConnectionManager.

Event envelope:
  {
    "event":   "CALL_STARTED" | "CALL_ENDED" | "DEMO_BOOKED" | "CAMPAIGN_UPDATE" | "STATS_UPDATE" | "PING",
    "payload": { ... },
    "ts":      "2026-11-06T10:00:00Z"
  }
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt
from sqlalchemy import select, func

from app.config import settings

logger = logging.getLogger("ws-router")
router = APIRouter(tags=["WebSocket"])

# ── JWT helpers ───────────────────────────────────────────────────────────────
_SECRET_KEY = settings.JWT_SECRET
_ALGORITHM = "HS256"


def _decode_jwt_token(token: str) -> Optional[int]:
    """
    Decode a JWT access token and return the user_id (``id`` claim).
    Returns None if the token is missing, expired, or invalid.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        return payload.get("id")
    except JWTError:
        return None


# ── In-process connection manager (fallback when Redis is unavailable) ────────

class ConnectionManager:
    """
    Manages a set of live WebSocket connections for a single process.

    When running behind multiple Uvicorn workers or in a Docker Swarm,
    each process has its own manager.  Cross-process fan-out is handled
    by the Redis pub/sub subscriber task (see below).
    """

    def __init__(self) -> None:
        # Maps user_id → set of active WebSocket connections
        self._connections: dict[int, Set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, user_id: int) -> None:
        await ws.accept()
        self._connections.setdefault(user_id, set()).add(ws)
        logger.info(f"[WS] User {user_id} connected. Total sockets: {self.total_connections}")

    def disconnect(self, ws: WebSocket, user_id: int) -> None:
        conns = self._connections.get(user_id, set())
        conns.discard(ws)
        if not conns:
            self._connections.pop(user_id, None)
        logger.info(f"[WS] User {user_id} disconnected. Remaining: {self.total_connections}")

    async def send_to_user(self, user_id: int, event: dict) -> None:
        """Push an event to all active sockets of a specific user."""
        dead: list[WebSocket] = []
        for ws in self._connections.get(user_id, set()):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, user_id)

    async def broadcast(self, event: dict) -> None:
        """Push an event to ALL connected users (e.g. PING heartbeat)."""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, event)

    @property
    def total_connections(self) -> int:
        return sum(len(v) for v in self._connections.values())


# Singleton manager — shared across all WebSocket connections in this process
manager = ConnectionManager()


# ── Event factory ─────────────────────────────────────────────────────────────

def _make_event(event_type: str, payload: dict) -> dict:
    return {
        "event": event_type,
        "payload": payload,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


# ── Public broadcast helpers (called from other routers / agent) ─────────────

async def broadcast_event(event_type: str, payload: dict, user_id: Optional[int] = None) -> None:
    """
    Broadcast a dashboard event.

    If user_id is provided, event is sent only to that user's connections.
    Otherwise it is broadcast to all connected users.

    Also publishes to Redis pub/sub so other API worker processes receive it.
    """
    from app.cache import cache  # late import to avoid circular deps

    event = _make_event(event_type, payload)

    # Fan-out via Redis for multi-process / multi-container deployments
    redis_channel = f"dashboard:user:{user_id}" if user_id else "dashboard:broadcast"
    await cache.publish(redis_channel, {"user_id": user_id, "event": event})

    # Also deliver locally (this process's connections)
    if user_id:
        await manager.send_to_user(user_id, event)
    else:
        await manager.broadcast(event)


# ── Redis subscriber (runs as a background task per worker) ──────────────────

async def _redis_subscriber_task() -> None:
    """
    Subscribes to Redis dashboard channels and fans out events to local
    WebSocket connections.  Runs as a long-lived asyncio task started from
    the FastAPI lifespan.
    """
    from app.cache import cache

    if not cache.is_available:
        logger.warning("[WS] Redis unavailable — cross-process fan-out disabled.")
        return

    pubsub = cache.pubsub()
    await pubsub.psubscribe("dashboard:*")
    logger.info("[WS] Redis pub/sub subscriber started on 'dashboard:*'")

    try:
        async for message in pubsub.listen():
            if message["type"] not in ("pmessage", "message"):
                continue
            try:
                data = json.loads(message["data"])
                uid = data.get("user_id")
                event = data.get("event", {})
                if uid:
                    await manager.send_to_user(uid, event)
                else:
                    await manager.broadcast(event)
            except Exception as exc:
                logger.debug(f"[WS] Redis message parse error: {exc}")
    except asyncio.CancelledError:
        logger.info("[WS] Redis subscriber task cancelled.")
    finally:
        await pubsub.unsubscribe()


# Keeps a reference so we can cancel on shutdown
_subscriber_task: Optional[asyncio.Task] = None


async def start_redis_subscriber() -> None:
    global _subscriber_task
    _subscriber_task = asyncio.create_task(_redis_subscriber_task())


async def stop_redis_subscriber() -> None:
    if _subscriber_task and not _subscriber_task.done():
        _subscriber_task.cancel()
        try:
            await _subscriber_task
        except asyncio.CancelledError:
            pass


# ── Heartbeat task ────────────────────────────────────────────────────────────

async def _heartbeat_task() -> None:
    """Send a PING every 25 seconds to keep connections alive through proxies."""
    while True:
        await asyncio.sleep(25)
        await manager.broadcast(_make_event("PING", {"connections": manager.total_connections}))


_heartbeat: Optional[asyncio.Task] = None


async def start_heartbeat() -> None:
    global _heartbeat
    _heartbeat = asyncio.create_task(_heartbeat_task())


async def stop_heartbeat() -> None:
    if _heartbeat and not _heartbeat.done():
        _heartbeat.cancel()


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/api/ws/dashboard")
async def dashboard_websocket(
    ws: WebSocket,
    token: Optional[str] = Query(default=None),
) -> None:
    """
    WebSocket endpoint for live dashboard updates.

    Connect with:
        ws://host/api/ws/dashboard?token=<jwt_access_token>

    The server will push events whenever:
      - A call starts or ends
      - A demo is booked
      - A campaign progresses
      - Dashboard KPI stats change

    If the JWT is invalid the connection is closed immediately (code 4001).
    """
    user_id = _decode_jwt_token(token or "")
    if not user_id:
        await ws.close(code=4001, reason="Invalid or missing authentication token.")
        return

    await manager.connect(ws, user_id)

    # Send initial stats snapshot on connect
    try:
        from app.cache import cache
        from app.database import AsyncSessionLocal
        from app.models.lead import Lead
        from app.models.booking import DemoBooking
        from app.models.call import Call, CallStatus

        stats = await cache.get_json(f"dashboard:stats:{user_id}")
        if stats is None:
            from app.routers.lead_router import get_dashboard_stats
            from app.models.user import User
            async with AsyncSessionLocal() as db:
                user_res = await db.execute(select(User).where(User.id == user_id))
                user_obj = user_res.scalars().first()
                if user_obj:
                    stats = await get_dashboard_stats(current_user=user_obj, db=db)

        await ws.send_json(_make_event("STATS_UPDATE", stats))
    except Exception as exc:
        logger.warning(f"[WS] Failed to send initial stats to user {user_id}: {exc}")

    try:
        while True:
            # Keep the connection alive — real events come via broadcast_event()
            data = await ws.receive_text()
            # Handle ping from client
            if data.strip() == "ping":
                await ws.send_json(_make_event("PING", {}))
    except WebSocketDisconnect:
        manager.disconnect(ws, user_id)
