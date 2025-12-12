# 🐳 Documentación Docker - WatchDogs Video Analysis

## 📦 Arquitectura Docker

```
┌─────────────────────────────────────────────┐
│  Host Machine                               │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  Docker Container: watchdogs          │ │
│  │                                       │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │  Python 3.11-slim               │ │ │
│  │  │  - Flask Server (port 5000)     │ │ │
│  │  │  - LangGraph Agents             │ │ │
│  │  │  - OpenAI API Client            │ │ │
│  │  └─────────────────────────────────┘ │ │
│  │                                       │ │
│  │  Volume: ./data/temp ──> /app/data   │ │
│  │  Network: watchdogs-network          │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  Port: 5000:5000 (host:container)          │
└─────────────────────────────────────────────┘
```

## 🚀 Comandos Esenciales

### Iniciar el Sistema

```bash
# Primera vez (construir imagen)
docker compose up --build

# Inicios posteriores
docker compose up

# Modo background (detached)
docker compose up -d
```

### Detener el Sistema

```bash
# Detener contenedores (mantiene volúmenes)
docker compose down

# Detener y eliminar volúmenes
docker compose down -v

# Detener sin eliminar red
docker compose stop
```

### Ver Estado y Logs

```bash
# Estado de servicios
docker compose ps

# Ver logs en tiempo real
docker compose logs -f

# Logs solo del servicio watchdogs
docker compose logs -f watchdogs

# Últimas 100 líneas
docker compose logs --tail=100
```

### Gestión de Contenedores

```bash
# Reiniciar servicio
docker compose restart

# Reiniciar sin downtime (si tienes múltiples instancias)
docker compose up -d --no-deps --build watchdogs

# Ejecutar comando dentro del contenedor
docker compose exec watchdogs bash

# Ver procesos dentro del contenedor
docker compose exec watchdogs ps aux
```

## 🔧 Desarrollo con Docker

### Modo Desarrollo (Hot Reload)

Crear `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  watchdogs:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./src:/app/src:ro  # Mount code for live editing
    environment:
      - FLASK_DEBUG=True
      - FLASK_ENV=development
```

Usar:
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Ejecutar Tests

```bash
# Ejecutar tests dentro del contenedor
docker compose exec watchdogs pytest tests/ -v

# Con coverage
docker compose exec watchdogs pytest tests/ --cov=src --cov-report=html
```

### Acceder al Contenedor

```bash
# Bash interactivo
docker compose exec watchdogs bash

# Ejecutar Python interactivo
docker compose exec watchdogs python

# Ver variables de entorno
docker compose exec watchdogs env
```

## 📊 Monitoreo y Debugging

### Ver Recursos

```bash
# Estadísticas en tiempo real
docker stats watchdogs-video-analysis

# Uso de disco
docker system df

# Inspeccionar contenedor
docker inspect watchdogs-video-analysis
```

### Health Check

```bash
# Verificar salud del contenedor
docker compose ps

# Verificar endpoint manualmente
curl http://localhost:5000/api/health
```

### Logs de Errores

```bash
# Ver solo errores
docker compose logs watchdogs | grep -i error

# Logs con timestamp
docker compose logs -t watchdogs

# Seguir logs de un archivo específico
docker compose exec watchdogs tail -f /app/logs/app.log
```

## 🔒 Seguridad

### Usuario No-Root

El contenedor ejecuta con usuario `watchdogs` (UID 1000):

```dockerfile
USER watchdogs
```

### Secrets Management

**✅ Correcto**: Variables de entorno desde `.env`
```yaml
env_file:
  - .env
```

**❌ Incorrecto**: Secrets en docker-compose.yml
```yaml
environment:
  - OPENAI_API_KEY=sk-1234...  # NUNCA HACER ESTO
```

### Límites de Recursos

Configurados en `docker-compose.yml`:
- CPU: 2 cores máximo
- RAM: 2GB máximo
- Reserva: 0.5 CPU / 512MB RAM

## 🧹 Limpieza y Mantenimiento

### Limpiar Volúmenes

```bash
# Ver volúmenes
docker volume ls

# Eliminar volumen específico
docker volume rm watchdogs-osint-system_video_storage

# Limpiar volúmenes huérfanos
docker volume prune
```

### Limpiar Imágenes

```bash
# Ver imágenes
docker images

# Eliminar imagen específica
docker rmi watchdogs-osint-system-watchdogs

# Limpiar imágenes sin usar
docker image prune -a
```

### Limpieza Completa

```bash
# CUIDADO: Elimina TODO lo que no esté en uso
docker system prune -a --volumes

# Ver espacio que se liberaría
docker system df
```

## 🔄 Actualización y Rebuild

### Actualizar Dependencias

```bash
# Modificar requirements.txt
# Luego reconstruir sin cache
docker compose build --no-cache

# Reiniciar con nueva imagen
docker compose up -d
```

### Cambios en Código

```bash
# Código fuente cambió, reconstruir
docker compose build

# Reiniciar con nueva imagen
docker compose up -d
```

## 🐛 Troubleshooting

### "Puerto ya en uso"

```bash
# Ver qué usa el puerto 5000
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows

# Cambiar puerto en docker-compose.yml
ports:
  - "8000:5000"
```

### "Contenedor se detiene inmediatamente"

```bash
# Ver logs de salida
docker compose logs watchdogs

# Verificar que .env existe
ls -la .env

# Verificar OPENAI_API_KEY
docker compose exec watchdogs printenv | grep OPENAI
```

### "Error de permisos en volúmenes"

```bash
# Verificar permisos del directorio
ls -la data/temp/

# Arreglar permisos
chmod 755 data/temp
chown -R 1000:1000 data/temp
```

### "Imagen muy grande"

```bash
# Ver tamaño de imagen
docker images watchdogs-osint-system-watchdogs

# Analizar capas
docker history watchdogs-osint-system-watchdogs

# Optimizar con multi-stage build (ya implementado)
```

## 📈 Métricas y Performance

### Ver Uso de Recursos

```bash
# Stats en tiempo real
docker stats --no-stream watchdogs-video-analysis

# Inspeccionar red
docker network inspect watchdogs-osint-system_watchdogs-network
```

### Benchmark

```bash
# Tiempo de startup
time docker compose up -d

# Tiempo de request
time curl http://localhost:5000/api/health
```

## 🌐 Producción

### Variables de Entorno de Producción

```env
# .env.production
OPENAI_API_KEY=sk-prod-key
FLASK_ENV=production
FLASK_DEBUG=False
MAX_VIDEO_SIZE_MB=200
VIDEO_RETENTION_HOURS=2
```

### Usar en Producción

```bash
# Usar archivo de entorno específico
docker compose --env-file .env.production up -d

# Con límites de recursos estrictos
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Logs en Producción

Configurado para rotar automáticamente:
- Tamaño máximo por archivo: 10MB
- Número de archivos: 3
- Total: ~30MB de logs

---

**Versión Docker**: 24.0+  
**Versión Docker Compose**: 2.20+  
**Imagen Base**: python:3.11-slim

