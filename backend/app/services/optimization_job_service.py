"""Optimization job persistence and management."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.optimization_job import JobStatus, OptimizationJob


async def create_job(
    db: AsyncSession,
    input_sequence: str,
    parameters: dict,
    construct_id: uuid.UUID | None = None,
) -> OptimizationJob:
    job = OptimizationJob(
        input_sequence=input_sequence,
        parameters_json=parameters,
        construct_id=construct_id,
        status=JobStatus.PENDING,
    )
    db.add(job)
    await db.flush()
    return job


async def complete_job(
    db: AsyncSession,
    job: OptimizationJob,
    output_sequence: str,
    cai_before: float | None,
    cai_after: float | None,
) -> OptimizationJob:
    job.status = JobStatus.COMPLETED
    job.output_sequence = output_sequence
    job.cai_before = cai_before
    job.cai_after = cai_after
    await db.commit()
    await db.refresh(job)
    return job


async def fail_job(
    db: AsyncSession, job: OptimizationJob, error: str
) -> OptimizationJob:
    job.status = JobStatus.FAILED
    job.parameters_json = {**(job.parameters_json or {}), "error": error}
    await db.commit()
    await db.refresh(job)
    return job


async def get_job(
    db: AsyncSession, job_id: uuid.UUID
) -> OptimizationJob | None:
    result = await db.execute(
        select(OptimizationJob).where(OptimizationJob.id == job_id)
    )
    return result.scalar_one_or_none()
