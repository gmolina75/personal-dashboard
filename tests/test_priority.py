import pytest
from app.services.priority import calculate_priority

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