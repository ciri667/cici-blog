"""Agent admin API: RSS source management, agent status, manual trigger."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.news import AgentRun, RssSource
from app.models.user import User
from app.schemas.news import (
    AgentRunResponse,
    AgentStatusResponse,
    RssSourceCreate,
    RssSourceResponse,
    RssSourceUpdate,
)

router = APIRouter(prefix="/admin", tags=["agent-admin"])


# --- RSS Sources CRUD ---


@router.get("/rss-sources", response_model=list[RssSourceResponse])
async def list_rss_sources(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RssSource).order_by(RssSource.id))
    return [RssSourceResponse.model_validate(s) for s in result.scalars().all()]


@router.post("/rss-sources", response_model=RssSourceResponse, status_code=201)
async def create_rss_source(
    data: RssSourceCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    source = RssSource(**data.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return RssSourceResponse.model_validate(source)


@router.put("/rss-sources/{source_id}", response_model=RssSourceResponse)
async def update_rss_source(
    source_id: int,
    data: RssSourceUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RssSource).where(RssSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="RSS 源不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(source, key, value)

    await db.commit()
    await db.refresh(source)
    return RssSourceResponse.model_validate(source)


@router.delete("/rss-sources/{source_id}", status_code=204)
async def delete_rss_source(
    source_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RssSource).where(RssSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="RSS 源不存在")
    await db.delete(source)
    await db.commit()


# --- Agent Status ---


@router.get("/agent/status", response_model=AgentStatusResponse)
async def agent_status(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentRun).order_by(AgentRun.started_at.desc()).limit(10)
    )
    runs = result.scalars().all()

    # Get next run time from scheduler
    next_run = None
    try:
        from app.agent.scheduler import scheduler

        job = scheduler.get_job("agent_pipeline")
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()
    except Exception:
        pass

    return AgentStatusResponse(
        recent_runs=[AgentRunResponse.model_validate(r) for r in runs],
        next_run_time=next_run,
    )


# --- Manual Trigger ---


@router.post("/agent/trigger")
async def trigger_pipeline(
    admin: User = Depends(require_admin),
):
    from app.agent.pipeline import run_pipeline

    asyncio.create_task(run_pipeline())
    return {"message": "Agent pipeline triggered"}
