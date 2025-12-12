# Project Requirements Document
**Project Name:** WatchDogs OSINT - Video Analysis System  
**Date:** 2025-01-08  
**Version:** 1.0  
**Status:** Draft - Pending Approval

---

## 1. BUSINESS CONTEXT

### 1.1 Problem to Solve
**Problema actual:**
- Análisis manual de videos e imágenes para investigación OSINT es lento y propenso a errores
- Investigadores deben revisar frame por frame manualmente
- Extracción de información (texto, objetos, personas) requiere múltiples herramientas separadas
- No hay un sistema unificado que combine análisis visual, OCR y detección de objetos

**Proceso manual actual:**
- Cargar video en reproductor
- Pausar manualmente en frames relevantes
- Usar herramientas separadas para OCR, detección, análisis
- Combinar resultados manualmente
- Tiempo estimado: 15-30 minutos por video corto

### 1.2 Measurable Objective
**Objetivos SMART:**
- **Reducir tiempo de análisis:** De 15-30 min a < 2 minutos por video (reducción 85-90%)
- **Aumentar precisión:** Extracción automática de texto con >95% accuracy
- **Automatizar proceso:** 100% automatización del análisis multi-agente
- **Mejorar cobertura:** Análisis simultáneo de 3 dimensiones (visual, OCR, detección)

**KPIs:**
- Tiempo promedio de análisis por frame: < 30 segundos
- Tasa de éxito de análisis: > 95%
- Precisión OCR: > 95% para texto claro
- Disponibilidad del sistema: > 99% (uptime)

### 1.3 End Users
**Perfil de usuarios:**
- **Investigadores OSINT** (principal)
  - Nivel técnico: Medio-Alto
  - Conocimiento AI/ML: Básico
  - Necesitan: Interfaz simple, resultados claros, exportación de datos
  
- **Analistas de seguridad**
  - Nivel técnico: Alto
  - Conocimiento AI/ML: Medio
  - Necesitan: API programática, integración con otras herramientas

- **Operadores de campo**
  - Nivel técnico: Bajo-Medio
  - Conocimiento AI/ML: Mínimo
  - Necesitan: Interfaz muy simple, guías claras

### 1.4 Budget & Timeline
**Presupuesto:**
- Infraestructura: Docker local (sin costos cloud iniciales)
- APIs: OpenAI GPT-5.1 Vision (~$0.01-0.03 por imagen analizada)
- Estimado: $50-200/mes para uso moderado (1000-5000 análisis/mes)

**Timeline:**
- **MVP:** Completado (versión actual)
- **Fase de mejoras:** 2-4 semanas
- **Producción:** Después de completar Phase 1 y Phase 2 del workflow

**Tipo de solución:**
- **Actual:** MVP funcional
- **Objetivo:** Sistema de producción para investigación OSINT

---

## 2. DATA

### 2.1 Data Types
**Tipos de datos:**
- **Videos:** MP4, AVI, MOV, MKV, WEBM
- **Imágenes:** Frames extraídos de videos (PNG, JPEG)
- **Texto:** Resultados de OCR, análisis estructurados (JSON)
- **Metadata:** Timestamps, coordenadas ROI, resultados de agentes

**Volumen:**
- Videos: 10-100 MB por archivo (límite: 100 MB)
- Frames: 1-10 MB por frame (base64)
- Resultados: < 1 MB por análisis (JSON + texto)

### 2.2 Data Quality
**Calidad de datos:**
- **Videos:** Variable (depende de fuente)
  - Pueden tener baja resolución
  - Pueden tener compresión
  - Pueden tener ruido
  
- **Texto en imágenes:**
  - Variable legibilidad
  - Múltiples idiomas posibles
  - Texto parcialmente oculto o borroso

- **Etiquetado:**
  - No hay dataset etiquetado
  - Análisis es no supervisado
  - Validación manual post-análisis

