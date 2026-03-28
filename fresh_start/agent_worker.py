from __future__ import annotations

import os

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import deepgram, elevenlabs, openai, silero

from app.config import get_settings
from app.prompts import SYSTEM_PROMPT

settings = get_settings()

os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
os.environ.setdefault("DEEPGRAM_API_KEY", settings.deepgram_api_key)
os.environ.setdefault("ELEVEN_API_KEY", settings.elevenlabs_api_key)
os.environ.setdefault("ELEVENLABS_API_KEY", settings.elevenlabs_api_key)


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(
            api_key=settings.deepgram_api_key,
            model="nova-3",
            interim_results=True,
            no_delay=True,
            endpointing_ms=25,
            filler_words=True,
            punctuate=True,
        ),
        llm=openai.LLM(
            model=settings.openai_model,
            temperature=0.8,
        ),
        tts=elevenlabs.TTS(
            api_key=settings.elevenlabs_api_key,
            voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
            model="eleven_turbo_v2_5",
            encoding="mp3_22050_32",
            chunk_length_schedule=[50, 100, 150, 200],
        ),
        vad=silero.VAD.load(),
        turn_handling={
            "endpointing": {"min_delay": 0.3, "max_delay": 2.0},
            "interruption": {
                "enabled": True,
                "min_duration": 0.5,
                "min_words": 0,
            },
        },
    )

    await session.start(
        room=ctx.room,
        agent=Agent(instructions=os.getenv("SYSTEM_PROMPT", SYSTEM_PROMPT).strip()),
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="voice-mvp-target",
        )
    )
