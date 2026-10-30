import uuid
import logging
from fastapi import APIRouter, Query, HTTPException
from livekit import api
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/token", tags=["LiveKit WebRTC Tokens"])

@router.get("")
async def get_livekit_token(
    room_name: str = Query(default=None, description="LiveKit WebRTC Room Name"),
    participant_name: str = Query(default="Web-User", description="Caller/User Name")
):
    """
    Generates a cryptographically signed WebRTC connection token.
    The frontend uses this to connect directly to the LiveKit WebRTC audio room.
    """
    if not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="LiveKit credentials missing in configuration")

    actual_room = room_name or f"room_{uuid.uuid4().hex[:8]}"
    participant_identity = f"user_{uuid.uuid4().hex[:6]}"

    token = api.AccessToken(
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET
    ).with_identity(participant_identity) \
     .with_name(participant_name) \
     .with_grants(api.VideoGrants(
         room_join=True,
         room=actual_room,
         can_publish=True,
         can_subscribe=True,
         can_publish_data=True
     ))

    jwt_token = token.to_jwt()

    logger.info(f"Generated LiveKit WebRTC Token for identity={participant_identity} in room={actual_room}")

    return {
        "serverUrl": settings.LIVEKIT_URL,
        "roomName": actual_room,
        "participantIdentity": participant_identity,
        "token": jwt_token
    }
