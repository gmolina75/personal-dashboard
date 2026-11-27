"""FastAPI main application entry point with routes, Jinja2 templates, HTMX UI, and APScheduler.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.core.db import init_db
from app.core.scheduler import start_scheduler, stop_scheduler
from app.web.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown hooks."""
    # Startup
    logger.info("Starting FastAPI application...")
    await init_db()
    start_scheduler()
    logger.info("Database initialized, scheduler started")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    stop_scheduler()
    logger.info("Scheduler stopped")

app = FastAPI(
    title="Personal Dashboard",
    description="FastAPI dashboard with Google Workspace integration and AI briefing",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for future HTML pages and widgets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if needed
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include web routes
app.include_router(router, prefix="")

# Root redirect to dashboard
@app.get("/", include_in_schema=False)
async def root_to_dashboard():
    """Redirect root to dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_redirect(request: Request):
    """Dashboard redirect - serves the same as root for backward compatibility."""
    from app.web.routes import dashboard
    return await dashboard(request)

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler."""
    templates = Jinja2Templates(directory="app/web/templates")
    return templates.TemplateResponse(
        {"request": request, "error": "Página no encontrada"},
        request.url.path,
        status_code=404
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)