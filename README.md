# 🎯 WatchDogs OSINT - Video Analysis System

Sistema de agentes multi-modal para análisis de video e imágenes usando LangGraph y GPT-5.1 Vision.

**Estado del Proyecto:** ✅ **Production-Ready** (95/100) - Auditoría completa realizada 2026-01-03

## 📋 Características

### 🤖 Sistema de Agentes Multi-Modal

- **LangGraph Native Parallelism** ✅: Ejecución paralela NATIVA de 4 agentes especializados
  - 🔍 **Vision Agent**: Análisis visual general de escenas y respuestas a preguntas específicas
  - 📝 **OCR Agent**: Extracción de texto (matrículas, carteles, documentos, señales)
  - 🎯 **Detection Agent**: Detección de objetos, personas, vehículos con conteo
  - 🌍 **Geolocation Agent**: Estimación de ubicación geográfica basada en clues visuales

### 🛡️ Patrones de Resiliencia (Production-Grade)

- **Retry Logic** ✅: Exponential backoff con tenacity (3 intentos, 2-10s wait)
- **Timeouts** ✅: 30 segundos por agente (configurable)
- **Circuit Breaker** ✅: Protección contra cascading failures (5 fallos → open)
- **Cache LRU** ✅: In-memory con límite de 500 entradas para prevenir memory leaks
- **Rate Limiting** ✅: 30 req/min general, 10 req/min para análisis por IP

### 🔒 Seguridad (Security Baseline Compliant)

- **No Hardcoded Secrets** ✅: Todas las API keys en variables de entorno
- **CORS Restrictivo** ✅: Solo orígenes permitidos (configurable)
- **Input Validation** ✅: Validación de tamaño de archivos y base64 (DoS prevention)
- **Base64 Size Limits** ✅: Máximo 10MB por frame (configurable)
- **Auto-cleanup** ✅: Videos temporales eliminados después de 1 hora

### 📊 Observabilidad y Métricas

- **Pydantic Validation** ✅: Validación completa de schemas con Pydantic models
- **Metrics Tracking** ✅: Latencia, success rate, error counts por agente
- **Structured Logging** ✅: Formato estándar con filename:lineno (Rule 19 compliant)
- **Health Checks** ✅: Endpoint `/api/health` para monitoreo
- **Metrics API** ✅: Endpoint `/api/metrics` con estadísticas detalladas
- **Dashboard en Tiempo Real** ✅: UI de monitoreo en `/dashboard.html`

### 🎨 Interfaz Web Intuitiva

- **Video Player** con controles completos
- **Captura de frames** en cualquier momento
- **Selección de ROI** (Region of Interest) para análisis focalizado
- **Chat conversacional** para preguntas sobre frames específicos
- **Resultados multi-formato**: JSON estructurado + Texto legible + Preview
- **Dashboard de monitoreo** con métricas en tiempo real

### ⚙️ Backend Flask Robusto

- **API REST** bien documentada con rate limiting
- **Procesamiento de imágenes** con PIL y base64
- **Orquestación LangGraph** con paralelismo nativo
- **Auto-cleanup** de archivos temporales
- **Docker multi-stage build** optimizado
- **Health checks** y graceful shutdown

## 🚀 Instalación

### Requisitos

- Python 3.10+
- OpenAI API Key con acceso a GPT-5.1 - Vision

### Pasos

1. **Clonar el repositorio**:
```bash
cd WatchDogs-Osint-System
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**:

Crear archivo `.env` en la raíz del proyecto:

```env
OPENAI_API_KEY=sk-your-api-key-here

FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

TEMP_VIDEO_PATH=data/temp
MAX_VIDEO_SIZE_MB=100
VIDEO_RETENTION_HOURS=1
```

4. **Crear directorios necesarios**:
```bash
mkdir -p data/temp
```

## ▶️ Uso

### Iniciar el sistema con Docker Compose

```bash
# Construir e iniciar el servicio
docker compose up --build

# O en modo detached (background)
docker compose up -d

# Ver logs
docker compose logs -f

# Detener el servicio
docker compose down
```

El servidor estará disponible en:
- **Aplicación principal:** `http://localhost:5000`
- **Dashboard de monitoreo:** `http://localhost:5000/dashboard.html`
- **Health check:** `http://localhost:5000/api/health`
- **Métricas:** `http://localhost:5000/api/metrics`

### Comandos útiles

```bash
# Ver estado del servicio
docker compose ps

# Reiniciar el servicio
docker compose restart

# Ver logs en tiempo real
docker compose logs -f watchdogs

# Detener y eliminar volúmenes
docker compose down -v

# Reconstruir la imagen
docker compose build --no-cache
```

### Flujo de trabajo

1. **Abrir** la interfaz web en el navegador
2. **Subir** un archivo de video (MP4, AVI, MOV, MKV, WEBM)
3. **Reproducir** el video y pausar en el momento deseado
4. **Capturar** el frame actual
5. **Seleccionar** (opcional) una región de interés (ROI) dibujando un rectángulo
6. **Analizar** - Los 3 agentes procesarán la imagen en paralelo
7. **Ver resultados**:
   - **Tab Texto**: Reporte completo en formato legible
   - **Tab JSON**: Datos estructurados para procesamiento
   - **Tab Preview**: Visualización del frame con ROI marcado

## 📊 Ejemplo de Salida

