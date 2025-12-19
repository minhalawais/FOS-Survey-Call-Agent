"""
FOS Survey Agent - LiveKit Voice Agent
Production-grade Urdu survey agent using LiveKit stack

Components:
- Silero VAD v5 for speech detection
- Faster-Whisper Turbo for Urdu STT
- Qwen 2.5 via Ollama for survey logic
- Indic Parler-TTS for Urdu voice synthesis
"""

import os
import asyncio
from dotenv import load_dotenv
from loguru import logger

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, JobContext
from livekit.plugins import silero

from .survey_brain import SurveyBrain
from .stt_whisper import WhisperSTT
from .tts_indic import IndicTTS

# Load environment
load_dotenv()


class SurveyAgent(Agent):
    """
    LiveKit Voice Agent for Urdu Surveys.
    
    Handles real-time voice conversation with:
    - VAD for speech detection
    - STT for Urdu transcription
    - LLM for survey state management
    - TTS for natural Urdu responses
    """
    
    def __init__(self):
        # Initialize survey brain
        brain = SurveyBrain()
        
        # Initialize Agent with STT, LLM, TTS
        super().__init__(
            instructions="You are a survey assistant conducting an Urdu language survey.",
            stt=WhisperSTT(),
            llm=brain,  # SurveyBrain acts as LLM
            tts=IndicTTS(),
        )
    
    async def on_enter(self):
        """Called when agent joins the room."""
        logger.info("Survey agent joined the room")
        
        # Send initial greeting
        self.session.generate_reply(
            instructions="Greet the user in Urdu and begin the survey.",
            allow_interruptions=True
        )


def create_agent():
    """Factory function for creating agent instances."""
    return SurveyAgent()


async def entrypoint(ctx: JobContext):
    """
    LiveKit agent entrypoint.
    
    This is called by livekit-agents framework when a new room is created.
    """
    logger.info(f"Connecting to room: {ctx.room.name}")
    
    # Connect to room
    await ctx.connect()
    
    # Wait for participant
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")
    
    # Create VAD
    vad = silero.VAD.load(
        min_speech_duration=0.1,
        min_silence_duration=0.5,
        activation_threshold=0.5
    )
    
    # Create agent session
    session = AgentSession(
        vad=vad,
        min_endpointing_delay=0.5,
        max_endpointing_delay=5.0,
    )
    
    # Start the session with our SurveyAgent
    await session.start(
        room=ctx.room,
        agent=SurveyAgent(),
    )
    
    logger.info("Agent session started")


if __name__ == "__main__":
    # Run in development mode
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            ws_url=os.getenv("LIVEKIT_URL"),
        )
    )
