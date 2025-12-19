"""
FOS Survey Agent - TTS Service Client
Client for Edge TTS service with proper Urdu support
"""

import httpx
from typing import Optional
from loguru import logger

from app.config import settings


class TTSService:
    """Client for Text-to-Speech service"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.piper_url
        self.timeout = 30.0
    
    async def synthesize(self, text: str, voice: str = None) -> Optional[bytes]:
        """
        Synthesize text to speech using Edge TTS.
        
        Args:
            text: Text to synthesize (Urdu supported)
            voice: Voice name (default: ur-PK-UzmaNeural)
            
        Returns:
            Audio bytes (MP3) or None on error
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/synthesize/urdu",
                    json={"text": text, "voice": voice}
                )
                response.raise_for_status()
                
                audio_bytes = response.content
                logger.info(f"TTS generated {len(audio_bytes)} bytes")
                return audio_bytes
                
        except httpx.TimeoutException:
            logger.error("TTS service timeout")
            return None
        except Exception as e:
            logger.error(f"TTS service error: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check if TTS service is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Global instance
tts_service = TTSService()


async def synthesize(text: str) -> Optional[bytes]:
    """Convenience function to synthesize speech"""
    return await tts_service.synthesize(text)
