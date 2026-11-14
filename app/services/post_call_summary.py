"""
app/services/post_call_summary.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Post-call AI summary and sentiment intelligence service.

After every call session ends, this service uses GPT-4o-mini / Sarvam LLM to
generate a structured evaluation of customer sentiment, connection depth,
and whether the caller was genuinely engaging or hanging up / resisting the AI.

Summary schema:
  {
    "outcome":               "DEMO_BOOKED" | "CALLBACK_REQUESTED" | "NOT_INTERESTED" | "IVR_DETECTED" | "INCOMPLETE",
    "sentiment":             "POSITIVE" | "NEUTRAL" | "NEGATIVE",
    "engagement_score":      1 – 10 (1 = cut call immediately, 10 = deep enthusiastic dialogue),
    "connection_status":     "GENUINE_CONVERSATION" | "EARLY_HANGUP" | "DISMISSED_AS_AI" | "BUSY_CALLBACK" | "NOT_INTERESTED" | "IVR",
    "ai_hesitation":         true | false (caller commented, resisted, or doubted talking to an AI),
    "key_points":            ["...", "..."],           # max 3 bullet points
    "objections":            ["Too busy", "..."],      # objections raised by the lead
    "next_action":           "...",                    # recommended follow-up
    "demo_slot":             "Tomorrow 3 PM" | null,   # if booked
    "lead_phone":            "+919876543210" | null,   # if captured
    "confidence":            0.0 – 1.0                 # model's confidence
  }
"""

import json
import logging
from typing import Optional

import httpx
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger("post-call-summary")

_SUMMARY_SYSTEM_PROMPT = """You are an expert sales call intelligence AI analyzing conversations between 
Sarah (an Indian AI sales representative for VoiceAgent AI) and potential business owners.

Evaluate whether the customer was genuinely connecting, interested, indifferent, or dismissing the call 
because they realized it's an AI or were uninterested.

Return ONLY valid JSON (no markdown fences, no explanation) with this exact schema:
{
  "outcome": one of ["DEMO_BOOKED", "CALLBACK_REQUESTED", "NOT_INTERESTED", "IVR_DETECTED", "INCOMPLETE"],
  "sentiment": one of ["POSITIVE", "NEUTRAL", "NEGATIVE"],
  "engagement_score": integer from 1 to 10 (1 = hung up immediately or cut off rudely, 5 = neutral question, 10 = enthusiastic connection),
  "connection_status": one of ["GENUINE_CONVERSATION", "EARLY_HANGUP", "DISMISSED_AS_AI", "BUSY_CALLBACK", "NOT_INTERESTED", "IVR"],
  "ai_hesitation": boolean (true if the caller asked 'Are you a robot/AI?', laughed, commented on the bot, or cut call specifically because it felt automated),
  "key_points": [list of up to 3 short strings summarizing what was discussed],
  "objections": [list of objections raised by the caller, empty list if none],
  "next_action": "short actionable next step for the sales team",
  "demo_slot": "day and time string if a demo was booked, otherwise null",
  "lead_phone": "10-digit mobile number if captured, otherwise null",
  "confidence": float between 0.0 and 1.0
}

Rules:
- If caller cut the call within 1-2 turns, set connection_status to "EARLY_HANGUP" and sentiment to "NEGATIVE"
- If caller mentioned bot/AI/computer voice dismissively, set ai_hesitation to true and connection_status to "DISMISSED_AS_AI"
- If caller engaged politely and answered questions, set connection_status to "GENUINE_CONVERSATION"
- If transcript is empty or telecom announcement, set outcome to "IVR_DETECTED" and connection_status to "IVR"
- Return ONLY the raw JSON object"""


async def generate_post_call_summary(
    transcript_lines: list[str],
    call_sid: str,
) -> Optional[dict]:
    """
    Generate a structured AI sentiment and connection summary for a completed call.

    Args:
        transcript_lines: List of "SPEAKER: text" strings from the conversation.
        call_sid: The call session ID (for logging context).

    Returns:
        Parsed summary dict, or None if generation fails.
    """
    if not transcript_lines:
        logger.info(f"[PostCallSummary] Empty transcript for {call_sid}, skipping.")
        return None

    transcript_text = "\n".join(transcript_lines)

    # Truncate very long transcripts to stay within token limits
    if len(transcript_text) > 6000:
        transcript_text = transcript_text[-6000:]
        logger.debug(f"[PostCallSummary] Transcript truncated to last 6000 chars for {call_sid}")

    messages = [
        {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": f"TRANSCRIPT:\n{transcript_text}"},
    ]

    # Try OpenAI GPT-4o-mini first
    if settings.OPENAI_API_KEY:
        summary = await _call_openai(messages, call_sid)
        if summary:
            return summary

    # Fall back to Sarvam LLM
    summary = await _call_sarvam(messages, call_sid)
    return summary


_openai_client: Optional[AsyncOpenAI] = None

def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client

async def _call_openai(messages: list[dict], call_sid: str) -> Optional[dict]:
    """Generate summary via OpenAI API using cached client instance."""
    try:
        client = _get_openai_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=512,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        summary = json.loads(raw)
        logger.info(
            f"[PostCallSummary] ✅ GPT-4o-mini summary for {call_sid}: "
            f"sentiment={summary.get('sentiment')} connection={summary.get('connection_status')}"
        )
        return summary
    except Exception as exc:
        logger.warning(f"[PostCallSummary] OpenAI failed for {call_sid}: {exc}")
        return None


async def _call_sarvam(messages: list[dict], call_sid: str) -> Optional[dict]:
    """Generate summary via Sarvam LLM API."""
    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.SARVAM_LLM_MODEL,
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.1,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(settings.SARVAM_LLM_URL, headers=headers, json=payload)
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            # Strip markdown code fences if Sarvam wraps in ```json ... ```
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            summary = json.loads(raw.strip())
            logger.info(
                f"[PostCallSummary] ✅ Sarvam summary for {call_sid}: "
                f"sentiment={summary.get('sentiment')}"
            )
            return summary
    except Exception as exc:
        logger.warning(f"[PostCallSummary] Sarvam failed for {call_sid}: {exc}")
        return None
