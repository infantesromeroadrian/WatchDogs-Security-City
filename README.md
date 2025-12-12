# 🎯 WatchDogs OSINT - Video Analysis System

Sistema de agentes multi-modal para análisis de video e imágenes usando LangGraph y GPT-4 Vision.

## 📋 Características

- **Sistema de Agentes LangGraph**: Coordinación inteligente de 3 agentes especializados
  - 🔍 **Vision Agent**: Análisis visual general de escenas
  - 📝 **OCR Agent**: Extracción de texto (matrículas, carteles, documentos)
  - 🎯 **Detection Agent**: Detección de objetos, personas y vehículos

- **Interfaz Web Intuitiva**: 
  - Subida y reproducción de videos
  - Captura de frames en cualquier momento
  - Selección de ROI (Region of Interest) para análisis focalizado
  - Resultados en formato JSON y texto legible

- **Backend Flask Robusto**:
  - API REST simple y eficiente
  - Procesamiento de imágenes con PIL
  - Orquestación de agentes con LangGraph
  - Limpieza automática de archivos temporales

## 🚀 Instalación

### Requisitos

- Python 3.10+
- OpenAI API Key con acceso a GPT-4 Vision

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

El servidor estará disponible en: `http://localhost:5000`

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

- ✅ API Key nunca en código fuente
- ✅ Videos temporales auto-eliminados después de 1 hora
- ✅ Sin logs de frames para evitar leak de datos
- ✅ Validación de tipos y tamaños de archivo
- ✅ CORS configurado apropiadamente

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

**Powered by**: LangGraph + GPT-4 Vision + Flask + Vanilla JavaScript

