"""FastAPI web routes with Jinja2 templates and HTMX support.

Includes OAuth routes for Google Workspace Personal Mode authentication.
"""

from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime
from app.core.db import get_db, RecordModel
from app.core.scheduler import sync_all_sources
from app.core.oauth import get_oauth_manager
from app.core.security import encrypt_token, decrypt_token
import httpx
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


# ==================== OAuth Routes ====================

SCOPES = {
    "gmail": ["https://www.googleapis.com/auth/gmail.readonly"],
    "calendar": ["https://www.googleapis.com/auth/calendar"],
    "tasks": ["https://www.googleapis.com/auth/tasks.readonly"],
    "drive": ["https://www.googleapis.com/auth/drive.file"],
}


@router.get("/auth/google")
async def google_auth_redirect():
    """Redirect user to Google OAuth for Personal Mode authorization.

    This starts the Personal Mode flow where:
    - Tokens never expire (unlike Testing mode's 7-day limit)
    - No CASA assessment required
    - No app verification needed
    - Only your account can authorize it
    """
    oauth_manager = get_oauth_manager()

    # Combine all scopes we need
    all_scopes = []
    for scopes in SCOPES.values():
        all_scopes.extend(scopes)

    auth_url = oauth_manager.get_authorization_url(
        scopes=all_scopes,
        access_type="offline",
    )

    return RedirectResponse(url=auth_url)


@router.get("/auth/google/callback")
async def oauth_callback(
    request: Request,
    code: str = Query(None),
    state: str = Query(None),
):
    """Handle Google OAuth callback and exchange code for tokens.

    Stores encrypted tokens in the database (or file for initial setup).
    """
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    try:
        oauth_manager = get_oauth_manager()
        token_request = oauth_manager.build_token_request(code, state or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": token_request["client_id"],
                "client_secret": token_request["client_secret"],
                "code": token_request["code"],
                "grant_type": token_request["grant_type"],
                "redirect_uri": token_request["redirect_uri"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to exchange code for tokens")

    token_data = response.json()

    # Store encrypted tokens
    tokens = {
        "access_token": encrypt_token(token_data.get("access_token", "")),
        "refresh_token": encrypt_token(token_data.get("refresh_token", "")),
        "expires_at": datetime.now().timestamp() + token_data.get("expires_in", 3600),
    }

    # Save to token file (later will save to DB)
    os.makedirs("data", exist_ok=True)
    import json
    with open("data/google_tokens.json", "w") as f:
        json.dump(tokens, f)

    return HTMLResponse(
        """<div class='p-6 bg-green-50 rounded'>
            <h2 class='text-xl font-bold mb-2'>¡Autenticación exitosa!</h2>
            <p>Tu cuenta de Google está conectada al dashboard.</p>
            <a href='/dashboard' class='inline-block mt-3 px-4 py-2 bg-blue-600 text-white rounded'>Ver Dashboard</a>
        </div>"""
    )


# ==================== Dashboard Routes ====================

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

    # Get last sync time
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


# ==================== Health Check ====================

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    from app.core.config import settings
    
    checks = {
        "status": "healthy",
        "google_client_id_configured": bool(settings.google_client_id),
        "minimax_api_key_configured": bool(settings.minimax_api_key),
        "database": "ok",
        "timestamp": datetime.now().isoformat(),
    }
    
    return {"checks": checks}