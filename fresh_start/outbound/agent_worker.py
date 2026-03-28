from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from livekit import api
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.agents.beta.tools import EndCallTool
from livekit.plugins import deepgram, elevenlabs, openai, silero

from app.config import get_settings
from app.prompts import INTRO_MESSAGE, SYSTEM_PROMPT

TRANSCRIPTS_DIR = Path(__file__).resolve().parent / "transcripts"

settings = get_settings()
logger = logging.getLogger("voice-mvp.outbound")

os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
os.environ.setdefault("DEEPGRAM_API_KEY", settings.deepgram_api_key)
os.environ.setdefault("ELEVEN_API_KEY", settings.elevenlabs_api_key)
os.environ.setdefault("ELEVENLABS_API_KEY", settings.elevenlabs_api_key)


def _open_transcript(room_name: str) -> Path:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return TRANSCRIPTS_DIR / f"outbound_{room_name}_{ts}.txt"


def _write_line(path: Path, role: str, text: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {role}: {text}\n")


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    dial_info = json.loads(ctx.job.metadata or "{}")
    phone_number = str(dial_info.get("phone_number", settings.outbound_target_number)).strip()
    if not phone_number:
        raise ValueError("Missing phone_number in dispatch metadata and no OUTBOUND_TARGET_NUMBER set.")

    sip_participant_identity = phone_number

    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=settings.outbound_trunk_id,
                sip_call_to=phone_number,
                participant_identity=sip_participant_identity,
                wait_until_answered=True,
            )
        )
    except api.TwirpError as exc:
        sip_code = exc.metadata.get("sip_status_code")
        sip_status = exc.metadata.get("sip_status")
        raise RuntimeError(
            f"Failed to place outbound call (SIP {sip_code} {sip_status}): {exc}"
        ) from exc

    await ctx.wait_for_participant(identity=sip_participant_identity)

    transcript_path = _open_transcript(ctx.room.name)
    logger.info("Transcript file: %s", transcript_path)

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

    @session.on("user_input_transcribed")
    def _on_user_input_transcribed(ev) -> None:
        if ev.is_final and ev.transcript.strip():
            _write_line(transcript_path, "USER", ev.transcript.strip())

    @session.on("conversation_item_added")
    def _on_conversation_item_added(ev) -> None:
        item = ev.item
        if getattr(item, "role", None) != "assistant":
            return

        text = getattr(item, "text_content", None)
        if text and text.strip():
            _write_line(transcript_path, "AGENT", text.strip())

    await session.start(
        room=ctx.room,
        agent=Agent(
            instructions=os.getenv("SYSTEM_PROMPT", SYSTEM_PROMPT).strip(),
            tools=[
                EndCallTool(
                    extra_description=(
                        "Use this when the appointment inquiry is resolved "
                        "or the receptionist says goodbye."
                    ),
                ),
            ],
        ),
    )

    session.say(INTRO_MESSAGE)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="voice-mvp-attacker",
        )
    )
