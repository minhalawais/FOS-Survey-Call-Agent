"""
FOS Survey Agent - LiveKit API Routes
Token generation and room management for LiveKit.
"""

import os
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from livekit import api
from loguru import logger

router = APIRouter(tags=["LiveKit"])


class TokenRequest(BaseModel):
    """Request for LiveKit access token."""
    room_name: str
    participant_name: str
    survey_id: Optional[int] = None
    employee_id: Optional[int] = None


class TokenResponse(BaseModel):
    """LiveKit access token response."""
    token: str
    room_name: str
    ws_url: str


class RoomInfo(BaseModel):
    """Room information."""
    name: str
    participants: int
    created_at: int


@router.post("/token", response_model=TokenResponse)
async def get_token(request: TokenRequest):
    """
    Generate LiveKit access token for participant.
    
    This token allows a user to join the voice room.
    """
    try:
        api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
        api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")
        ws_url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        
        # Create token
        token = api.AccessToken(api_key, api_secret)
        token.with_identity(request.participant_name)
        token.with_name(request.participant_name)
        
        # Grant permissions
        grant = api.VideoGrants(
            room_join=True,
            room=request.room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        )
        token.with_grants(grant)
        
        # Add metadata
        if request.survey_id or request.employee_id:
            token.with_metadata(f"survey:{request.survey_id}:employee:{request.employee_id}")
        
        # Generate JWT
        jwt_token = token.to_jwt()
        
        logger.info(f"Generated token for {request.participant_name} in {request.room_name}")
        
        return TokenResponse(
            token=jwt_token,
            room_name=request.room_name,
            ws_url=ws_url
        )
    
    except Exception as e:
        logger.error(f"Token generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/room/{room_name}")
async def create_room(room_name: str):
    """
    Create a LiveKit room for survey session.
    """
    try:
        api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
        api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")
        ws_url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        
        # Create room service client
        room_service = api.RoomServiceClient(ws_url, api_key, api_secret)
        
        # Create room
        room = await room_service.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=300,  # 5 minutes
                max_participants=2   # User + Agent
            )
        )
        
        logger.info(f"Created room: {room_name}")
        
        return {
            "room_name": room.name,
            "sid": room.sid,
            "created_at": room.creation_time
        }
    
    except Exception as e:
        logger.error(f"Room creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/room/{room_name}")
async def delete_room(room_name: str):
    """
    Delete a LiveKit room.
    """
    try:
        api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
        api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")
        ws_url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        
        room_service = api.RoomServiceClient(ws_url, api_key, api_secret)
        await room_service.delete_room(api.DeleteRoomRequest(room=room_name))
        
        logger.info(f"Deleted room: {room_name}")
        
        return {"status": "deleted", "room_name": room_name}
    
    except Exception as e:
        logger.error(f"Room deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rooms")
async def list_rooms():
    """
    List all active LiveKit rooms.
    """
    try:
        api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
        api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")
        ws_url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        
        room_service = api.RoomServiceClient(ws_url, api_key, api_secret)
        rooms = await room_service.list_rooms(api.ListRoomsRequest())
        
        return {
            "rooms": [
                {
                    "name": room.name,
                    "sid": room.sid,
                    "participants": room.num_participants,
                    "created_at": room.creation_time
                }
                for room in rooms.rooms
            ]
        }
    
    except Exception as e:
        logger.error(f"Room listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
