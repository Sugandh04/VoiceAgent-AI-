"""
app/models/call_content.py
━━━━━━━━━━━━━━━━━━━━━━━━━
CallContent model — user-defined call scripts / prompts injected into Sarah's
system context at dial time.  Examples: seasonal greetings, campaign-specific
pitches, regional language variants.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from datetime import datetime
from app.database import Base


class CallContent(Base):
    """
    Stores a named call script / prompt override that the authenticated user
    can apply to individual calls or entire campaigns.

    When ``is_active`` is True this content is merged into Sarah's base system
    prompt at the start of every new call session for the owning user.
    Only one CallContent per user can be active at a time (enforced at the
    router level).
    """

    __tablename__ = "call_contents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Human-readable label — shown in the UI picker
    title = Column(String(120), nullable=False)

    # e.g. "NEW_YEAR", "CHRISTMAS", "DIWALI", "PRODUCT_LAUNCH", "CUSTOM"
    content_type = Column(String(50), default="CUSTOM", nullable=False)

    # The actual prompt addendum injected before the base system prompt.
    # Keep concise (≤ 500 chars) to avoid inflating LLM context window.
    prompt_text = Column(Text, nullable=False)

    # Optional short greeting override (replaces GREETING_MESSAGE for this content)
    greeting_override = Column(String(500), nullable=True)

    # Only one active content per user at a time
    is_active = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
