"""
app/routers/call_content_router.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRUD endpoints for user-defined call content (seasonal greetings, campaign
scripts, regional language variants, etc.).

GET    /api/call-content          — list all content for current user
POST   /api/call-content          — create new content
PUT    /api/call-content/{id}     — update title / prompt / greeting
DELETE /api/call-content/{id}     — delete content
POST   /api/call-content/{id}/activate — set as active (deactivates all others)
POST   /api/call-content/deactivate   — clear active content (revert to default)
GET    /api/call-content/active   — get the currently active content (or null)
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, Field, field_validator

from app.database import get_db
from app.models.call_content import CallContent
from app.models.user import User
from app.routers.auth_router import require_user

logger = logging.getLogger("call-content-router")
router = APIRouter(prefix="/api/call-content", tags=["Call Content / Scripts"])


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class CallContentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    content_type: str = Field(default="CUSTOM", max_length=50)
    prompt_text: str = Field(..., min_length=10, max_length=1000)
    greeting_override: Optional[str] = Field(default=None, max_length=500)

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        allowed = {"NEW_YEAR", "CHRISTMAS", "DIWALI", "EID", "HOLI",
                   "PRODUCT_LAUNCH", "SEASONAL", "CUSTOM"}
        v = v.upper().strip()
        if v not in allowed:
            raise ValueError(f"content_type must be one of {sorted(allowed)}")
        return v

    @field_validator("prompt_text")
    @classmethod
    def no_injection(cls, v: str) -> str:
        from app.security.prompt_guard import inspect_user_input, ThreatLevel
        result = inspect_user_input(v)
        if result.threat_level == ThreatLevel.BLOCKED:
            raise ValueError(
                f"Prompt text contains disallowed content: {result.reason}"
            )
        return result.sanitized_text


class CallContentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    content_type: Optional[str] = Field(default=None, max_length=50)
    prompt_text: Optional[str] = Field(default=None, min_length=10, max_length=1000)
    greeting_override: Optional[str] = Field(default=None, max_length=500)

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"NEW_YEAR", "CHRISTMAS", "DIWALI", "EID", "HOLI",
                   "PRODUCT_LAUNCH", "SEASONAL", "CUSTOM"}
        v = v.upper().strip()
        if v not in allowed:
            raise ValueError(f"content_type must be one of {sorted(allowed)}")
        return v

    @field_validator("prompt_text")
    @classmethod
    def no_injection(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        from app.security.prompt_guard import inspect_user_input, ThreatLevel
        result = inspect_user_input(v)
        if result.threat_level == ThreatLevel.BLOCKED:
            raise ValueError(
                f"Prompt text contains disallowed content: {result.reason}"
            )
        return result.sanitized_text


class CallContentResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content_type: str
    prompt_text: str
    greeting_override: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _get_owned_content(
    content_id: int, user_id: int, db: AsyncSession
) -> CallContent:
    """Fetch a CallContent record owned by the given user or raise 404."""
    res = await db.execute(
        select(CallContent).where(
            CallContent.id == content_id,
            CallContent.user_id == user_id,
        )
    )
    obj = res.scalars().first()
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call content not found or you do not have access to it.",
        )
    return obj


async def _deactivate_all(user_id: int, db: AsyncSession) -> None:
    """Set is_active=False on all content rows owned by this user."""
    await db.execute(
        update(CallContent)
        .where(CallContent.user_id == user_id)
        .values(is_active=False, updated_at=datetime.now(timezone.utc))
    )


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("", response_model=List[CallContentResponse])
async def list_call_content(
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit"),
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> List[CallContent]:
    """Return all call content scripts for the authenticated user."""
    res = await db.execute(
        select(CallContent)
        .where(CallContent.user_id == current_user.id)
        .order_by(CallContent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return res.scalars().all()


@router.get("/active", response_model=Optional[CallContentResponse])
async def get_active_content(
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[CallContent]:
    """Return the currently active call content, or null if default Sarah script is in use."""
    res = await db.execute(
        select(CallContent).where(
            CallContent.user_id == current_user.id,
            CallContent.is_active == True,  # noqa: E712
        )
    )
    return res.scalars().first()


@router.post("", response_model=CallContentResponse, status_code=status.HTTP_201_CREATED)
async def create_call_content(
    payload: CallContentCreate,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> CallContent:
    """Create a new call content script. Does NOT auto-activate it."""
    obj = CallContent(
        user_id=current_user.id,
        title=payload.title,
        content_type=payload.content_type,
        prompt_text=payload.prompt_text,
        greeting_override=payload.greeting_override,
        is_active=False,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    logger.info(
        f"[CallContent] Created '{obj.title}' (id={obj.id}) for user {current_user.id}"
    )
    return obj


@router.put("/{content_id}", response_model=CallContentResponse)
async def update_call_content(
    content_id: int,
    payload: CallContentUpdate,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> CallContent:
    """Update title, prompt text, or greeting override of an existing script."""
    obj = await _get_owned_content(content_id, current_user.id, db)

    if payload.title is not None:
        obj.title = payload.title
    if payload.content_type is not None:
        obj.content_type = payload.content_type.upper()
    if payload.prompt_text is not None:
        obj.prompt_text = payload.prompt_text
    if payload.greeting_override is not None:
        obj.greeting_override = payload.greeting_override

    obj.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call_content(
    content_id: int,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a call content script. Active scripts are deactivated before deletion."""
    obj = await _get_owned_content(content_id, current_user.id, db)
    await db.delete(obj)
    await db.commit()
    logger.info(
        f"[CallContent] Deleted content id={content_id} for user {current_user.id}"
    )


@router.post("/{content_id}/activate", response_model=CallContentResponse)
async def activate_call_content(
    content_id: int,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> CallContent:
    """
    Set a script as the active call content.
    Automatically deactivates any previously active script for this user.
    """
    obj = await _get_owned_content(content_id, current_user.id, db)
    await _deactivate_all(current_user.id, db)

    obj.is_active = True
    obj.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(obj)
    logger.info(
        f"[CallContent] Activated '{obj.title}' (id={obj.id}) for user {current_user.id}"
    )
    return obj


@router.post("/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_all_content(
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Deactivate all scripts — revert Sarah to her default base system prompt."""
    await _deactivate_all(current_user.id, db)
    await db.commit()
    return {"message": "All call content deactivated. Sarah will use default script."}
