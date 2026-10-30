from fastapi import APIRouter, Request, Query, Response, HTTPException
import logging
from app.config import settings

logger = logging.getLogger("whatsapp-router")
router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Webhook verification endpoint for Meta / WhatsApp Cloud API.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.info("✅ WhatsApp Webhook verified successfully!")
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@router.post("/webhook")
async def handle_incoming_message(request: Request):
    """
    Handles incoming messages and status delivery receipts from WhatsApp.
    """
    body = await request.json()
    logger.info(f"📨 Incoming WhatsApp event: {body}")
    return {"status": "EVENT_RECEIVED"}
