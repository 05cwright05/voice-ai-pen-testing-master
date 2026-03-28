from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    outbound_trunk_id: str
    outbound_target_number: str
    outbound_source_number: str
    openai_api_key: str
    openai_model: str
    elevenlabs_api_key: str
    deepgram_api_key: str

def get_settings() -> Settings:
    return Settings(
        livekit_url=_required("LIVEKIT_URL"),
        livekit_api_key=_required("LIVEKIT_API_KEY"),
        livekit_api_secret=_required("LIVEKIT_API_SECRET"),
        outbound_trunk_id=_required("OUTBOUND_TRUNK_ID"),
        outbound_target_number=os.getenv("OUTBOUND_TARGET_NUMBER", "").strip()
        or _required("TWILIO_PHONE_NUMBER1"),
        outbound_source_number=_required("TWILIO_PHONE_NUMBER2"),
        openai_api_key=_required("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        elevenlabs_api_key=_required("ELEVENLABS_API_KEY"),
        deepgram_api_key=_required("DEEPGRAM_API_KEY"),
    )
