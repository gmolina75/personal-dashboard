import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from app.services.briefing import generate_daily_briefing, _deterministic_briefing, estimate_tokens

def test_briefing_no_records():
    result = asyncio.run(generate_daily_briefing([]))
    assert 'No hay registros' in result or 'API key no configurada' in result

def test_deterministic_briefing_no_records():
    """Test deterministic briefing with no records."""
    result = _deterministic_briefing([])
    assert 'No hay registros' in result or 'Sincroniza' in result

def test_deterministic_briefing_with_urgencies():
    """Test deterministic briefing prioritizes urgent items."""
    records = [
        {"id": "1", "source": "gmail", "priority": 3, "ts_start": 0, "title": "URGENTE: Firmar contrato", "type": "task"},
        {"id": "2", "source": "calendar", "priority": 2, "ts_start": 0, "title": "Reunión importante", "type": "event"},
        {"id": "3", "source": "tasks", "priority": 1, "ts_start": 0, "title": "Tarea normal", "type": "task"},
    ]
    result = _deterministic_briefing(records)
    lines = result.split('\n')
    assert len(lines) <= 5
    # First line should be urgent
    assert 'URGENTE' in lines[0] or '✅' in lines[0]

def test_estimate_tokens():
    """Test token estimation."""
    records = [{"id": str(i), "source": "gmail", "title": f"Tarea {i}", "priority": 1} for i in range(10)]
    tokens = estimate_tokens(records)
    # Should be reasonable
    assert tokens > 0
    assert tokens < 5000  # Should not be excessive

def test_briefing_api_error_fallback():
    """Test that API errors fall back to deterministic briefing."""
    records = [
        {"id": "1", "source": "gmail", "priority": 2, "ts_start": 0, "title": "Tarea", "type": "task"},
    ]
    
    with patch('app.services.briefing.settings') as mock_settings:
        mock_settings.minimax_api_key = "fake-key-for-testing"
        async def mock_post(*args, **kwargs):
            raise Exception("Network error")
        
        with patch('httpx.AsyncClient.post', side_effect=mock_post):
            result = asyncio.run(generate_daily_briefing(records))
            # Should fall back to deterministic
            assert '✅' in result or 'Tarea' in result or 'Día tranquilo' in result or '📭' in result
