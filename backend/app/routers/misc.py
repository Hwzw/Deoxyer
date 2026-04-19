from fastapi import APIRouter, Depends, Query

from app.dependencies import get_session_id
from app.schemas.misc import MiscSearchResult, MiscSequenceInfo
from app.services import misc_service

router = APIRouter()


@router.get("/search", response_model=MiscSearchResult)
async def search_misc(
    q: str | None = Query(None, description="Free-text query over name/category/type/notes"),
    sequence_type: str | None = Query(None, description="Filter by sequence type: 'protein' or 'dna'"),
    limit: int = Query(50, ge=1, le=200),
    session_id: str = Depends(get_session_id),
):
    return await misc_service.search_misc(q, sequence_type=sequence_type, limit=limit)


@router.get("/{misc_id}", response_model=MiscSequenceInfo)
async def get_misc(misc_id: str, session_id: str = Depends(get_session_id)):
    return await misc_service.get_misc(misc_id)
