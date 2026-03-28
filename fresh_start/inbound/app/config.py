from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _as_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    twilio_auth_token: str
    livekit_sip_uri: str
    target_phone_number: str
    inbound_trunk_username: str
    inbound_trunk_password: str
    public_webhook_base_url: str
    validate_twilio_signature: bool
    openai_api_key: str
    openai_model: str
    elevenlabs_api_key: str
    deepgram_api_key: str
    mongo_uri: str

    @property
    def livekit_sip_host(self) -> str:
        return self.livekit_sip_uri.removeprefix("sip:")


def get_settings() -> Settings:
    return Settings(
        twilio_auth_token=_required("TWILIO_AUTH_TOKEN"),
        livekit_sip_uri=_required("LIVEKIT_SIP_URI"),
        target_phone_number=_required("TWILIO_PHONE_NUMBER1"),
        inbound_trunk_username=_required("LIVEKIT_INBOUND_TRUNK_USERNAME"),
        inbound_trunk_password=_required("LIVEKIT_INBOUND_TRUNK_PASSWORD"),
        public_webhook_base_url=_required("PUBLIC_WEBHOOK_BASE_URL").rstrip("/"),
        validate_twilio_signature=_as_bool("ENABLE_TWILIO_SIGNATURE_VALIDATION", True),
        openai_api_key=_required("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        elevenlabs_api_key=_required("ELEVENLABS_API_KEY"),
        deepgram_api_key=_required("DEEPGRAM_API_KEY"),
        mongo_uri=_required("MONGO_URI"),
    )
