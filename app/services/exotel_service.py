import httpx
import logging
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class ExotelService:
    def __init__(self):
        self.account_sid = settings.EXOTEL_ACCOUNT_SID
        self.api_key = settings.EXOTEL_API_KEY
        self.api_token = settings.EXOTEL_API_TOKEN
        self.caller_id = settings.EXOTEL_CALLER_ID
        self.app_id = settings.EXOTEL_APP_ID

    async def initiate_outbound_call(self, destination_number: str, custom_field: str = "") -> Dict[str, Any]:
        """
        Triggers an outbound PSTN call via Exotel's REST API:
        POST https://<api_key>:<api_token>@api.exotel.com/v1/Accounts/<account_sid>/Calls/connect.json
        """
        if not self.account_sid or not self.api_key or not self.api_token:
            logger.warning("Exotel credentials not configured in .env. Simulating call.")
            return {
                "success": False,
                "message": "Exotel credentials missing in .env"
            }

        url = f"https://api.exotel.com/v1/Accounts/{self.account_sid}/Calls/connect.json"
        
        data = {
            "From": destination_number,
            "CallerId": self.caller_id,
            "Url": f"http://my.exotel.com/{self.account_sid}/exomls/{self.app_id}",
            "CustomField": custom_field,
            "CallType": "trans"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, auth=(self.api_key, self.api_token), data=data)
                if response.status_code == 200:
                    result = response.json()
                    call_sid = result.get("Call", {}).get("Sid")
                    logger.info(f"Exotel outbound call initiated: CallSid={call_sid} to={destination_number}")
                    return {"success": True, "call_sid": call_sid, "data": result}
                else:
                    logger.error(f"Exotel API error ({response.status_code}): {response.text}")
                    return {"success": False, "status_code": response.status_code, "error": response.text}
            except Exception as e:
                logger.error(f"Failed to initiate Exotel call: {e}")
                return {"success": False, "error": str(e)}

exotel_service = ExotelService()
