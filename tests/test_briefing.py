import pytest
from unittest.mock import AsyncMock, patch
import asyncio
from app.services.briefing import generate_daily_briefing

def test_briefing_no_records():
    result = asyncio.run(generate_daily_briefing([]))
    assert 'No hay registros' in result or 'API key no configurada' in result
