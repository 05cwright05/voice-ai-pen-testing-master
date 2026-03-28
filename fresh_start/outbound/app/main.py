from __future__ import annotations

import json
import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from livekit import api
import uvicorn

from app.config import get_settings

logger = logging.getLogger("voice-mvp")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

settings = get_settings()

app = FastAPI(title="LiveKit Outbound Caller", version="0.2.0")


def _build_room_name() -> str:
    return f"outbound-call-{uuid4().hex[:10]}"


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/call")
async def start_outbound_call() -> dict[str, str]:
    room_name = _build_room_name()
    metadata = json.dumps({"phone_number": settings.outbound_target_number})

    logger.info(
        "Creating dispatch room=%s target=%s source=%s",
        room_name,
        settings.outbound_target_number,
        settings.outbound_source_number,
    )

    lkapi = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )
    try:
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="voice-mvp-attacker",
                room=room_name,
                metadata=metadata,
            )
        )
    except Exception as exc:
        logger.exception("Failed to create outbound dispatch")
        raise HTTPException(status_code=500, detail=f"Failed to start outbound call: {exc}") from exc
    finally:
        await lkapi.aclose()

    return {
        "status": "dispatch_created",
        "room": room_name,
        "agent_dispatch_id": dispatch.id,
        "target_number": settings.outbound_target_number,
        "source_number": settings.outbound_source_number,
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=9000, reload=False)