### Reporte Texto:
```
================================================================================
REPORTE DE ANÁLISIS DE IMAGEN - SISTEMA DE AGENTES OSINT
================================================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📸 1. ANÁLISIS VISUAL GENERAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

La escena muestra un entorno urbano exterior...
```

### JSON Estructurado:
```json
{
  "timestamp": "2025-01-08T10:30:00",
  "status": "success",
  "agents": {
    "vision": {
      "status": "success",
      "confidence": "high",
      "analysis": "..."
    },
    "ocr": {
      "status": "success",
      "has_text": true,
      "confidence": "high",
      "analysis": "..."
    },
    "detection": {
      "status": "success",
      "confidence": "high",
      "analysis": "..."
    }
  }
}
```

## 🏗️ Arquitectura

```
Frontend (HTML/JS/CSS)
    ↓
Flask API (/api/analyze-frame)
    ↓
ImageService (Procesamiento)
    ↓
LangGraph Coordinator
    ├─→ Vision Agent (GPT-4 Vision)
    ├─→ OCR Agent (GPT-4 Vision)
    └─→ Detection Agent (GPT-4 Vision)
    ↓
Combinador de Resultados
    ↓
JSON + Texto → Frontend
```

## 📁 Estructura del Proyecto

```
WatchDogs-Osint-System/
├── src/
│   ├── backend/
│   │   ├── app.py                 # Flask server
│   │   ├── config.py              # Configuración
│   │   ├── agents/
│   │   │   ├── coordinator.py     # LangGraph orchestrator
│   │   │   ├── vision_agent.py    # Análisis visual
│   │   │   ├── ocr_agent.py       # OCR
│   │   │   └── detection_agent.py # Detección
│   │   └── services/
│   │       ├── video_service.py   # Gestión de videos
│   │       └── image_service.py   # Procesamiento imágenes
│   └── frontend/
│       ├── index.html             # UI principal
│       └── static/
│           ├── css/
│           │   └── style.css
│           └── js/
│               ├── video-player.js
│               ├── roi-selector.js
│               └── api-client.js
├── data/
│   └── temp/                      # Videos temporales
├── tests/                         # Tests unitarios
├── requirements.txt
├── .env                           # Variables de entorno
└── README.md
```

## 🧪 Tests

```bash
pytest tests/ -v
```

## 🔒 Seguridad

- ✅ API Key nunca en código fuente (variables de entorno)
- ✅ Videos temporales auto-eliminados después de 1 hora
- ✅ Sin logs de frames para evitar leak de datos
- ✅ Validación de tipos y tamaños de archivo
- ✅ CORS restringido a orígenes permitidos
- ✅ Rate limiting por IP (30 req/min general, 10 req/min análisis)
- ✅ Base64 size validation (DoS prevention, max 10MB)
- ✅ Circuit breaker para protección contra API failures
- ✅ Input sanitization y validación con Pydantic

## 📊 Métricas de Calidad

**Auditoría Completa (2026-01-03):**
- **Score General:** 95/100 ⭐⭐⭐⭐⭐
- **Seguridad:** 95/100
- **Performance:** 85/100
- **Reliability:** 95/100
- **Code Quality:** 90/100

**Características Verificadas:**
- ✅ LangGraph Native Parallelism (4 agentes simultáneos)
- ✅ Retry Logic con Exponential Backoff
- ✅ Timeouts Configurables (30s default)
- ✅ Pydantic Validation (schemas completos)
- ✅ Metrics & Observability (tracking completo)
- ✅ Circuit Breaker Pattern (shared state)
- ✅ Cache LRU (max 500 entries)

Ver detalles en:
- `AUDIT_REPORT.md` - Auditoría técnica completa
- `CHANGELOG_FIXES.md` - Fixes críticos aplicados
- `docs/PROJECT_REVIEW.md` - Revisión de cumplimiento
- `historyMD/sessions/` - Registro de desarrollo

## 🤝 Contribución

Este proyecto sigue las reglas de desarrollo definidas en `.cursor/rules/`:
- Clean Code Principles
- Python Style Guide (PEP8)
- Security Baseline
- LLM Usage Best Practices
- Modern ML Workflow

## 📝 Licencia

Proyecto educativo para investigación OSINT.

## 🆘 Soporte

Para problemas o preguntas:
1. Verificar que `OPENAI_API_KEY` esté configurada correctamente
2. Revisar logs del servidor Flask
3. Verificar consola del navegador para errores de frontend

---

## 📁 Documentación del Proyecto

| Documento | Descripción |
|-----------|-------------|
| `README.md` | Este archivo - Guía principal |
| `docs/requirements.md` | Especificación completa de requisitos |
| `AUDIT_REPORT.md` | Auditoría técnica detallada (95/100) |
| `CHANGELOG_FIXES.md` | Registro de fixes críticos aplicados |
| `docs/PROJECT_REVIEW.md` | Revisión de cumplimiento de reglas |
| `docs/IMPROVEMENTS_PROPOSAL.md` | Propuestas de mejoras futuras |
| `diagrams/README.md` | Documentación de diagramas de arquitectura |
| `historyMD/README.md` | Registro de sesiones y decisiones técnicas |
| `tracking/project_tracking.csv` | Métricas de progreso y desarrollo |

---

**Powered by**: LangGraph + GPT-5.1 Vision + Flask + Pydantic + Tenacity + Vanilla JavaScript

**Status:** Production-Ready ✅ | **Quality Score:** 95/100 ⭐⭐⭐⭐⭐ | **Last Audit:** 2026-01-03

