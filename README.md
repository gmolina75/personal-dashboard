# 📊 Personal Dashboard

**Un dashboard personal en Python que centraliza tu vida digital: correo, calendario, tareas y datos auxiliares, accesibles desde la red local en cualquier dispositivo.**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-green.svg)](https://fastapi.tiangolo.com/)

## 🚀 Características

- **Sincronización de Google Workspace**: Gmail, Calendar, Tasks, Drive
- **Briefing matutino con AI**: Resumen diario en español con MiniMax
- **Seguridad de tokens**: Cifrado DPAPI (Windows) con fallback Fernet
- **Modo Personal OAuth**: Tokens permanentes, sin expiración de 7 días
- **UI responsive**: FastAPI + HTMX + Tailwind CSS
- **Almacenamiento local**: SQLite + sincronización en background

## 📦 Requisitos

- Python 3.14+
- Cuenta de Google Workspace (Personal Mode recomendado)
- API Key de MiniMax (opcional para briefing IA)

## 🔧 Instalación

```bash
git clone https://github.com/gmolina75/personal-dashboard.git
cd PersonalDashboard
python -m venv venv
.\venv\Scripts\activate  # Windows
# o
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## ⚙️ Configuración

Crea un archivo `.env` basado en `.env.example`:

```env
GOOGLE_CLIENT_ID=tu_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_client_secret
MINIMAX_API_KEY=  # Opcional
```

## 🏃‍♂️ Uso

1. **Iniciar el dashboard**:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

2. **Abrir en navegador**: http://localhost:8000

3. **Conectar Google** (primera vez):
   - Click en "Sincronizar"
   - Completa el OAuth en otra pestaña: http://localhost:8000/auth/google

4. **Ver el briefing IA**:
   - Click en "Briefing IA" para obtener tu resumen diario

## 🏗️ Arquitectura

```
personal-dashboard/
├─ app/
│  ├─ core/          # Config, DB, OAuth, Security
│  ├─ connectors/    # Gmail, Calendar, Tasks, Drive
│  ├─ models/        # SQLAlchemy RecordModel
│  ├─ services/      # Priority, Briefing
│  └─ web/           # Routes y Templates HTMX
├─ data/             # SQLite + tokens cifrados
├─ tests/            # Unit tests
└─ docs/             # Specs y plans
```

## 📚 Fases del proyecto

| Fase | Entregable | Estado |
|---|---|---|
| 1 | Núcleo: Gmail, Calendar, Tasks, Drive, briefing IA | ✅ Completado |
| 2 | Salud, Spotify, YouTube, clima, RSS | ⏳ Pendiente |
| 3 | GitHub, notas, delegar tareas → crear tareas | ⏳ Pendiente |
| 4 | Import financiero (CSV bancario) | ⏳ Pendiente |

## 🔐 Seguridad

- Tokens cifrados con **Windows DPAPI** (vinculados al usuario/máquina)
- **Nunca** el cuerpo del correo sale a la IA (solo metadatos)
- Acceso al dashboard con PIN de 4 dígitos
- Sin servidores externos, datos 100% locales

## 🤝 Contribuir

1. Fork del repositorio
2. Crear rama `feature/nueva-funcionalidad`
3. Commit con mensaje claro
4. Pull request

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE)

## 📞 Contacto

Giancarlo Molina - [@gmolina75](https://github.com/gmolina75)