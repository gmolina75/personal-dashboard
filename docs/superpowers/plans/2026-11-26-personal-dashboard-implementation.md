# Personal Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deliver Phase 1 of the Personal Dashboard in Python (FastAPI + Jinja2/HTMX, SQLite storage, Google Workspace sync for Gmail, Calendar, Tasks, Drive, and MiniMax AI briefing).

**Architecture:** Single FastAPI backend process, SQLite local store with WAL mode, background sync via APScheduler, encrypted token storage via Windows DPAPI, and server-rendered HTML views enhanced with HTMX and Tailwind CSS.

**Tech Stack:** Python 3.14, FastAPI, Uvicorn, SQLAlchemy, Aiosqlite, HTMX, Tailwind CSS, Jinja2, httpx, APScheduler, google-api-python-client, google-auth-oauthlib, cryptography.

## Global Constraints
- **Scope:** Phase 1 complete (Gmail, Calendar, Tasks, Drive, AI briefing).
- **Frontend:** FastAPI + Jinja2 + HTMX (no React, no Node).
- **AI Privacy:** Only metadata and snippets sent to MiniMax; email bodies never leave local storage.
- **OAuth:** Personal mode flow (no 7-day test token expiration, no CASA review).
- **Database:** Local SQLite at `data/dashboard.db`.

---

## Task 1: Project Skeleton, Configuration, and Database Setup

**Files:**
- Create: `app/__init__.py`
- Create: `app/core/__init__.py`
- Create: `app/core/config.py`
- Create: `app/core/db.py`
- Create: `app/core/security.py`
- Create: `app/models/__init__.py`
- Create: `app/models/record.py`
- Create: `tests/__init__.py`
- Create: `tests/test_security.py`
- Modify: `.env.example`

- [ ] **Step 1: Write failing test for DPAPI token encryption/decryption**
```python
import pytest
from app.core.security import encrypt_token, decrypt_token

def test_token_encryption():
    secret = "ya29.a0AfH6SM..."
    encrypted = encrypt_token(secret)
    assert encrypted != secret
    decrypted = decrypt_token(encrypted)
    assert decrypted == secret
```

- [ ] **Step 2: Run pytest to verify test fails**
Run: `pytest tests/test_security.py -v`
Expected: FAIL with ModuleNotFoundError or import error

- [ ] **Step 3: Implement `app/core/security.py` using Windows DPAPI (ctypes) or Fernet fallback**
```python
import os
from cryptography.fernet import Fernet

# Simple secure key setup using local app key
KEY_FILE = "data/.key"

def _get_or_create_key():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key

_fernet = Fernet(_get_or_create_key())

def encrypt_token(token: str) -> str:
    return _fernet.encrypt(token.encode("utf-8")).decode("utf-8")

def decrypt_token(encrypted_token: str) -> str:
    return _fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
```

- [ ] **Step 4: Run pytest to verify encryption test passes**
Run: `pytest tests/test_security.py -v`
Expected: PASS

- [ ] **Step 5: Implement `app/core/config.py` and `app/core/db.py`**
```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_client_id: str = ""
    google_client_secret: str = ""
    minimax_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./data/dashboard.db"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
```

- [ ] **Step 6: Implement `app/models/record.py` (BaseRecord SQLAlchemy model)**
```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Text, JSON

class Base(DeclarativeBase):
    pass

class RecordModel(Base):
    __tablename__ = "records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source: Mapped[str] = mapped_column(String(32), index=True) # gmail, calendar, tasks, drive
    type: Mapped[str] = mapped_column(String(32), index=True)   # message, event, task, document
    title: Mapped[str] = mapped_column(String(255))
    snippet: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(512), default="")
    ts_start: Mapped[int] = mapped_column(Integer, default=0, index=True)
    ts_end: Mapped[int] = mapped_column(Integer, default=0)
    meta_json: Mapped[dict] = mapped_column(JSON, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[int] = mapped_column(Integer, index=True)
```

- [ ] **Step 7: Commit Task 1**
```bash
git add app/ tests/ .env.example
git commit -m "feat: add project skeleton, security, config and database models"
```

---

## Task 2: Priority Service and Unified Registry

**Files:**
- Create: `app/services/priority.py`
- Create: `app/core/registry.py`
- Create: `tests/test_priority.py`

- [ ] **Step 1: Write failing test for priority calculation**
```python
import pytest
from app.services.priority import calculate_priority

def test_priority_urgent_keywords():
    item = {"title": "URGENTE: Revisar contrato hoy", "snippet": "Por favor firmar", "meta": {"sender": "boss@company.com"}}
    score = calculate_priority("gmail", item)
    assert score >= 2
```

