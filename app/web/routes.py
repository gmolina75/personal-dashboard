"""FastAPI web routes with Jinja2 templates and HTMX support.
"""

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime
from app.core.db import get_db, RecordModel
from app.core.scheduler import sync_all_sources

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Main dashboard view with records grouped by source."""
    
    # Build query
    query = select(RecordModel)
    if source:
        query = query.where(RecordModel.source == source)
    query = query.order_by(RecordModel.priority.desc(), RecordModel.ts_start.asc())
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Group by source
    grouped = {}
    for record in records:
        if record.source not in grouped:
            grouped[record.source] = []
        grouped[record.source].append(record)
    
    # Get distinct sources for filter
    sources_result = await db.execute(select(RecordModel.source).distinct())
    sources = [row[0] for row in sources_result.all()]
    
    # Get last sync time (from most recent updated_at)
    last_sync_result = await db.execute(
        select(func.max(RecordModel.updated_at))
    )
    last_sync_ts = last_sync_result.scalar()
    last_sync = datetime.fromtimestamp(last_sync_ts) if last_sync_ts else None
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "grouped": grouped,
            "sources": sources,
            "selected_source": source,
            "last_sync": last_sync,
            "total_records": len(records),
        }
    )

@router.get("/records/{record_id}", response_class=HTMLResponse)
async def record_detail(
    request: Request,
    record_id: str,
    db: AsyncSession = Depends(get_db)
):
    """HTMX partial for record detail modal."""
    result = await db.execute(
        select(RecordModel).where(RecordModel.id == record_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        return HTMLResponse("<div class='p-4 text-red-500'>Record not found</div>", status_code=404)
    
    return templates.TemplateResponse(
        "partials/record_detail.html",
        {"request": request, "record": record}
    )

@router.post("/sync", response_class=HTMLResponse)
async def manual_sync(request: Request, db: AsyncSession = Depends(get_db)):
    """Manual sync trigger endpoint."""
    await sync_all_sources()
    
    # Return updated stats
    result = await db.execute(select(func.count(RecordModel.id)))
    count = result.scalar()
    last_sync = datetime.now()
    
    return templates.TemplateResponse(
        "partials/sync_status.html",
        {
            "request": request,
            "total_records": count,
            "last_sync": last_sync,
            "message": "Sincronización completada"
        }
    )

@router.get("/briefing", response_class=HTMLResponse)
async def briefing(request: Request, db: AsyncSession = Depends(get_db)):
    """Get AI briefing for current records."""
    from app.services.briefing import generate_daily_briefing
    
    result = await db.execute(select(RecordModel))
    records = result.scalars().all()
    
    record_dicts = [
        {
            "id": r.id,
            "source": r.source,
            "type": r.type,
            "title": r.title,
            "snippet": r.snippet,
            "priority": r.priority,
        }
        for r in records
    ]
    
    briefing_text = await generate_daily_briefing(record_dicts)
    
    return templates.TemplateResponse(
        "partials/briefing.html",
        {"request": request, "briefing": briefing_text}
    )