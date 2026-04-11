import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_session_id
from app.schemas.optimization import OptimizationRequest, OptimizationResponse
from app.services import codon_optimization_service, optimization_job_service

router = APIRouter()


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_codons(
    request: OptimizationRequest,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    # Create job record
    job = await optimization_job_service.create_job(
        db,
        input_sequence=request.sequence,
        parameters={
            "organism_tax_id": request.organism_tax_id,
            "strategy": request.strategy,
            "avoid_restriction_sites": request.avoid_restriction_sites,
            "target_gc_min": request.target_gc_min,
            "target_gc_max": request.target_gc_max,
            "avoid_repeats": request.avoid_repeats,
        },
        session_id=session_id,
    )

    try:
        result = codon_optimization_service.optimize_sequence(
            protein_sequence=request.sequence,
            organism_tax_id=request.organism_tax_id,
            strategy=request.strategy,
            avoid_restriction_sites=request.avoid_restriction_sites,
            target_gc_min=request.target_gc_min,
            target_gc_max=request.target_gc_max,
            avoid_repeats=request.avoid_repeats,
        )

        job = await optimization_job_service.complete_job(
            db,
            job,
            output_sequence=result["optimized_sequence"],
            cai_before=result["cai_before"],
            cai_after=result["cai_after"],
        )

        return OptimizationResponse(
            job_id=job.id,
            status=job.status,
            optimized_sequence=result["optimized_sequence"],
            cai_before=result["cai_before"],
            cai_after=result["cai_after"],
            gc_content=result["gc_content_after"],
        )
    except Exception as e:
        await optimization_job_service.fail_job(db, job, str(e))
        raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")


@router.get("/jobs/{job_id}", response_model=OptimizationResponse)
async def get_optimization_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    job = await optimization_job_service.get_job(db, job_id, session_id)
    if not job:
        raise HTTPException(status_code=404, detail="Optimization job not found")
    return OptimizationResponse(
        job_id=job.id,
        status=job.status,
        optimized_sequence=job.output_sequence,
        cai_before=job.cai_before,
        cai_after=job.cai_after,
        gc_content=None,
    )
