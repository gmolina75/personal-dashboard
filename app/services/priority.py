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