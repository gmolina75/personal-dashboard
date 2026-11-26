# Design: Personal Dashboard en Python
**Fecha:** 2026-11-26  
**Estado:** Propuesto (espera aprobación del usuario)  
**Decisión del usuario validada:** FastAPI + Jinja2/HTMX, entregar Fase 1 completa (núcleo), briefing IA solo metadatos.

---

## 1. Propósito

Un dashboard personal que **centralice** toda tu vida digital: correo, calendario, tareas y datos auxiliares (salud, música, clima) accesibles desde la red local en cualquier dispositivo. El objetivo es **reducir el tiempo buscando información** y **ofrecer un briefing matutino accionable** elaborado por IA.

---

## 2. Principios de diseño

| Principio | Justificación |
|---|---|
| **Plugabilidad** | Cada conector expone una interfaz estable (`id, source, type, title, snippet, url, ts_start, ts_end, meta, priority`). Agregar un nuevo servicio es escribir un archivo, no tocar el resto. |
| **Caché offline** | Todo pasa por SQLite. Llamar a Google/Correo es opcional: si el servicio está caído, el dashboard sigue funcionando con últimos datos. |
| **Sync diferido** | Actualizaciones en background vía `APScheduler`. El usuario no espera a que se descarguen 10.000 correos. |
| **Seguridad de tokens** | Tokens y credenciales cifrados con DPAPI (Windows) → inutilizables en otro equipo. |
| **Personal mode OAuth** | Evita la expiración de 7 días de los tokens en modo Testing. Solo tu cuenta puede autorizar la app. |

---

## 3. Arquitectura del sistema

```
personal-dashboard/
├─ app/
│  ├─ core/
│  │  ├─ config.py          # Carga settings desde .env
│  │  ├─ db.py              # Motor SQLAlchemy + SQLite
│  │  ├─ oauth.py           # Registro y refresco de tokens OAuth
│  │  ├─ registry.py        # Registro dinámico de conectores
│  │  ├─ scheduler.py       # APScheduler background jobs
│  │  ├─ ai.py              # Llamada al endpoint de MiniMax
│  │  └─ security.py        # Cifrado DPAPI de credenciales
│  ├─ connectors/
│  │  ├─ gmail.py           # Mensajes con prioridad (vencer, palabra clave, etc.)
│  │  ├─ calendar.py        # Eventos del día + próximos 7 días
│  │  ├─ tasks.py           # Google Tasks → modelo Task
│  │  ├─ drive.py           | Listado de archivos críticos (documentos pendientes)
│  │  ├─ health_strava.py   # Pasos, entrenamientos, peso (Fase 2)
│  │  ├─ spotify.py         # Canciones vistas hoy, playlists activas (Fase 2)
│  │  ├─ youtube.py         # Videos vistos, historial recomendado (Fase 2)
│  │  ├─ weather.py         # Clima + alertas (Fase 2)
│  │  ├─ rss.py             # Feeds configurables (Fase 2)
│  │  ├─ github.py          # Issues de repitos (Fase 3)
│  │  ├─ notes.py           # Obsidian local o Notion (Fase 3)
│  │  └─ finance.py         # Parseo de correos bancarios (Fase 4)
│  ├─ models/
│  │  ├─ message.py         # Email normalizado
│  │  ├─ event.py           # Calendar event + tarea implícita
│  │  ├─ task.py            # Google Task + metadatos
│  │  ├─ metric.py          # Pasos, sueño, clima, stream
│  │  ├─ track.py           # Video/música visto
│  │  ├─ feed_item.py       # RSS/Noticia
│  │  └─ transaction.py     # Gasto
│  ├─ services/
│  │  ├─ priority.py        # Scoring de urgencia (fechas, palabras, remitente)
│  │  ├─ briefing.py        # Prompt estructurado + llamada a IA
│  │  └─ digest.py          # Resumen semanal
│  └─ web/
│     ├─ routes.py          # FastAPI router
│     ├─ templates/         # Jinja2 + HTMX fragments
│     └─ static/            # Tailwind CDN, Alpine.js
├─ data/
│  ├─ dashboard.db         # SQLite + WAL
│  └─ .tokens.enc          # Credenciales cifradas
├─ docs/
│  └─ superpowers/specs/
├─ .env                     # GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, MINIMAX_API_KEY
└─ AGENTS.md                # Instrucciones para agents secundarios
```

---

## 4. Modelos de datos unificados

### BaseRecord (abstracto)
```python
id: str           # UUID4, único global
source: str       # gmail, calendar, tasks, ...
type: str         # message, event, task, metric, track, feed, transaction
title: str        # Asunto / Título del evento
snippet: str      # Extracto (máx. 500 chars), SIN contenido completo de correo
url: str          # Enlace directo ( mensaje: threadId, evento: htmlLink, etc.)
ts_start: int     # Epoch ms
ts_end: int       # Epoch ms (0 para tasks)
meta: dict        # JSON libre (remitente, etiquetas, calificación, etc.)
priority: int     # -2 a +3, calculado por el servicio de prioridad
updated_at: int   # Epoch ms
```

