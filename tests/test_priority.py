import pytest
from datetime import datetime, timedelta
from app.services.priority import calculate_priority, filter_by_priority, sort_by_priority

def test_priority_urgent_keywords():
    item = {"title": "URGENTE: Revisar contrato hoy", "snippet": "Por favor firmar", "meta": {"sender": "boss@company.com"}}
    score = calculate_priority("gmail", item)
    assert score >= 2

def test_priority_calendar_source():
    item = {"title": "Reunion importante", "snippet": "", "meta": {}}
    score = calculate_priority("calendar", item)
    assert score >= 1

def test_priority_tasks_source():
    item = {"title": "Tarea pendiente", "snippet": "", "meta": {}}
    score = calculate_priority("tasks", item)
    assert score >= 1

def test_priority_documents_not_specified():
    item = {"title": "Documento de proyecto", "snippet": "Contenido del doc", "meta": {}}
    score = calculate_priority("drive", item)
    assert score == 0

def test_priority_low_priority():
    item = {"title": "Nota sin urgencia", "snippet": "Algo normal", "meta": {}}
    score = calculate_priority("gmail", item)
    assert score == 0

# New tests for enhanced priority service

def test_priority_time_based_urgent():
    """Test that events within 2 hours get high priority."""
    soon = datetime.now() + timedelta(minutes=30)
    item = {
        "title": "Reunión urgente",
        "snippet": "En 30 minutos",
        "ts_start": int(soon.timestamp()),
        "meta": {}
    }
    score = calculate_priority("calendar", item)
    assert score >= 2

def test_priority_overdue_event():
    """Test that overdue events get critical priority."""
    past = datetime.now() - timedelta(hours=1)
    item = {
        "title": "Evento vencido",
        "snippet": "Debería haber ocurrido hace 1 hora",
        "ts_start": int(past.timestamp()),
        "meta": {}
    }
    score = calculate_priority("calendar", item)
    assert score >= 3

def test_priority_asap_keyword():
    """Test ASAP keyword detection."""
    item = {"title": "Necesito esto ASAP", "snippet": "", "meta": {}}
    score = calculate_priority("gmail", item)
    assert score >= 2

def test_priority_deadline_keyword():
    """Test deadline keyword detection."""
    item = {"title": "Deadline: entregar hoy", "snippet": "", "meta": {}}
    score = calculate_priority("tasks", item)
    assert score >= 3

def test_filter_by_priority():
    """Test filtering records by minimum priority."""
    records = [
        {"id": "1", "source": "gmail", "title": "URGENTE: tarea", "snippet": "", "meta_json": {}, "priority": 3, "ts_start": 0},
        {"id": "2", "source": "calendar", "title": " evento", "snippet": "", "meta_json": {}, "ts_start": int((datetime.now() + timedelta(hours=3)).timestamp())},
        {"id": "3", "source": "tasks", "title": " tarea", "snippet": "", "meta_json": {}, "ts_start": int((datetime.now() + timedelta(hours=3)).timestamp())},
    ]
    filtered = filter_by_priority(records, min_priority=2)
    assert len(filtered) >= 1  # At least the urgent one

def test_sort_by_priority():
    """Test sorting records by priority."""
    records = [
        {"id": "1", "source": "gmail", "priority": 1, "ts_start": 0},
        {"id": "2", "source": "calendar", "priority": 3, "ts_start": 0},
        {"id": "3", "source": "tasks", "priority": 2, "ts_start": 0},
    ]
    sorted_records = sort_by_priority(records)
    assert sorted_records[0]["priority"] == 3
    assert sorted_records[2]["priority"] == 1

def test_priority_no_timestamp():
    """Test priority calculation without timestamp."""
    item = {"title": "Evento sin fecha", "snippet": "", "meta": {}}
    score = calculate_priority("calendar", item)
    assert score >= 1  # Should still get source bonus

def test_priority_label_bonus():
    """Test priority bonus for urgent labels."""
    item = {
        "title": "Documento normal",
        "snippet": "Contenido",
        "meta_json": {"labels": ["URGENTE"]}
    }
    score = calculate_priority("gmail", item)
    assert score >= 1  # Label bonus