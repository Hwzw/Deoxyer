from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.dependencies import get_db, get_redis
from app.schemas.common import HealthCheckResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
):
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    redis_status = "ok"
    try:
        await redis_client.ping()
    except Exception:
        redis_status = "error"

    overall = "ok"
    if db_status == "error" or redis_status == "error":
        overall = "degraded"

    return HealthCheckResponse(
        status=overall,
        database=db_status,
        redis=redis_status,
    )
