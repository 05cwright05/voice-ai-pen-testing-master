from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from livekit import api
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.agents.beta.tools import EndCallTool
from livekit.plugins import deepgram, elevenlabs, openai, silero

from app.call_end_handler import on_outbound_call_end
from app.config import get_settings
from app.prompts import get_prompt

TRANSCRIPTS_DIR = Path(__file__).resolve().parent / "transcripts"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

settings = get_settings()
logger = logging.getLogger("voice-mvp.outbound")
logger.setLevel(logging.DEBUG)

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
        sip_participant = await ctx.api.sip.create_sip_participant(
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
    sip_call_id = str(getattr(sip_participant, "sip_call_id", "")).strip() or None
    logger.info("SIP call ID resolved: %s", sip_call_id or "(none)")
    transcript_lines: list[str] = []
    persisted = False

    async def _persist_call_eval(shutdown_reason: str = "") -> None:
        nonlocal persisted
        logger.info("=" * 60)
        logger.info(
            "[SHUTDOWN] _persist_call_eval triggered  room=%s  shutdown_reason=%r  already_persisted=%s",
            ctx.room.name, shutdown_reason, persisted,
        )

        if persisted:
            logger.warning("[SHUTDOWN] Already persisted — skipping duplicate call")
            return
        persisted = True

        logger.info(
            "[SHUTDOWN] In-memory transcript_lines count: %d", len(transcript_lines)
        )
        transcript_text = "\n".join(transcript_lines).strip()

        if not transcript_text:
            logger.info(
                "[SHUTDOWN] In-memory transcript empty, checking file: %s (exists=%s)",
                transcript_path, transcript_path.exists(),
            )
            if transcript_path.exists():
                transcript_text = transcript_path.read_text(encoding="utf-8").strip()
                logger.info(
                    "[SHUTDOWN] Loaded transcript from file: %d chars", len(transcript_text)
                )

        if not transcript_text:
            logger.warning(
                "[SHUTDOWN] Transcript is EMPTY after all fallbacks — skipping evaluation  room=%s",
                ctx.room.name,
            )
            return

        logger.info(
            "[SHUTDOWN] Transcript ready: %d chars, %d lines",
            len(transcript_text), transcript_text.count("\n") + 1,
        )
        logger.debug("[SHUTDOWN] Transcript preview (first 500 chars): %.500s", transcript_text)

        if not sip_call_id:
            logger.warning(
                "[SHUTDOWN] No SIP/Twilio call ID for room=%s — evaluation will lack metadata.call_id",
                ctx.room.name,
            )

        logger.info("[SHUTDOWN] Calling on_outbound_call_end() via asyncio.to_thread ...")
        try:
            result = await asyncio.to_thread(
                on_outbound_call_end,
                transcript_text,
                call_id=sip_call_id,
                additional_tags=["outbound"],
                notes=f"shutdown_reason={shutdown_reason}" if shutdown_reason else None,
            )
            logger.info(
                "[SHUTDOWN] SUCCESS — evaluation persisted  room=%s  doc_id=%s  call_id=%s  timestamp=%s",
                ctx.room.name,
                result.get("inserted_id"),
                sip_call_id or "(missing)",
                result.get("timestamp"),
            )
        except Exception:
            logger.exception(
                "[SHUTDOWN] FAILED to persist call-end evaluation  room=%s  call_id=%s",
                ctx.room.name, sip_call_id or "(missing)",
            )
        logger.info("=" * 60)

    logger.info("Registering _persist_call_eval as shutdown callback for room=%s", ctx.room.name)
    ctx.add_shutdown_callback(_persist_call_eval)

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
            voice_id=(
                os.getenv("OUTBOUND_ELEVENLABS_VOICE_ID")
                or os.getenv("ELEVENLABS_VOICE_ID")
            ),
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
            user_text = ev.transcript.strip()
            _write_line(transcript_path, "USER", user_text)
            transcript_lines.append(f"USER: {user_text}")
            logger.debug("[TRANSCRIPT] Captured USER line #%d: %.120s", len(transcript_lines), user_text)

    @session.on("conversation_item_added")
    def _on_conversation_item_added(ev) -> None:
        item = ev.item
        if getattr(item, "role", None) != "assistant":
            return

        text = getattr(item, "text_content", None)
        if text and text.strip():
            agent_text = text.strip()
            _write_line(transcript_path, "AGENT", agent_text)
            transcript_lines.append(f"AGENT: {agent_text}")
            logger.debug("[TRANSCRIPT] Captured AGENT line #%d: %.120s", len(transcript_lines), agent_text)

    system_prompt, intro_message = get_prompt()
    logger.info("Selected persona for this call — intro: %.80s", intro_message)

    await session.start(
        room=ctx.room,
        agent=Agent(
            instructions=os.getenv("SYSTEM_PROMPT", system_prompt).strip(),
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

    session.say(intro_message)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="voice-mvp-attacker",
        )
    )
