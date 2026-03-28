from __future__ import annotations

import os

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import deepgram, elevenlabs, openai, silero

from app.config import get_settings

settings = get_settings()

# Normalize keys to names expected by provider SDKs/plugins.
os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
os.environ.setdefault("DEEPGRAM_API_KEY", settings.deepgram_api_key)
os.environ.setdefault("ELEVEN_API_KEY", settings.elevenlabs_api_key)
os.environ.setdefault("ELEVENLABS_API_KEY", settings.elevenlabs_api_key)


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        stt=elevenlabs.STT(api_key=settings.elevenlabs_api_key),
        llm=openai.LLM(model=settings.openai_model),
        tts=deepgram.TTS(api_key=settings.deepgram_api_key),
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=Agent(instructions=settings.system_prompt),
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="voice-mvp-target",
        )
    )
