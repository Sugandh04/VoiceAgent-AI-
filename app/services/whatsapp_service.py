import httpx
import logging
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger("whatsapp-service")

class WhatsAppService:
    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID

    async def send_demo_confirmation(
        self,
        to_phone: str,
        name: str = "Valued Customer",
        demo_time: str = "Upcoming Slot",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Sends an automated WhatsApp reminder/confirmation for the 5-minute phone demo call.
        """
        clean_phone = to_phone.replace("+", "").replace(" ", "").replace("-", "")
        if len(clean_phone) == 10:
            clean_phone = f"91{clean_phone}"

        message_body = (
            f"Hi {name}! 👋\n\n"
            f"Thank you for speaking with Sarah at *VoiceAgent AI*.\n\n"
            f"📞 *Demo Details:*\n"
            f"• *Type:* Quick 5-Minute Phone Call Demo\n"
            f"• *Scheduled Time:* {demo_time}\n"
            f"• *Format:* Our product specialist will call you directly on this number.\n\n"
            f"If you need to reschedule, simply reply to this message.\n\n"
            f"— Team VoiceAgent AI"
        )

        if not self.access_token or not self.phone_number_id:
            logger.info(f"📱 [WHATSAPP NOTIFICATION (Simulated)]: Message to {clean_phone}:\n{message_body}")
            return {"success": True, "simulated": True, "to": clean_phone, "message": message_body}

        url = f"https://graph.facebook.com/v20.0/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {"body": message_body}
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code in [200, 201]:
                    logger.info(f"✅ WhatsApp confirmation sent successfully to {clean_phone}")
                    return {"success": True, "response": resp.json()}
                else:
                    logger.error(f"❌ WhatsApp API error ({resp.status_code}): {resp.text}")
                    return {"success": False, "error": resp.text}
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp message: {e}")
            return {"success": False, "error": str(e)}

whatsapp_service = WhatsAppService()
