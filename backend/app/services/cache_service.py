"""Redis caching wrapper with configurable TTL per resource type."""

import json

import redis.asyncio as aioredis

from app.config import settings

# Default TTLs in seconds (from settings)
TTL_GENE = settings.CACHE_TTL_GENE
TTL_PROTEIN = settings.CACHE_TTL_PROTEIN
TTL_ORGANISM = settings.CACHE_TTL_ORGANISM
TTL_CODON_TABLE = settings.CACHE_TTL_CODON_TABLE


class CacheService:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def get_cached(self, key: str) -> dict | None:
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_cached(self, key: str, value: dict, ttl: int = TTL_GENE) -> None:
        await self.redis.set(key, json.dumps(value), ex=ttl)

    async def invalidate(self, key: str) -> None:
        await self.redis.delete(key)

    @staticmethod
    def make_key(resource_type: str, identifier: str) -> str:
        return f"genbit:{resource_type}:{identifier}"
