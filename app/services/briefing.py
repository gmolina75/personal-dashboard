"""MiniMax AI briefing service for generating daily summaries.

Features:
- Optimized prompt for lower token usage
- Fallback to deterministic briefing if API unavailable
- Token usage metrics for cost tracking
"""

import os
import time
import logging
import json
from typing import Optional
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

# Token estimation (rough)
TOKENS_PER_RECORD = 15  # source + title + priority
MAX_TOKENS_BUDGET = 1500  # Safe limit for 1M context model


async def generate_daily_briefing(records: list[dict]) -> str:
    """Generate AI briefing with optimized token usage.

    Uses low reasoning effort and truncated data to minimize costs.
    Falls back to deterministic briefing if API unavailable.
    """
    if not settings.minimax_api_key:
        return _deterministic_briefing(records)

    if not records:
        return "📭 No hay registros para generar el briefing de hoy."

    # Filter and sort by priority
    sorted_records = sorted(records, key=lambda r: r.get("priority", 0), reverse=True)
    top_records = sorted_records[:15]  # Limit for token budget

    # Build minimal prompt
    context_lines = []
    for r in top_records:
        # Only include essential fields
        context_lines.append(f"{r.get('source','?')[0].upper()}:{r.get('priority',0)}:{r.get('title','?')[:50]}")

    prompt = (
        f"Daily briefing in Spanish. "
        f"Data: {'|'.join(context_lines[:10])}. "
        f"Format: 5 lines: 1) main urgencia, 2) eventos, 3) delegar, "
        f"4) tarea clave, 5) cierre."
    )

    # Token budgeting
    estimated_tokens = len(prompt) * 1.3 + 500
    if estimated_tokens > MAX_TOKENS_BUDGET:
        logger.warning(f"Prompt too large ({estimated_tokens} tokens), using deterministic fallback")
        return _deterministic_briefing(records)

    try:
        import httpx
        start_time = time.time()

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.minimax.io/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.minimax_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "MiniMax-M3.1-Flash",
                    "reasoning_effort": "low",  # Optimized for speed/cost
                    "max_completion_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}]
                },
            )

        elapsed = time.time() - start_time
        logger.info(f"Briefing API call completed in {elapsed:.2f}s")

        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                return content
        else:
            logger.warning(f"Briefing API returned {resp.status_code}")

    except Exception as e:
        logger.warning(f"Briefing API error: {e}")

    return _deterministic_briefing(records)


def _deterministic_briefing(records: list[dict]) -> str:
    """Generate deterministic briefing without external API.

    This is used when:
    - API key not configured
    - API fails
    - Token budget exceeded
    """
    if not records:
        return "📭 No hay registros para el briefing. Sincroniza tus datos primero."

    # Sort by priority and time
    sorted_records = sorted(
        records,
        key=lambda r: (r.get("priority", 0) * -1, r.get("ts_start", 0))
    )

    # Generate briefing lines
    lines = []
    urgent_items = [r for r in sorted_records if r.get("priority", 0) >= 2][:2]
    events = [r for r in sorted_records if r.get("type") == "event"][:1]
    tasks = [r for r in sorted_records if r.get("type") == "task"][:1]

    # Line 1: Urgencia principal
    if urgent_items:
        lines.append(f"⚡ {urgent_items[0].get('title', 'Item urgente')}")
    else:
        lines.append("✅ Día tranquilo, sin urgencias inmediatas")

    # Line 2: Eventos destacados
    if events:
        lines.append(f"📅 {events[0].get('title', 'Evento')}")

    # Line 3: Tareas pendientes
    if tasks:
        lines.append(f"✅ {tasks[0].get('title', 'Tarea pendiente')}")

    # Line 4: Qué revisar
    others = [r for r in sorted_records if r.get("priority", 0) == 1][:2]
    if others:
        lines.append(f"👀 Revisar: {', '.join(o.get('title','?')[:30] for o in others)}")

    # Line 5: Cierre positivo
    lines.append("💪 ¡Excelente día para lograr metas! 🌟")

    return "\n".join(lines[:5])


def estimate_tokens(records: list[dict]) -> int:
    """Estimate token usage for a briefing request."""
    base_tokens = 100  # System + prompt overhead
    record_tokens = len(records) * TOKENS_PER_RECORD
    completion_tokens = 500  # Expected response
    return base_tokens + record_tokens + completion_tokens