"""Custom adapter that plugs controller logic into LiveKit's LLM slot."""

from __future__ import annotations

from typing import Any

from attacker.controller import AttackController

try:
    from livekit.agents import llm as livekit_llm
except Exception:  # pragma: no cover - allows static import without dependency installed
    livekit_llm = None


class _AdapterBase:
    """Fallback base type when livekit is unavailable at import time."""

    pass


AdapterParent = livekit_llm.LLM if livekit_llm is not None else _AdapterBase


class AttackLLMAdapter(AdapterParent):
    """
    LiveKit-compatible custom LLM adapter.

    The real-time voice loop sends target transcripts into this adapter. It delegates
    decision-making to `AttackController` and returns the next attacker utterance.
    """

    def __init__(self, controller: AttackController) -> None:
        if livekit_llm is not None:
            super().__init__()
        self.controller = controller

    async def complete(self, *args: Any, **kwargs: Any) -> Any:
        """
        Produce the next attacker text for the session.

        LiveKit's concrete method shape can vary by version; we accept flexible args
        and extract the most recent textual content heuristically.
        """
        incoming_text = self._extract_last_text(args=args, kwargs=kwargs)
        next_text = self.controller.on_target_transcript(incoming_text)
        if livekit_llm is None:
            return {"text": next_text}
        return livekit_llm.ChatChunk(text=next_text)

    @staticmethod
    def _extract_last_text(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
        """Best-effort extraction of a text message from framework callback payloads."""
        if "text" in kwargs and isinstance(kwargs["text"], str):
            return kwargs["text"]
        if "message" in kwargs and isinstance(kwargs["message"], str):
            return kwargs["message"]
        for value in reversed(args):
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                for key in ("text", "message", "content"):
                    found = value.get(key)
                    if isinstance(found, str):
                        return found
        return ""

