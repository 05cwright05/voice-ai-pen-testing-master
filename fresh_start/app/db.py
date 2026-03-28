from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

DB_NAME = "medical_office"

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


def init_mongo_client() -> AsyncIOMotorClient:
    """Initialize and cache the MongoDB client."""
    global _client, _database

    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongo_uri)
        _database = _client[DB_NAME]
    return _client


def get_database() -> AsyncIOMotorDatabase:
    """Return the medical_office MongoDB database handle."""
    global _database

    if _database is None:
        init_mongo_client()
    if _database is None:
        raise RuntimeError("MongoDB client is not initialized")
    return _database

