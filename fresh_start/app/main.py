from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request, Response
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import Dial, VoiceResponse

from app.config import get_settings

logger = logging.getLogger("voice-mvp")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

settings = get_settings()
validator = RequestValidator(settings.twilio_auth_token)

app = FastAPI(title="Twilio ↔ LiveKit Voice MVP", version="0.1.0")


def _validation_url(request: Request) -> str:
    base = f"{settings.public_webhook_base_url}{request.url.path}"
    if request.url.query:
        return f"{base}?{request.url.query}"
    return base


async def _verify_twilio_signature(request: Request) -> dict[str, str]:
    form = dict(await request.form())
    if not settings.validate_twilio_signature:
        return {k: str(v) for k, v in form.items()}

    signature = request.headers.get("X-Twilio-Signature", "")
    valid = validator.validate(_validation_url(request), form, signature)
    if not valid:
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    return {k: str(v) for k, v in form.items()}


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/twilio/voice")
async def twilio_voice_webhook(request: Request) -> Response:
    form = await _verify_twilio_signature(request)
    call_sid = form.get("CallSid", "unknown")
    from_number = form.get("From", "unknown")

    logger.info("Inbound call received call_sid=%s from=%s", call_sid, from_number)

    response = VoiceResponse()
    dial = Dial(answer_on_bridge=True)
    dial.sip(
        f"sip:{settings.target_phone_number}@{settings.livekit_sip_host};transport=tcp",
        username=settings.inbound_trunk_username,
        password=settings.inbound_trunk_password,
    )
    response.append(dial)
    return Response(content=str(response), media_type="application/xml")


@app.post("/twilio/status")
async def twilio_status_webhook(request: Request) -> dict[str, str]:
    form = await _verify_twilio_signature(request)
    logger.info(
        "Twilio status callback call_sid=%s status=%s",
        form.get("CallSid", "unknown"),
        form.get("CallStatus", "unknown"),
    )
    return {"status": "received"}