- [ ] **Step 2: Run pytest**
Run: `pytest tests/test_priority.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `app/services/priority.py`**
```python
def calculate_priority(source: str, data: dict) -> int:
    score = 0
    title = data.get("title", "").lower()
    snippet = data.get("snippet", "").lower()
    
    urgent_words = ["urgente", "hoy", "vence", "importante", "asap", "deadline"]
    if any(w in title or w in snippet for w in urgent_words):
        score += 2
        
    if source == "calendar":
        score += 1
    elif source == "tasks":
        score += 1
        
    return score
```

- [ ] **Step 4: Run test to verify pass**
Run: `pytest tests/test_priority.py -v`
Expected: PASS

- [ ] **Step 5: Commit Task 2**
```bash
git add app/services/priority.py app/core/registry.py tests/test_priority.py
git commit -m "feat: add priority calculation service and registry"
```

---

## Task 3: Google Workspace Connectors (Gmail, Calendar, Tasks, Drive)

**Files:**
- Create: `app/connectors/base.py`
- Create: `app/connectors/gmail.py`
- Create: `app/connectors/calendar.py`
- Create: `app/connectors/tasks.py`
- Create: `app/connectors/drive.py`

- [ ] **Step 1: Implement connector base and mock/real sync logic for Google APIs**
```python
class BaseConnector:
    name: str = "base"
    async def fetch(self) -> list[dict]:
        raise NotImplementedError
```

- [ ] **Step 2: Implement Gmail, Calendar, Tasks, and Drive connectors using `google-api-python-client` and OAuth tokens from DB.**

- [ ] **Step 3: Commit Task 3**
```bash
git add app/connectors/
git commit -m "feat: add google workspace connectors for gmail, calendar, tasks and drive"
```

---

## Task 4: MiniMax AI Briefing Service

**Files:**
- Create: `app/services/briefing.py`
- Create: `tests/test_briefing.py`

- [ ] **Step 1: Implement `app/services/briefing.py` connecting to `https://api.minimax.io/v1/chat/completions`**
```python
import httpx
from app.core.config import settings

async def generate_daily_briefing(records: list[dict]) -> str:
    if not settings.minimax_api_key:
        return "⚠️ MiniMax API key no configurada. Resumen no disponible."
        
    summary_items = [f"- [{r['source']}] {r['title']} (prioridad {r['priority']})" for r in records[:25]]
    prompt = f"""Con base en los siguientes elementos del día:\n\n{'\n'.join(summary_items)}\n\nGenera un briefing matutino en español exacto de 5 líneas:
1. Urgencia principal del día.
2. Conflictos o eventos destacados.
3. Qué delegar o revisar rápido.
4. Tarea clave a cerrar hoy.
5. Cierre positivo motivador."""

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.minimax.io/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.minimax_api_key}"},
            json={
                "model": "MiniMax-M3.1-Flash",
                "reasoning_effort": "low",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30.0
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        return "Error al conectar con la IA de MiniMax."
```

- [ ] **Step 2: Commit Task 4**
```bash
git add app/services/briefing.py tests/test_briefing.py
git commit -m "feat: add minimax ai briefing service"
```

---

## Task 5: Background Scheduler, FastAPI Web App, and HTMX UI

**Files:**
- Create: `app/core/scheduler.py`
- Create: `app/web/routes.py`
- Create: `app/web/templates/index.html`
- Create: `main.py`
- Create: `requirements.txt`

- [ ] **Step 1: Create `requirements.txt` with all exact pinned dependencies**
```txt
fastapi==0.141.1
uvicorn==0.52.4
SQLAlchemy==2.0.52
aiosqlite==0.22.1
pydantic-settings==2.15.0
httpx==0.28.1
Jinja2==3.1.6
pandas==3.0.3
icalendar==7.3.0
google-api-python-client==2.201.0
google-auth==2.62.0
google-auth-oauthlib==1.2.0
cryptography==50.0.1
apscheduler==3.10.4
feedparser==6.0.11
rich==15.0.0
pytest==8.3.2
```

- [ ] **Step 2: Implement FastAPI app (`main.py`) with routes, Jinja2 templates, HTMX layout, and APScheduler background sync job.**

- [ ] **Step 3: Commit Task 5**
```bash
git add main.py requirements.txt app/core/scheduler.py app/web/
git commit -m "feat: add fastapi backend, background scheduler and htmx frontend UI"
```

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-11-26-personal-dashboard-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**