### 2.3 Data Location
**Ubicación actual:**
- **Videos:** Upload temporal en `data/temp/` (local filesystem)
- **Frames:** En memoria durante procesamiento (base64)
- **Resultados:** Retornados al frontend, no persistidos (por ahora)

**Futuro:**
- Considerar almacenamiento persistente de resultados
- Considerar base de datos para historial de análisis

### 2.4 Additional Data Collection
**Recolección adicional:**
- No se requiere recolección externa
- Los usuarios suben sus propios videos
- No hay scraping ni APIs externas (excepto OpenAI)

**Restricciones legales:**
- **GDPR/Privacidad:** 
  - Videos pueden contener PII
  - No se almacenan permanentemente (retention: 1 hora)
  - Usuarios responsables de contenido subido
- **Uso ético:**
  - Sistema para investigación legítima OSINT
  - No para vigilancia no autorizada

### 2.5 Data Dynamics
**Naturaleza de los datos:**
- **Estático por análisis:** Cada frame se analiza de forma independiente
- **Batch processing:** Un frame a la vez (no streaming)
- **No requiere:** Kafka, Kinesis, o pipelines en tiempo real
- **Patrón:** Request-response síncrono

---

## 3. AI/ML SOLUTION

### 3.1 Problem Type
**Tipo de problema:**
- **Computer Vision:** Análisis de imágenes y videos
- **OCR (Optical Character Recognition):** Extracción de texto
- **Object Detection:** Detección de objetos, personas, vehículos
- **Multi-modal AI:** Combinación de visión y lenguaje (GPT-5.1 Vision)

**No es:**
- Clasificación supervisada (no hay dataset etiquetado)
- Entrenamiento de modelos (usa modelos pre-entrenados)
- Reinforcement Learning

### 3.2 Pre-trained Models
**Modelos utilizados:**
- **GPT-5.1 Vision (OpenAI):**
  - Modelo multimodal pre-entrenado
  - Capacidades: Análisis visual, OCR, detección de objetos
  - No requiere fine-tuning
  - Acceso vía API

**No se requiere:**
- Entrenamiento desde cero
- Fine-tuning de modelos
- Modelos locales (por ahora)

### 3.3 Success Metrics
**Métricas de éxito:**

**Precisión OCR:**
- Objetivo: > 95% para texto claro y legible
- Mínimo aceptable: > 85%
- Método: Validación manual de muestras

**Tiempo de respuesta:**
- Objetivo: < 30 segundos por frame (3 agentes en paralelo)
- Mínimo aceptable: < 60 segundos
- Método: Medición de latencia end-to-end

**Tasa de éxito:**
- Objetivo: > 95% de análisis completados sin errores
- Mínimo aceptable: > 90%
- Método: Logs de errores vs requests totales

**Calidad de análisis:**
- Objetivo: Reportes útiles en > 90% de casos
- Método: Feedback de usuarios (subjetivo)

### 3.4 Interpretability Requirements
**Requisitos de interpretabilidad:**
- **Sí, es crítico:**
  - Investigadores necesitan entender qué detectó el sistema
  - Reportes deben ser legibles por humanos
  - Resultados deben ser auditables
  
- **No se requiere:**
  - SHAP/LIME (no hay modelo entrenado localmente)
  - Explicación de pesos del modelo (modelo externo)
  
- **Sí se requiere:**
  - Reportes en texto legible
  - JSON estructurado con confianza
  - Visualización de ROI seleccionado

### 3.5 Model Constraints
**Restricciones:**

**Latencia:**
- Máximo aceptable: 60 segundos por frame
- Objetivo: < 30 segundos
- Real-time no requerido (batch OK)

**Tamaño del modelo:**
- No aplica (modelo en la nube vía API)
- Sin restricciones de tamaño local

**Costos:**
- Presupuesto: $50-200/mes
- Costo por análisis: ~$0.01-0.03
- Límite: ~5000 análisis/mes

**Recursos:**
- CPU: Suficiente para procesamiento de imágenes
- RAM: 2GB mínimo (Docker limit: 2GB)
- GPU: No requerida (API externa)

