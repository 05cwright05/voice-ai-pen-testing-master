"""Domain models for strategy execution and persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


Category = Literal[
    "identity",
    "prompt_injection",
    "jailbreak",
    "voice_specific",
    "info_extraction",
    "social_engineering",
    "logic_state",
    "telephony",
]

Severity = Literal["low", "medium", "high", "critical"]


class Strategy(BaseModel):
    """Single attack strategy document."""

    strategy_id: str
    name: str
    category: Category
    enabled: bool = True
    prompt_template: str
    tags: list[str] = Field(default_factory=list)
    priority: int = 1
    success_rate: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class GroundTruth(BaseModel):
    """Identity and role claims that should remain stable throughout the call."""

    name: str | None = None
    is_human: bool | None = None
    role: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ConversationTurn(BaseModel):
    """Conversation payload used by attack/evaluator models."""

    speaker: Literal["attacker", "target", "system"]
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class TestResult(BaseModel):
    """Persisted per-strategy result."""

    test_run_id: str
    strategy_id: str
    category: Category
    passed: bool
    severity: Severity | None = None
    details: str
    conversation_excerpt: list[ConversationTurn] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class TestRun(BaseModel):
    """Top-level test execution record."""

    test_run_id: str
    status: Literal["created", "running", "completed", "failed"] = "created"
    target_number: str | None = None
    attacker_number: str | None = None
    room_name: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

