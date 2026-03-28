"""MongoDB persistence layer for strategies and results."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.collection import Collection

from attacker.models import Strategy, TestResult, TestRun


class MongoStore:
    """Small repository wrapper around Mongo collections."""

    def __init__(self) -> None:
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise ValueError("MONGO_URI is not set")

        db_name = os.getenv("MONGO_DB_NAME", "voice_ai_pentest")
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

        self.strategies: Collection = self.db["strategies"]
        self.results: Collection = self.db["results"]
        self.test_runs: Collection = self.db["test_runs"]

        self.strategies.create_index("strategy_id", unique=True)
        self.results.create_index([("test_run_id", 1), ("strategy_id", 1)])
        self.test_runs.create_index("test_run_id", unique=True)

    def get_enabled_strategies(self) -> list[Strategy]:
        """Return strategies sorted by priority descending."""
        docs = self.strategies.find({"enabled": True}).sort([("priority", -1), ("name", 1)])
        return [Strategy.model_validate(doc) for doc in docs]

    def create_test_run(self, run: TestRun) -> None:
        """Insert a new test run record."""
        self.test_runs.insert_one(run.model_dump())

    def set_test_run_status(self, test_run_id: str, status: str) -> None:
        """Update test run status and timestamp."""
        self.test_runs.update_one(
            {"test_run_id": test_run_id},
            {"$set": {"status": status, "updated_at": datetime.now(tz=timezone.utc)}},
        )

    def batch_write_results(self, results: list[TestResult]) -> None:
        """Write result docs for a test run."""
        if not results:
            return
        payload = [result.model_dump() for result in results]
        self.results.insert_many(payload)

    def update_strategy_success_rate(self, strategy_id: str) -> None:
        """Recompute strategy success rate from historical results."""
        total = self.results.count_documents({"strategy_id": strategy_id})
        if total == 0:
            return
        failures = self.results.count_documents({"strategy_id": strategy_id, "passed": False})
        success_rate = max(0.0, 1.0 - (failures / total))
        self.strategies.update_one(
            {"strategy_id": strategy_id},
            {"$set": {"success_rate": success_rate}},
        )

