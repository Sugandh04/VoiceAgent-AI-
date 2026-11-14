"""
app/security/prompt_guard.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Prompt injection detection and response policy enforcement for the VoiceAgent AI
real-time voice pipeline.

Two-layer defence:
  Layer 1 – Input Guard  : sanitises caller speech before it reaches the LLM context.
  Layer 2 – Output Guard : validates Sarah's reply before it is handed to TTS.

Both layers are synchronous (called inline in the hot audio path) and must remain
< 1 ms on average to preserve sub-120 ms end-to-end latency.
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger("prompt-guard")


class ThreatLevel(str, Enum):
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class GuardResult:
    threat_level: ThreatLevel
    reason: Optional[str]
    sanitized_text: str          # text safe to pass to LLM / TTS
    was_modified: bool


# ─── Injection Pattern Library ───────────────────────────────────────────────
# Each tuple: (compiled_regex, human-readable reason)
_INJECTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Role-override attempts
    (re.compile(r"\bignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instruction|prompt|context|message)s?\b", re.I), "role-override: ignore instructions"),
    (re.compile(r"\bact\s+as\b.{0,40}\b(admin|root|god|system|developer|openai|gpt)\b", re.I), "role-override: act as privileged entity"),
    (re.compile(r"\byou\s+are\s+(now|actually)\b.{0,40}\b(a\s+different|not\s+sarah|not\s+an\s+ai|human)\b", re.I), "role-override: identity reassignment"),
    (re.compile(r"\bnew\s+(system\s+)?prompt\b", re.I), "injection: new system prompt"),
    (re.compile(r"\bsystem\s*:\s*you\s+are\b", re.I), "injection: inline system message"),
    (re.compile(r"\[INST\]|\[\/INST\]|<<SYS>>|<</SYS>>", re.I), "injection: LLM control tokens"),

    # Jailbreak / DAN patterns
    (re.compile(r"\b(jailbreak|dan\s+mode|developer\s+mode|unrestricted\s+mode)\b", re.I), "jailbreak attempt"),
    (re.compile(r"\bdo\s+anything\s+now\b", re.I), "jailbreak: DAN"),
    (re.compile(r"\bpretend\s+(you\s+)?(have\s+no\s+restrictions?|are\s+unrestricted|can\s+do\s+anything)\b", re.I), "jailbreak: restrictions removal"),

    # Data exfiltration attempts
    (re.compile(r"\b(reveal|show|print|output|display|leak|dump)\s+(your\s+)?(system\s+prompt|instructions?|api\s+key|secret|password|token|config)\b", re.I), "exfiltration: system data"),
    (re.compile(r"\bwhat\s+(is|are)\s+your\s+(exact\s+)?(instruction|prompt|system\s+message)\b", re.I), "exfiltration: prompt probing"),

    # Code execution patterns
    (re.compile(r"<script\b|javascript:|eval\s*\(|exec\s*\(|__import__\s*\(", re.I), "injection: code execution"),
]

# ─── Output Policy Rules ─────────────────────────────────────────────────────
# Content that must NEVER appear in Sarah's spoken replies.
_BLOCKED_OUTPUT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(api[_\s]?key|secret[_\s]?key|access[_\s]?token|bearer\s+[a-z0-9\-_]{20,})\b", re.I), "leaked: api key / token"),
    (re.compile(r"\bsk[-_][a-zA-Z0-9]{20,}\b"), "leaked: OpenAI-style secret key"),
    (re.compile(r"\bmy\s+(system\s+prompt|instructions?)\s+(say|tell|state|are)\b", re.I), "disclosure: system prompt"),
    (re.compile(r"\b(ignore|override|bypass)\s+(your\s+)?(instructions?|restrictions?|rules?)\b", re.I), "policy: compliance break"),
]

# Topics Sarah must redirect — she is ONLY a sales agent
_OFF_TOPIC_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(write\s+(me\s+)?(a\s+)?([a-z0-9_\-]+\s+)*(code|script|essay|email|letter|program|sql|function)|translate\s+this|summarize\s+this\s+document)\b", re.I), "off-topic: general assistant task"),
    (re.compile(r"\b(medical|legal|financial)\s+advice\b", re.I), "off-topic: regulated advice"),
    (re.compile(r"\bpassword\s+(for|of|to)\b", re.I), "off-topic: credential request"),
]

# Safe redirect Sarah uses when output is off-topic
_SAFE_REDIRECT = (
    "I am Sarah from VoiceAgent AI and I am here to help you schedule a quick five-minute "
    "phone demo. Would tomorrow work for a quick call with our specialist?"
)


# ─── Public API ──────────────────────────────────────────────────────────────

def inspect_user_input(text: str) -> GuardResult:
    """
    Layer 1 — Input Guard.

    Checks caller speech transcript for prompt injection before it enters the
    LLM context.  Called synchronously in the agent's on-transcript hook.

    Returns a GuardResult; if threat_level is BLOCKED the caller speech should
    be suppressed and Sarah should give a polite non-answer.
    """
    if not text or not text.strip():
        return GuardResult(ThreatLevel.SAFE, None, text, False)

    cleaned = text.strip()

    for pattern, reason in _INJECTION_PATTERNS:
        if pattern.search(cleaned):
            logger.warning(
                f"[INPUT GUARD] 🚨 Injection detected | reason='{reason}' | "
                f"text='{cleaned[:120]}'"
            )
            # Strip the offending segment instead of blocking the whole utterance
            # so legitimate surrounding speech still reaches the LLM.
            sanitized = pattern.sub("[REDACTED]", cleaned)
            threat = ThreatLevel.BLOCKED if sanitized != cleaned else ThreatLevel.SUSPICIOUS
            return GuardResult(threat, reason, sanitized, True)

    return GuardResult(ThreatLevel.SAFE, None, cleaned, False)


def inspect_agent_response(text: str) -> GuardResult:
    """
    Layer 2 — Output Guard.

    Validates Sarah's LLM-generated reply before it is handed to TTS.
    Called synchronously before every session.say() call.

    If BLOCKED, replace with a safe sales redirect.
    If SUSPICIOUS, log and pass through (we do not want to interrupt a natural
    conversation for a false positive on voice).
    """
    if not text or not text.strip():
        return GuardResult(ThreatLevel.SAFE, None, text, False)

    # Hard-block: sensitive data leakage
    for pattern, reason in _BLOCKED_OUTPUT_PATTERNS:
        if pattern.search(text):
            logger.error(
                f"[OUTPUT GUARD] 🔴 BLOCKED response | reason='{reason}' | "
                f"text='{text[:120]}'"
            )
            return GuardResult(ThreatLevel.BLOCKED, reason, _SAFE_REDIRECT, True)

    # Soft-warn: off-topic content — replace with redirect
    for pattern, reason in _OFF_TOPIC_PATTERNS:
        if pattern.search(text):
            logger.warning(
                f"[OUTPUT GUARD] 🟡 Off-topic response redirected | reason='{reason}' | "
                f"text='{text[:120]}'"
            )
            return GuardResult(ThreatLevel.SUSPICIOUS, reason, _SAFE_REDIRECT, True)

    return GuardResult(ThreatLevel.SAFE, None, text, False)


def sanitize_for_llm_context(text: str) -> str:
    """
    Convenience wrapper: run input guard and return sanitized text.
    Callers should still check the GuardResult if they want to react to
    BLOCKED status (e.g. skip the turn entirely).
    """
    result = inspect_user_input(text)
    return result.sanitized_text
