"""Twilio webhook server for bridging calls into LiveKit SIP."""

from __future__ import annotations

import os

from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import Dial, VoiceResponse

app = FastAPI(title="target-webhook", version="0.1.0")


def _sip_uri_for_room(room_name: str) -> str:
    sip_domain = os.getenv("LIVEKIT_SIP_URI", "sip.livekit.local")
    return f"sip:{room_name}@{sip_domain}"


@app.get("/health")
async def health() -> dict[str, str]:
    """Health endpoint for uptime checks."""
    return {"status": "ok"}


@app.post("/voice", response_class=PlainTextResponse)
async def voice_webhook(
    request: Request,
    call_sid: str = Form(default="unknown-call"),
) -> str:
    """Return TwiML that dials the call into a LiveKit SIP room."""
    host = os.getenv("TARGET_ROOM_PREFIX", "target-medical")
    room_name = f"{host}-{call_sid}"
    sip_uri = _sip_uri_for_room(room_name)

    response = VoiceResponse()
    dial = Dial()
    dial.sip(sip_uri)
    response.append(dial)
    return str(response)

