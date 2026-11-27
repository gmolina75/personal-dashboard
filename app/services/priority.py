"""Priority calculation service with enhanced scoring.

Features:
- Urgency scoring based on keywords
- Time-based priority (events within 2 hours, tasks due today)
- Source weights
- Configurable via environment
"""

import os
import math
from datetime import datetime, timedelta
from typing import Optional


# Configuration from environment
URGENT_HOURS_THRESHOLD = int(os.getenv("URGENT_HOURS_THRESHOLD", "2"))
TODAY_HOURS = int(os.getenv("TODAY_HOURS", "24"))
HIGH_PRIORITY_BASE = int(os.getenv("HIGH_PRIORITY_BASE", "3"))
MEDIUM_PRIORITY_BASE = int(os.getenv("MEDIUM_PRIORITY_BASE", "1"))


def calculate_priority(source: str, data: dict, current_time: Optional[datetime] = None) -> int:
    """Calculate priority score for a record.

    Score components:
    1. Urgency keywords (urgente, hoy, vence, importante, asap, deadline)
    2. Time-based scoring (events within 2 hours, tasks due today)
    3. Source weight (calendar/tasks get bonus)

    Returns:
        int: Priority score (-2 to +3)
            -2: Low priority
            -1: Normal priority
             0: Medium priority
             1: High priority
             2: Urgent (due within 2 hours)
             3: Critical (due now or overdue)
    """
    if current_time is None:
        current_time = datetime.now()

    score = 0
    title = data.get("title", "").lower()
    snippet = data.get("snippet", "").lower()

    # 1. Urgency keywords
    urgent_words = ["urgente", "hoy", "vence", "importante", "asap", "deadline", "inmediato"]
    if any(w in title or w in snippet for w in urgent_words):
        score += MEDIUM_PRIORITY_BASE + 1

    # 2. Time-based scoring
    ts_start = data.get("ts_start")
    ts_end = data.get("ts_end")

    if ts_start:
        event_time = datetime.fromtimestamp(ts_start)
        hours_diff = (event_time - current_time).total_seconds() / 3600

        if hours_diff < 0:  # Overdue
            score += 3
        elif hours_diff <= 0.5:  # Within 30 minutes
            score += 3
        elif hours_diff <= 1:  # Within 1 hour
            score += 2
        elif hours_diff <= URGENT_HOURS_THRESHOLD:  # Within threshold
            score += 1

    elif ts_end:
        end_time = datetime.fromtimestamp(ts_end)
        hours_diff = (end_time - current_time).total_seconds() / 3600

        if hours_diff < 0:  # Already ended
            pass  # Don't penalize past events
        elif hours_diff < 1:  # Ending soon
            score += 2
        elif hours_diff < URGENT_HOURS_THRESHOLD:
            score += 1

    # 3. Source-specific scoring
    source_weights = {
        "calendar": 1,
        "tasks": 1,
        "gmail": 0,
        "drive": 0,
        "health": 0,
        "weather": 0,
    }
    score += source_weights.get(source, 0)

    # 4. Label-based bonus (email labels)
    meta = data.get("meta_json", {})
    labels = meta.get("labels", []) if isinstance(meta, dict) else []
    if any(l in ["URGENTE", "IMPORTANTE", "PRIORITARIO"] for l in labels):
        score += 1

    # Cap score to prevent overflow
    return min(score, 3)


def filter_by_priority(records: list[dict], min_priority: int = 0) -> list[dict]:
    """Filter records by minimum priority score."""
    return [r for r in records if calculate_priority(r.get("source", ""), r) >= min_priority]


def sort_by_priority(records: list[dict], current_time: Optional[datetime] = None) -> list[dict]:
    """Sort records by calculated priority (descending)."""
    return sorted(records, key=lambda r: calculate_priority(
        r.get("source", ""), r, current_time
    ), reverse=True)