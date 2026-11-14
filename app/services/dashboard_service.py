"""
app/services/dashboard_service.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Modular analytics service for VoiceAgent AI dashboard.
Calculates core KPIs, sentiment distributions, and bot connection metrics
with Redis caching layer.
"""

import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.lead import Lead
from app.models.booking import DemoBooking
from app.models.call import Call, CallStatus
from app.cache import cache

logger = logging.getLogger("dashboard-service")


async def get_base_metrics(user_id: int, db: AsyncSession) -> Dict[str, Any]:
    """Calculate lead, demo, call counts and conversion rates."""
    lead_stmt = select(func.count(Lead.id)).where(Lead.user_id == user_id)
    booking_stmt = select(func.count(DemoBooking.id)).where(DemoBooking.user_id == user_id)
    call_stmt = select(func.count(Call.id)).where(Call.user_id == user_id)
    not_picked_stmt = select(func.count(Call.id)).where(
        Call.user_id == user_id,
        Call.status.in_([CallStatus.NO_ANSWER, CallStatus.BUSY, CallStatus.FAILED])
    )
    connected_stmt = select(func.count(Call.id)).where(
        Call.user_id == user_id,
        Call.status == CallStatus.COMPLETED
    )

    total_leads = (await db.execute(lead_stmt)).scalar() or 0
    demos_booked = (await db.execute(booking_stmt)).scalar() or 0
    total_calls = (await db.execute(call_stmt)).scalar() or 0
    calls_not_picked = (await db.execute(not_picked_stmt)).scalar() or 0
    calls_connected = (await db.execute(connected_stmt)).scalar() or 0
    conversion_rate = round((demos_booked / total_leads * 100), 1) if total_leads > 0 else 0.0

    return {
        "total_leads": total_leads,
        "demos_booked": demos_booked,
        "total_calls": total_calls,
        "calls_connected": calls_connected,
        "calls_not_picked": calls_not_picked,
        "conversion_rate": conversion_rate,
    }


async def analyze_sentiment_and_connection(user_id: int, db: AsyncSession) -> Dict[str, Any]:
    """Analyze the last 100 call records for customer sentiment and engagement quality."""
    calls_res = await db.execute(
        select(Call.summary, Call.duration_seconds, Call.status)
        .where(Call.user_id == user_id)
        .order_by(Call.start_time.desc())
        .limit(100)
    )
    call_rows = calls_res.all()

    pos_count = 0
    neu_count = 0
    neg_count = 0
    genuine_conn = 0
    early_drop = 0
    ai_resist = 0
    total_analyzed = 0

    for summary_raw, duration, status in call_rows:
        duration = duration or 0
        if not summary_raw:
            if status == CallStatus.COMPLETED and duration >= 25:
                pos_count += 1
                genuine_conn += 1
                total_analyzed += 1
            elif status in (CallStatus.NO_ANSWER, CallStatus.BUSY, CallStatus.FAILED) or duration < 10:
                neg_count += 1
                early_drop += 1
                total_analyzed += 1
            continue

        try:
            summary = json.loads(summary_raw) if isinstance(summary_raw, str) else summary_raw
            total_analyzed += 1
            s = str(summary.get("sentiment", "NEUTRAL")).upper()
            if "POS" in s:
                pos_count += 1
            elif "NEG" in s:
                neg_count += 1
            else:
                neu_count += 1

            conn_status = str(summary.get("connection_status", "")).upper()
            if conn_status == "GENUINE_CONVERSATION" or summary.get("engagement_score", 0) >= 6:
                genuine_conn += 1
            elif conn_status in ("EARLY_HANGUP", "DISMISSED_AS_AI") or duration < 15:
                early_drop += 1

            if summary.get("ai_hesitation") is True or conn_status == "DISMISSED_AS_AI":
                ai_resist += 1
        except Exception as err:
            logger.debug(f"Failed parsing call summary JSON: {err}")

    if total_analyzed > 0:
        pos_pct = round((pos_count / total_analyzed) * 100)
        neu_pct = round((neu_count / total_analyzed) * 100)
        neg_pct = round((neg_count / total_analyzed) * 100)
    else:
        pos_pct = neu_pct = neg_pct = 0

    if pos_pct >= 60:
        health_rating = "Excellent Connection (Human-like)"
    elif pos_pct >= 35:
        health_rating = "Healthy Engagement"
    elif total_analyzed == 0:
        health_rating = "Awaiting Calls"
    else:
        health_rating = "High Bot Resistance / Early Drops"

    return {
        "total_analyzed": total_analyzed,
        "positive": pos_count,
        "neutral": neu_count,
        "negative": neg_count,
        "positive_pct": pos_pct,
        "neutral_pct": neu_pct,
        "negative_pct": neg_pct,
        "genuine_connections": genuine_conn,
        "early_dropoffs": early_drop,
        "ai_resistance": ai_resist,
        "connection_health": health_rating
    }


async def compute_dashboard_stats(user_id: int, db: AsyncSession) -> Dict[str, Any]:
    """Fetch dashboard stats from Redis cache or calculate fresh and cache for 30s."""
    cache_key = f"dashboard:stats:{user_id}"
    cached_stats = await cache.get_json(cache_key)
    if cached_stats is not None:
        return cached_stats

    base = await get_base_metrics(user_id, db)
    sentiment = await analyze_sentiment_and_connection(user_id, db)
    stats = {**base, "sentiment": sentiment}

    await cache.set_json(cache_key, stats, ttl=30)
    return stats