### Registro específico
```python
Message(meta['sender'], meta['threadId'], meta['size'])
Event(meta['location'], meta['attendees'], meta['conferenceData'])
Task(meta['status'], meta['delegated_to'])
Metric(meta['source_device'], meta['steps'])
Track(meta['artist'], meta['videoId'], meta['platform'])
FeedItem(meta['author'], meta['category'], meta['link'])
Transaction(meta['bank'], meta['type'], meta['amount'])
```

---

## 5. OAuth flow (Personal Mode)

1. En el primer arranque, el dashboard detecta que `dashboard.db` no existe → guarda `GOOGLE_CLIENT_ID` en `.env`.
2. Usuario visita `http://localhost:8000/auth/google` → redirige a la URL de Personal mode onboarding de Google.
3. Al completar, Google entrega `refresh_token` y lo guarda cifrado.
4. En recargos posteriores, si el token está caducado, se refresca automáticamente.

**Ventaja:** sin verificación CASA, sin pantalla "app no verificada", sin expiración de 7 días.

---

## 6. UI / UX

### Página principal (dashboard)
```
+------------------------------------------------------------+
| 06:15 AM - Buen día, Giancarlo.  (botón refresh)        |
|------------------------------------------------------------|
|  Prioridades del día (IA)                                 |
|  1. Reunión con M. a las 10:00 - agenda + notas          |
|  2. Enviar documento a Laura - respuesta a su email urgent|
|  3. Revisar contrato - vencimiento hoy 18:00              |
|                                                            |
|  Calendario (hoy)         |  Tareas pendientes (vencer)   |
|  ┌──────────────────────┐ |  ┌───────────────────────────┐|
|  │10:00 - Reunión...  │ |  │[ ] Firma contrato        │|
|  │14:30 - Almuerzo    │ |  │[ ] Responder a Laura     │|
|  │16:00 - Llamada...  │ |  │[ ] Revisar documentos   │|
|  └──────────────────────┘ |  └───────────────────────────┘|
|  Emails recientes (sin cuerpo) |  Clima: 22° ☀️          |
|  ┌──────────────────────┐              +5° / nubes      |
|  │Laura - Doc adjunto  │                            🌧️ nieve mañana|
|  │M. - Reunión 10:00  │                              |
|  └──────────────────────┘                              |
+------------------------------------------------------------+
```

- **HTMX** para refrescar secciones sin recargar página.
- **Alpine.js** para pequeños estados (colapsar/expandir).
- **Tailwind CDN** → cero archivos CSS, cero build.

### Briefing de la IA
Prompt estructurado:
```
Contexto del día:
- Eventos hoy: [lista]
- Tareas vencer hoy: [lista]
- Correos urgentes (extractos): [lista]
- Pausa: clima, salud, agenda

Genera un briefing de 5 líneas en español:
1. Qué urgencia del día (máx. 1 línea)
2. Conflicto de agenda (2 líneas si hay, 1 si no)
3. Qué delegar (máx. 1 línea)
4. Qué hacer hoy (máx. 1 línea)
5. Cierre positivo
```

---

## 7. Seguridad y privacidad

| Aspecto | Implementación |
|---|---|
| **Tokens** | Cifrado DPAPI (Windows) → `security.py` usa `pycryptodome` cifrado con `CryptProtectData`. |
| **Datos en SQLite** | Encriptación a nivel de fila con SQLCipher (opcional, se evalúa en Fase 2). |
| **Acceso al dashboard** | PIN de 4 dígitos al primer acceso de la sesión, cookie de 30 min. |
| **Salida a IA** | Solo metadatos. El cuerpo del correo nunca sale. El prompt incluye: *"No muestres el contenido del correo, solo resume la acción que el remitente busca"*. |
| **Google Health API** | El usuario debe tener la app Google Health vinculada antes. No hay forma de evitar esto por hardware. |

---

## 8. Roadmap por fases

| Fase | Entregable | Timeline estimado |
|---|---|---|
| 1 | Núcleo: Gmail, Calendar, Tasks, Drive, briefing IA | 2-3 días |
| 2 | Salud (Strava/Health), Spotify, YouTube, clima, RSS | 1 semana |
| 3 | GitHub, notas (Obsidian local), delegar tareas → crear tareas | 3-4 días |
| 4 | Import financiero (CSV bancario, parseo de correos) | 2 días |

---

## 9. Decisiones pendientes (para el usuario)

> **Nota:** Esta spec usa las siguientes decisiones validadas por el usuario:
> - **Frontend:** FastAPI + Jinja2/HTMX
> - **Alcance v1:** Fase 1 completa (núcleo)
> - **IA privacidad:** Solo metadatos del correo

---

## 10. Checklist de calidad

- [ ] Verificar que todos los conectores normalizan a `BaseRecord`
- [ ] Agregar tests de unit para `priority.py`
- [ ] Documentar cómo rotar `GOOGLE_CLIENT_SECRET`
- [ ] Script de backup de `dashboard.db`
- [ ] Script de migración de datos si cambia el schema

---

**Especificación escrita y guardada.** Puedes revisarla en: `docs/superpowers/specs/2026-11-26-personal-dashboard-design.md`