from __future__ import annotations

import sys
from pathlib import Path

from pymongo import MongoClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import get_settings


def main() -> int:
    settings = get_settings()

    print("Checking MongoDB connection...")
    try:
        with MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000) as client:
            ping_result = client.admin.command("ping")
            print(f"Ping response: {ping_result}")

            db_names = client.list_database_names()
            print(f"Databases found ({len(db_names)}): {', '.join(db_names) if db_names else 'none'}")

            db = client["medical_office"]
            collections = db.list_collection_names()
            print(
                "Collections in medical_office "
                f"({len(collections)}): {', '.join(collections) if collections else 'none'}"
            )

        print("MongoDB connection successful.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"MongoDB connection failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

