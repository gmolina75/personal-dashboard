"""MiniMax AI briefing service for generating daily summaries.
"""

import httpx
from app.core.config import settings

async def generate_daily_briefing(records: list[dict]) -> str:
    if not settings.minimax_api_key:
        return "⚠️ MiniMax API key no configurada. Resumen no disponible."
    
    if not records:
        return "📭 No hay registros para generar el briefing de hoy."
    
    summary_items = [f"- [{r['source']}] {r['title']} (prioridad {r['priority']})" for r in records[:25]]
    prompt = f"""Con base en los siguientes elementos del día:

{chr(10).join(summary_items)}

Genera un briefing matutino en español exacto de 5 líneas:
1. Urgencia principal del día.
2. Conflictos o eventos destacados.
3. Qué delegar o revisar rápido.
4. Tarea clave a cerrar hoy.
5. Cierre positivo motivador."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.minimax.io/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.minimax_api_key}"},
                json={
                    "model": "MiniMax-M3.1-Flash",
                    "reasoning_effort": "low",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"Error al conectar con la IA de MiniMax (status: {resp.status_code})."
    except Exception as e:
        return f"Error al conectar con la IA de MiniMax: {str(e)}"