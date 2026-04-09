from collections.abc import AsyncGenerator
from functools import lru_cache

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, settings
from app.db.session import async_session
from app.services.cache_service import CacheService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def get_cache() -> AsyncGenerator[CacheService, None]:
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield CacheService(client)
    finally:
        await client.aclose()


@lru_cache
def get_settings() -> Settings:
    return settings