---

## 4. ARCHITECTURE & TECHNOLOGIES

### 4.1 Preferred Languages
**Lenguajes:**
- **Python 3.11+** (principal)
  - Backend Flask
  - Procesamiento de imágenes (PIL)
  - Integración con LangGraph y OpenAI
  
- **JavaScript (Vanilla)** (frontend)
  - Sin frameworks pesados
  - Interactividad del video player
  - Comunicación con API

### 4.2 ML/AI Frameworks
**Frameworks y librerías:**
- **LangGraph** (>=0.2.50): Orquestación de agentes
- **LangChain** (>=0.3.0): Integración con LLMs
- **LangChain OpenAI** (>=0.2.0): Cliente para GPT-5.1
- **OpenAI** (>=1.58.1): SDK oficial
- **Pillow** (>=11.0.0): Procesamiento de imágenes
- **OpenCV** (headless): Procesamiento de video (futuro)

### 4.3 Deployment Target
**Target de deployment:**
- **Actual:** Docker local (desarrollo)
- **Objetivo:** 
  - Docker Compose (producción local/on-prem)
  - Posible: Cloud (AWS ECS, GCP Cloud Run) en futuro
- **No requerido:** Kubernetes (por ahora)

### 4.4 Data Infrastructure
**Infraestructura de datos:**
- **Almacenamiento temporal:** Filesystem local (`data/temp/`)
- **Base de datos:** No requerida (por ahora)
- **Vector DB:** No requerida (no hay RAG)
- **Cache:** No implementado (futuro: Redis para resultados)

### 4.5 Pipeline Orchestration
**Orquestación:**
- **LangGraph:** Orquestación de agentes (workflow)
- **Flask:** Orquestación de requests HTTP
- **No se requiere:** Airflow, Prefect, Kubeflow (muy simple)

**Experiment tracking:**
- **No implementado:** MLflow, W&B
- **Futuro:** Considerar logging de métricas

### 4.6 Integrations
**Integraciones existentes:**
- **OpenAI API:** GPT-5.1 Vision
- **Flask CORS:** Comunicación frontend-backend

**Integraciones futuras:**
- Posible: Base de datos para historial
- Posible: Sistema de autenticación
- Posible: Exportación a formatos externos

---

## 5. SECURITY & COMPLIANCE

### 5.1 Sensitive Data
**Datos sensibles:**
- **PII potencial:** 
  - Videos pueden contener caras, matrículas, documentos
  - Texto extraído puede contener información personal
- **Credenciales:**
  - OpenAI API Key (en .env, no en código)
- **Datos de investigación:**
  - Contenido de videos puede ser confidencial

### 5.2 Regulations
**Regulaciones aplicables:**
- **GDPR:** Si se procesan datos de UE
  - Retención limitada (1 hora)
  - No almacenamiento permanente
  - Usuarios responsables del contenido
  
- **No aplica directamente:**
  - HIPAA (no es salud)
  - PCI-DSS (no es pagos)
  
- **Consideraciones éticas:**
  - Uso legítimo para investigación OSINT
  - No para vigilancia no autorizada

### 5.3 Encryption
**Encriptación:**
- **En tránsito:** HTTPS/TLS (recomendado para producción)
- **En reposo:** No implementado (videos temporales sin encriptar)
- **API Keys:** En .env (no en código)
- **Modelos:** No aplica (API externa)

### 5.4 Ethical Constraints
**Consideraciones éticas:**
- **Bias:** Modelo GPT-5.1 puede tener sesgos (no controlables localmente)
- **Privacidad:** 
  - No se almacenan videos permanentemente
  - No se logean frames completos
  - Usuarios responsables del contenido
  
- **Abuse prevention:**
  - Rate limiting (a implementar)
  - Validación de tipos de archivo
  - Límites de tamaño

---

## 6. MONITORING & MAINTENANCE

### 6.1 Monitoring
**Monitoreo actual:**
- **Logs:** Python logging básico
- **Health check:** Endpoint `/api/health`
- **Métricas:** No implementadas

**Monitoreo requerido:**
- **Métricas básicas:**
  - Requests por minuto
  - Tiempo de respuesta promedio
  - Tasa de errores
  - Uso de API OpenAI (costos)
  
- **Herramientas:**
  - Logs estructurados (implementar)
  - Posible: Prometheus + Grafana (futuro)

### 6.2 Drift Detection
**Detección de drift:**
- **No aplica directamente:** No hay modelo entrenado localmente
- **Monitoreo de calidad:**
  - Tasa de éxito de análisis
  - Feedback de usuarios sobre calidad
  - Comparación de resultados entre versiones

### 6.3 Retraining Strategy
**Estrategia de retraining:**
- **No aplica:** No hay modelo local para retrenar
- **Actualizaciones:**
  - GPT-5.1 se actualiza por OpenAI
  - Monitorear cambios en calidad de respuestas
  - Ajustar prompts si es necesario

### 6.4 Maintenance & Ownership
**Mantenimiento:**
- **Equipo actual:** Desarrollador único / pequeño equipo
- **Responsabilidades:**
  - Mantenimiento de código
  - Actualización de dependencias
  - Monitoreo de costos API
  - Resolución de bugs
  
- **Documentación requerida:**
  - README (existente)
  - Documentación de API (a crear)
  - Guías de deployment (a crear)

---

## 7. PROPOSED ARCHITECTURE (HIGH LEVEL)

```
┌─────────────────┐
│   Frontend      │
│  (HTML/JS/CSS)  │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│   Flask API     │
│   (app.py)      │
└────────┬────────┘
         │
         ├─→ ImageService (ROI cropping)
         │
         ▼
┌─────────────────┐
│ LangGraph       │
│ Coordinator     │
└────────┬────────┘
         │
         ├─→ Vision Agent (GPT-5.1)
         ├─→ OCR Agent (GPT-5.1)
         └─→ Detection Agent (GPT-5.1)
         │
         ▼
┌─────────────────┐
│ Result Combiner │
│ (JSON + Text)   │
└─────────────────┘
```

**Componentes principales:**
- Frontend: Interfaz web para upload y visualización
- Flask API: Endpoints REST para análisis
- LangGraph: Orquestación de agentes (actualmente secuencial, objetivo: paralelo)
- Agentes: 3 agentes especializados usando GPT-5.1 Vision
- Servicios: Procesamiento de imágenes y videos

**Detalles técnicos:**
- Docker containerizado
- Sin base de datos (por ahora)
- Almacenamiento temporal en filesystem
- Comunicación síncrona request-response

---

## 8. RISKS & MITIGATIONS

### 8.1 Technical Risks

**Riesgo 1: Costos de API OpenAI**
- **Probabilidad:** Media
- **Impacto:** Alto
- **Mitigación:** 
  - Rate limiting
  - Monitoreo de costos
  - Cache de resultados (futuro)
  - Límites de uso por usuario

**Riesgo 2: Latencia alta**
- **Probabilidad:** Media
- **Impacto:** Medio
- **Mitigación:**
  - Ejecución paralela de agentes (a implementar)
  - Timeouts configurables
  - Feedback visual de progreso

**Riesgo 3: Calidad variable de análisis**
- **Probabilidad:** Alta
- **Impacto:** Medio
- **Mitigación:**
  - Prompts mejorados
  - Validación de resultados
  - Feedback loop con usuarios

### 8.2 Security Risks

**Riesgo 4: Exposición de datos sensibles**
- **Probabilidad:** Baja
- **Impacto:** Alto
- **Mitigación:**
  - No almacenamiento permanente
  - No logging de frames completos
  - CORS restringido (a implementar)
  - Rate limiting

**Riesgo 5: Abuso de API**
- **Probabilidad:** Media
- **Impacto:** Medio
- **Mitigación:**
  - Rate limiting (a implementar)
  - Validación de inputs
  - Límites de tamaño de archivo

### 8.3 Operational Risks

**Riesgo 6: Dependencia de OpenAI API**
- **Probabilidad:** Baja
- **Impacto:** Alto
- **Mitigación:**
  - Manejo robusto de errores
  - Retry logic
  - Fallback a modelos alternativos (futuro)

---

## 9. PROJECT PHASES & TIMELINE

### Phase 1: Discovery & Requirements ✅ (En progreso)
- **Duración:** 1 día
- **Estado:** Documento de requisitos creado (pendiente aprobación)
- **Entregables:** Este documento

### Phase 2: Planning & Architecture (Pendiente)
- **Duración:** 1-2 días
- **Tareas:**
  - Crear diagramas de arquitectura
  - Crear sistema de tickets
  - Planificar implementación de mejoras
- **Entregables:**
  - Diagramas en `diagrams/`
  - Tickets en `tickets/`

### Phase 3: Execution & Development (En progreso)
- **Duración:** 2-4 semanas
- **Tareas:**
  - Implementar ejecución paralela en LangGraph
  - Mejorar logging según regla 19
  - Mejorar seguridad (CORS, rate limiting)
  - Mejorar frontend
  - Agregar tests de integración
- **Entregables:**
  - Código mejorado
  - Tests completos
  - Documentación actualizada

---

## 10. ACCEPTANCE CRITERIA

### 10.1 Functional Requirements
- [ ] Sistema puede analizar frames de video con 3 agentes
- [ ] ROI (Region of Interest) funciona correctamente
- [ ] Resultados se muestran en formato JSON y texto
- [ ] Chat conversacional funciona con contexto
- [ ] Videos se limpian automáticamente después de 1 hora

### 10.2 Performance Requirements
- [ ] Análisis completo en < 60 segundos (objetivo: < 30s)
- [ ] Sistema maneja videos hasta 100 MB
- [ ] Interfaz responde en < 2 segundos para operaciones UI

### 10.3 Quality Requirements
- [ ] Precisión OCR > 85% (objetivo: > 95%)
- [ ] Tasa de éxito > 90% (objetivo: > 95%)
- [ ] Código pasa linters (flake8/ruff)
- [ ] Tests unitarios con cobertura > 70%

### 10.4 Security Requirements
- [ ] No secrets en código
- [ ] CORS configurado apropiadamente
- [ ] Rate limiting implementado
- [ ] Validación de inputs robusta

### 10.5 Documentation Requirements
- [ ] README completo y actualizado
- [ ] Documento de requisitos aprobado
- [ ] Diagramas de arquitectura
- [ ] Documentación de API (Swagger/OpenAPI)

---

## 11. ASSUMPTIONS & CONSTRAINTS

### 11.1 Assumptions
- Los usuarios tienen acceso a OpenAI API con créditos suficientes
- Los videos subidos son legítimos para investigación OSINT
- Los usuarios tienen conocimiento básico de cómo usar interfaces web
- El sistema se ejecuta en entorno con Docker disponible

### 11.2 Constraints
- **Técnicos:**
  - Dependencia de API externa (OpenAI)
  - Latencia de red afecta tiempos de respuesta
  - Sin GPU local (procesamiento en la nube)
  
- **Presupuesto:**
  - Costos de API limitan uso intensivo
  - Sin infraestructura cloud inicial
  
- **Tiempo:**
  - MVP ya completado
  - Mejoras incrementales

---

## 12. APPROVAL

**Este documento requiere aprobación explícita antes de continuar a Phase 2 (Planning & Architecture).**

**Revisado por:** _________________  
**Fecha:** _________________  
**Aprobado:** ☐ Sí  ☐ No  
**Comentarios:** _________________

---

**Próximos pasos después de aprobación:**
1. Crear diagramas de arquitectura (`diagrams/`)
2. Crear sistema de tickets (`tickets/`)
3. Iniciar implementación de mejoras según tickets

---

*Documento creado siguiendo `02_requirements_gathering_rule.mdc`*

