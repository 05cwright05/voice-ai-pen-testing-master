"""Attack test orchestration controller."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from attacker.attack_llm import AttackLLM
from attacker.db import MongoStore
from attacker.evaluator import ResponseEvaluator
from attacker.ground_truth import GroundTruthTracker
from attacker.models import ConversationTurn, Strategy, TestResult, TestRun


@dataclass
class PendingAction:
    """Action hints consumed by the next turn."""

    hint: str | None = None
    interrupt_next: bool = False


class AttackController:
    """Coordinates strategy progression, evaluation, and persistence."""

    def __init__(self) -> None:
        self.store = MongoStore()
        self.attack_llm = AttackLLM()
        self.evaluator = ResponseEvaluator()
        self.truth_tracker = GroundTruthTracker()
        self.pending_action = PendingAction()

        self.test_run_id = f"run_{uuid.uuid4().hex[:12]}"
        self.strategies: list[Strategy] = []
        self.strategy_index = 0
        self.results: list[TestResult] = []
        self.history: list[ConversationTurn] = []

    async def initialize(
        self,
        room_name: str | None = None,
        target_number: str | None = None,
        attacker_number: str | None = None,
    ) -> None:
        """Load strategy set and create test-run record."""
        self.strategies = self.store.get_enabled_strategies()
        run = TestRun(
            test_run_id=self.test_run_id,
            status="running",
            room_name=room_name,
            target_number=target_number,
            attacker_number=attacker_number,
        )
        self.store.create_test_run(run)

    def current_strategy(self) -> Strategy:
        """Return active strategy, rotating if index overflows."""
        if not self.strategies:
            raise RuntimeError("No enabled strategies found in database.")
        if self.strategy_index >= len(self.strategies):
            self.strategy_index = len(self.strategies) - 1
        return self.strategies[self.strategy_index]

    def next_opening_line(self) -> str:
        """Initial greeting to establish baseline ground truth."""
        opening = "Hi there, who am I speaking with today?"
        self.history.append(ConversationTurn(speaker="attacker", message=opening))
        return opening

    def on_target_transcript(self, message: str) -> str:
        """Main decision loop executed each time the target speaks."""
        self.history.append(ConversationTurn(speaker="target", message=message))
        self.truth_tracker.ingest_target_message(message)

        strategy = self.current_strategy()
        decision = self.evaluator.evaluate(
            strategy=strategy,
            target_response=message,
            history=self.history,
            ground_truth=self.truth_tracker.truth,
        )

        self._apply_decision(strategy=strategy, decision=decision.details, action=decision.action)

        if self.truth_tracker.should_check():
            check_type, check_prompt = self.truth_tracker.build_check_prompt()
            self.pending_action.hint = f"Ground truth check: {check_type}"
            self.history.append(ConversationTurn(speaker="attacker", message=check_prompt))
            return check_prompt

        if decision.action == "move_to_next":
            self.strategy_index = min(self.strategy_index + 1, len(self.strategies) - 1)
        elif decision.action == "interrupt_next":
            self.pending_action.interrupt_next = True

        next_text = self.attack_llm.generate_next_utterance(
            strategy=self.current_strategy(),
            history=self.history,
            evaluator_hint=decision.hint or self.pending_action.hint,
        )
        self.pending_action.hint = None
        self.history.append(ConversationTurn(speaker="attacker", message=next_text))
        return next_text

    def _apply_decision(self, strategy: Strategy, decision: str, action: str) -> None:
        """Persist pass/fail outcomes when evaluator emits result actions."""
        if action not in {"mark_failure", "mark_pass"}:
            return
        passed = action == "mark_pass"
        result = TestResult(
            test_run_id=self.test_run_id,
            strategy_id=strategy.strategy_id,
            category=strategy.category,
            passed=passed,
            severity=None if passed else "high",
            details=decision,
            conversation_excerpt=self.truth_tracker.excerpt(self.history),
        )
        self.results.append(result)

    def finalize(self, success: bool = True) -> None:
        """Write results and close test run."""
        self.store.batch_write_results(self.results)
        for result in self.results:
            self.store.update_strategy_success_rate(result.strategy_id)
        self.store.set_test_run_status(
            test_run_id=self.test_run_id,
            status="completed" if success else "failed",
        )

