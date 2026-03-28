"""LiveKit target agent entrypoint."""

from __future__ import annotations

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import deepgram, elevenlabs, openai, silero

from target.config import MEDICAL_RECEPTIONIST_PROMPT


async def entrypoint(ctx: JobContext) -> None:
    """Start a target receptionist agent session in the assigned room."""
    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o"),
        tts=elevenlabs.TTS(),
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=Agent(instructions=MEDICAL_RECEPTIONIST_PROMPT),
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )

