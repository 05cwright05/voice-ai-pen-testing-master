from __future__ import annotations

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

DB_NAME = "medical_office"

_clients_by_loop: dict[int, AsyncIOMotorClient] = {}
_databases_by_loop: dict[int, AsyncIOMotorDatabase] = {}


def init_mongo_client() -> AsyncIOMotorClient:
    """Initialize and cache a MongoDB client for the current event loop."""
    loop = asyncio.get_running_loop()
    loop_id = id(loop)

    if loop_id not in _clients_by_loop:
        settings = get_settings()
        client = AsyncIOMotorClient(settings.mongo_uri, io_loop=loop)
        _clients_by_loop[loop_id] = client
        _databases_by_loop[loop_id] = client[DB_NAME]

    return _clients_by_loop[loop_id]


def get_database() -> AsyncIOMotorDatabase:
    """Return the current loop's medical_office MongoDB database handle."""
    loop_id = id(asyncio.get_running_loop())
    if loop_id not in _databases_by_loop:
        init_mongo_client()

    database = _databases_by_loop.get(loop_id)
    if database is None:
        raise RuntimeError("MongoDB client is not initialized")
    return database

