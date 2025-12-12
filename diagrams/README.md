# Project Architecture Diagrams

**Project:** WatchDogs OSINT - Video Analysis System  
**Last updated:** 2025-01-08  

---

## Architecture Diagrams

| Name            | File                                  | Purpose                        | Status |
|-----------------|---------------------------------------|--------------------------------|--------|
| System Overview | architecture/01_system_overview.drawio  | High-level system view         | ✅ |
| ML Pipeline     | architecture/02_ml_pipeline.drawio      | ML workflow (agent orchestration) | ✅ |
| Deployment      | architecture/03_deployment.drawio       | Deployment architecture        | ✅ |

---

## Notes

### Architecture Pattern
- **Monolith + Modules:** Flask app con módulos separados (agents, services, utils)
- **Agent Orchestration:** LangGraph para coordinar agentes especializados
- **Request-Response:** Patrón síncrono (no streaming, no async)

### Key Components
- **Frontend:** HTML/JS/CSS estático servido por Flask
- **Backend API:** Flask REST API con rate limiting y CORS restringido
- **Agents:** 3 agentes especializados (Vision, OCR, Detection) ejecutándose en paralelo
- **Services:** Procesamiento de imágenes y gestión de videos
- **Storage:** Filesystem temporal (no base de datos)

### Security Considerations
- CORS restringido a orígenes permitidos
- Rate limiting por IP (30 req/min general, 10 req/min para análisis)
- Validación de inputs (tipo de archivo, tamaño)
- No almacenamiento permanente de videos (retention: 1 hora)

### Performance
- **Ejecución paralela:** 3 agentes ejecutan simultáneamente usando threading
- **Tiempo objetivo:** < 30 segundos por análisis completo
- **Límites:** Videos hasta 100 MB, timeout de 60s en frontend

---

## Links to Related Documents

- Requirements: `docs/requirements.md`
- Tickets: `tickets/README.md`
- History: `historyMD/README.md`
- Review: `docs/PROJECT_REVIEW.md`

---

*Diagramas creados según `04_architecture_diagram_rule.mdc`*

