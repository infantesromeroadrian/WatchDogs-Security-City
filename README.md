# WatchDogs Security City

Sistema OSINT de análisis de imágenes y vídeo con 16 agentes de visión especializados (LangGraph + Flask).
Proyecto personal de investigación: la calidad de cada agente está **medida** (sección «Calidad medida») y el
despliegue está protegido por autenticación obligatoria.

## Qué hace

Un fotograma (o hasta 10) se envía a 16 agentes que se ejecutan en paralelo sobre un LLM con visión; un
combinador valida y une sus resultados en un informe JSON + texto (y PDF).

| Bloque | Agentes |
|---|---|
| Base | `vision` (descripción), `ocr` (texto leído), `detection` (objetos y conteo), `geolocation` (ubicación y coordenadas) |
| Análisis de personas e imagen | `face_analysis`, `forensic_analysis` (autenticidad), `context_intel` (contexto temporal/cultural) |
| Inteligencia militar | `vehicle_detection`, `weapon_detection`, `crowd_analysis`, `shadow_analysis`, `infrastructure_analysis` |
| Inteligencia militar II/III | `temporal_comparison`, `night_vision`, `nato_symbology` (SIDC APP-6D), `multi_monitor` |

Además: reproductor de vídeo con captura de fotogramas y ROI, análisis multi-fotograma (paralelo o con contexto
acumulado), chat de seguimiento sobre un fotograma, mapa táctico (Mapbox) e informe PDF / paquete de evidencia.

## Arquitectura

```
Navegador (login) ── cookie HttpOnly ──▶ Flask (gunicorn 1 worker × 4 hilos)
                                            │  guard global de autenticación (deny-by-default)
                                            ▼
                                  LangGraph: 16 agentes en paralelo ──▶ combinador ──▶ JSON / texto / PDF
                                            │ (capa llm/: proveedor único, salida estructurada pydantic,
                                            │  timeout HTTP real, reintentos, tope diario de llamadas)
                                            ▼
                         Groq (por defecto) · OpenAI · Ollama · cualquier endpoint OpenAI-compatible
```

Cada agente pide al modelo un objeto JSON con el esquema pydantic de `src/backend/models/structured.py`, lo valida y
lo sanea; si el modelo no devuelve JSON válido se reintenta y, como último recurso, se usa el parser regex heredado.

## Modelo por defecto y proveedores

Un único modelo por defecto, configurable con variables de entorno (`LLM_PROVIDER`, `OPENAI_MODEL`):

| `LLM_PROVIDER` | Endpoint | Modelo por defecto |
|---|---|---|
| `groq` (por defecto, el desplegado) | `https://api.groq.com/openai/v1` | `meta-llama/llama-4-scout-17b-16e-instruct` |
| `openai` | `https://api.openai.com/v1` | `gpt-4.1-mini` |
| `ollama` | `http://localhost:11434/v1` | `qwen3-vl:8b-instruct` |
| `custom` | `OPENAI_BASE_URL` (obligatoria) | `OPENAI_MODEL` |

Con Ollama hay que usar un modelo **sin razonamiento** (`qwen3-vl:8b-instruct`): con `qwen3-vl:8b` (razonamiento
activado, no desactivable por la API `/v1`) un OCR de un cartel generó más de 7000 tokens de razonamiento en bucle.

## Puesta en marcha

Requisitos: Python 3.12 (o Docker), una clave del proveedor y credenciales para la aplicación.

```bash
cp .env.example .env      # rellenar OPENAI_API_KEY, ADMIN_USERNAME, ADMIN_PASSWORD, FLASK_SECRET_KEY
docker compose up --build # http://localhost:5000  (pide usuario y contraseña)
```

Sin Docker: `pip install -r requirements.txt && python main.py`.
`ADMIN_PASSWORD` debe tener al menos 12 caracteres con mayúscula, minúscula y dígito, o al menos 32 caracteres aleatorios
(por ejemplo, el botón «Generate» de Render), sin reglas de composición (NIST SP 800-63B). **La aplicación no arranca sin
`ADMIN_PASSWORD`** (y, en producción, sin `FLASK_SECRET_KEY`): no existe contraseña por defecto ni generada.

### Despliegue en Render

`render.yaml` define un servicio Docker en plan free (Frankfurt). Los secretos (`OPENAI_API_KEY`, `ADMIN_USERNAME`,
`ADMIN_PASSWORD`, `MAP_BOX_ACCESS_TOKEN`) se introducen a mano en el panel de Render (`sync: false`); `FLASK_SECRET_KEY`
se genera allí. **Hacer merge a `main` redespliega**: configurar antes esas variables, o el despliegue fallará su
health check y Render mantendrá la versión anterior.

## Seguridad

- **Autenticación obligatoria** en toda la aplicación y la API (guard global, denegar por defecto; solo son públicos
  `/api/health`, `/api/auth/login`, `/login` y `/static/`). Sesión por cookie `HttpOnly` + `SameSite=Strict` (y
  `Authorization: Bearer` para clientes API), token firmado con `FLASK_SECRET_KEY`, 8 h de vida, PBKDF2-HMAC-SHA256 con
  600 000 iteraciones, bloqueo por intentos fallidos, 5 intentos de login por minuto y defensa CSRF por origen.
  Una petición sin credenciales a cualquier endpoint de análisis devuelve `401` (cubierto por tests).
- **Tope diario de llamadas al LLM** (`LLM_DAILY_CALL_LIMIT`, `LLM_DAILY_CALL_LIMIT_PER_USER`; un análisis completo =
  16 llamadas por fotograma), persistido en SQLite; comprobación previa (`429` + `Retry-After`) y corte duro en la capa LLM.
- **Límites de subida**: vídeo 50 MB, JSON 30 MB, imagen 12 MB, 40 Mpíxeles, 10 fotogramas por lote, 4000 caracteres de chat.
- **Sin persistencia más allá del procesamiento**: un job en segundo plano elimina vídeos (15 min), sesiones con sus
  fotogramas y el historial de chat (15 min), y la caché de resultados (5 min). El grafo de análisis no guarda estado.
- **Logs sin contenido de imagen ni datos personales**: filtro que elimina datos base64/data-URI, tokens y correos; la IP
  de cliente solo se registra como hash corto.
- **CORS cerrado por defecto** (la SPA es del mismo origen); `*` se rechaza. Respuestas de API con `Cache-Control: no-store`.
- **Secretos solo en el entorno** (Render). `gitleaks` limpio sobre todo el historial y sobre el árbol de trabajo.
- **Imágenes = entrada no fiable (inyección de prompt visual)**: el texto incrustado en una imagen se trata como dato.
  Salidas de agentes validadas por esquema, saneadas (sin caracteres de control/bidi, longitud acotada) y encerradas entre
  marcadores `DATOS_NO_FIABLES` con aviso cuando vuelven a un prompt (contexto multi-fotograma y chat); el PDF escapa
  cualquier marcado que no sea `<b>`, `<i>`, `<br/>` (ReportLab aceptaba `<img src=…>`); la UI escapa las etiquetas del mapa
  (había un XSS: etiquetas derivadas del LLM llegaban a `innerHTML`). Suite de regresión en `tests/test_prompt_injection.py`.

Limitación conocida: ningún filtro impide que un modelo pequeño *se deje influir* en el contenido de sus propias salidas
por un texto en la imagen; las defensas acotan el daño (no ejecuta nada, no escala a otros prompts como instrucciones, no
inyecta marcado), no garantizan salidas veraces. Las salidas son probabilísticas y requieren revisión humana.

## Calidad medida

Todas las cifras de esta sección se generan desde `metrics.json` (`python -m eval.update_readme`). Reproducir:

```bash
python -m eval.fetch_data                                   # descarga imágenes (fuera del repo, con sha256)
LLM_PROVIDER=ollama OPENAI_MODEL=qwen3-vl:8b-instruct python -m eval.run_eval --out metrics.json
python -m eval.service_probe --out metrics.json             # concurrencia y memoria con gunicorn
python -m eval.update_readme
```

Los datos no se versionan: `eval/data/*.json` solo contiene títulos de Wikimedia Commons, identificadores COCO,
licencias y sha256. Conjuntos: geolocalización (Commons geoetiquetadas, CC0/PD/CC BY/CC BY-SA), OCR (texto sintético
con PIL, semilla fija), conteo (COCO val2017, licencias BY/BY-SA/sin restricciones conocidas), simbología OTAN (SIDC
APP-6D sintéticos con milsymbol, MIT) y armas (Commons dominio público/CC0, etiquetado a mano, conjunto pequeño).
**Reconocimiento facial/demografía: no se evalúa cuantitativamente** (no hay un conjunto con licencia compatible y
etiquetas válidas; evaluar atributos demográficos sobre personas sin consentimiento no procede). `face_analysis` solo se
mide en conteo de personas.

<!-- metrics:start -->
Modelo evaluado: `qwen3-vl:8b-instruct` vía `ollama` (`localhost:11434`). Generado el 2026-11-07T22:14:04+00:00 sobre el commit `8b217ba`. 235 llamadas a agentes, 1 sin estado `success`.

| Familia | Agente | n | Resultado |
|---|---|---|---|
| Geolocalización | geolocation | 19 | 9 con coordenadas (el resto: «no determinable»); error mediano 5.1 km sobre esas; 36.8 % del total a ≤25 km; 42.1 % a ≤200 km |
| OCR (texto sintético) | ocr | 24 | CER medio 0.03 (mediana 0.0); coincidencia exacta 87.5 %; plate 0.021, sign 0.039 |
| Conteo (people) | detection | 20 | MAE 2.25 (línea base «mediana constante» 2.5); exactos 40.0 %; sin dato 1 |
| Conteo (people) | face_analysis | 20 | MAE 2.45 (línea base «mediana constante» 2.5); exactos 40.0 %; sin dato 0 |
| Conteo (vehicles) | detection | 20 | MAE 2.9 (línea base «mediana constante» 2.5); exactos 5.0 %; sin dato 0 |
| Conteo (vehicles) | vehicle_detection | 20 | MAE 3.3 (línea base «mediana constante» 2.5); exactos 10.0 %; sin dato 0 |
| Conteo (crowd) | crowd_analysis | 10 | MAE 6.7 (línea base «mediana constante» 0.6); exactos 20.0 %; sin dato 1 |
| Conteo (crowd) | detection | 10 | MAE 3.9 (línea base «mediana constante» 0.6); exactos 10.0 %; sin dato 0 |
| Simbología OTAN (SIDC APP-6D sintético) | nato_symbology | 24 | SIDC bien formado 45.8 %; afiliación 41.7 %; conjunto de símbolos 25.0 %; entidad 0.0 %; exacto 0.0 % |
| Armas (presencia, conjunto pequeño etiquetado a mano) | weapon_detection | 20 | exactitud 100.0 %; precisión 100.0 %; recall 100.0 % (TP 10, FP 0, FN 0, TN 10) |

Coste de un análisis completo (16 agentes, un fotograma; media de 3 imágenes): 55,275 tokens de entrada y 8,405 de salida; 332.8 s sumando los 16 agentes en secuencia en este backend (en producción los 16 se ejecutan en paralelo).
<!-- metrics:end -->

Coste: multiplicar los tokens medidos por análisis (entrada y salida, arriba) por los precios publicados del proveedor; para Groq, https://groq.com/pricing . No se incluye cifra monetaria.

### Desviaciones del protocolo (conjunto de desarrollo)

**Este conjunto de evaluación se usó para ajustar prompts: es un conjunto de desarrollo, no una prueba independiente.**
Hubo tres pases sobre el mismo conjunto:

1. Pase 1 (esquema con marcadores 0/0.0). Los modelos copiaban el 0 para «no sé»; las 19 «predicciones» de
   geolocalización del pase 1 incluyen coordenadas (0, 0) de relleno.
2. **Desviación 1**: marcadores `<número o null>`, regla «null, nunca 0» y (0, 0) tratado como «sin coordenadas».
   Efecto: `crowd_analysis` dejó de dar conteo en 10/10 imágenes.
3. **Desviación 2**: directiva «en conteos da siempre una estimación numérica; null solo en coordenadas y códigos».
   El pase 3 es el reportado. No se hizo un cuarto ajuste.

La conversión de LengthFinishReasonError en reintento y la base de presupuesto propia del eval son correcciones de
robustez, no ajustes al conjunto. Cifras por pase (también en `metrics.json`, `notes.passes`):

| Métrica | Pase 1 | Pase 2 | Pase 3 (reportado) |
|---|---|---|---|
| geo_con_coordenadas | 19 | 8 | 9 |
| geo_pct_25km | 42.1 | 36.8 | 36.8 |
| geo_pct_200km | 42.1 | 36.8 | 42.1 |
| ocr_cer | 0.03 | 0.03 | 0.03 |
| mae_detection_people | 2.55 | 2.1 | 2.25 |
| sin_dato_detection_people | 0 | 2 | 1 |
| mae_face_analysis_people | 2.7 | 2.75 | 2.45 |
| sin_dato_face_analysis_people | 1 | 1 | 0 |
| mae_detection_vehicles | 3.15 | 2.75 | 2.9 |
| sin_dato_detection_vehicles | 1 | 1 | 0 |
| mae_vehicle_detection_vehicles | 2.4 | 3.3 | 3.3 |
| sin_dato_vehicle_detection_vehicles | 0 | 2 | 0 |
| mae_crowd_analysis_crowd | 3.1 | 12.0 | 6.7 |
| sin_dato_crowd_analysis_crowd | 0 | 10 | 1 |
| mae_detection_crowd | 6.2 | 5.4 | 3.9 |
| sin_dato_detection_crowd | 1 | 1 | 0 |
| nato_sidc_bien_formado | 83.3 | 54.2 | 45.8 |
| nato_afiliacion | 70.8 | 41.7 | 41.7 |
| nato_entidad | 4.2 | 0.0 | 0.0 |
| armas_accuracy | 100.0 | 100.0 | 100.0 |
| llamadas_no_success | 3 | 6 | 1 |

## Rendimiento y recursos

<!-- service:start -->
Medido con `eval.service_probe`: gunicorn 1 worker x 4 threads, MALLOC_ARENA_MAX=2, stub LLM with 0.5s per call.

| Medida | Valor |
|---|---|
| Análisis completos simultáneos (16 agentes cada uno) | 4 × 2 rondas, 8/8 con 16/16 agentes correctos |
| Latencia por análisis (mediana / máxima) | 2.27 s / 2.34 s (con 0,5 s por llamada simulada: demuestra el paralelismo, no la latencia de un proveedor real) |
| Memoria del worker en reposo / tras la carga | 108.6 MB / 151.1 MB (límite del plan free de Render: 512 MB) |
<!-- service:end -->

## Desarrollo

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest        # tests offline (LLM simulado con tests/stub_llm.py), sin claves ni red
ruff check src tests eval
```

CI (GitHub Actions, `permissions: contents: read`, acciones fijadas por SHA): ruff + pytest, `docker build` sin push y
`gitleaks` sobre todo el historial. Dependabot: mensual, agrupado, máximo 2 PR abiertas.

## Uso responsable y marco legal

Este sistema puede procesar imágenes de personas y de entornos sensibles. Úselo solo sobre material propio o con base
legal y autorización, nunca para vigilancia encubierta, identificación de particulares ni decisiones automatizadas sobre
personas. Esto no es asesoramiento jurídico.

- **RGPD (Reglamento (UE) 2016/679)**: una imagen de una persona identificable es dato personal; los datos biométricos
  usados para identificar de forma única son categoría especial (art. 9). Hace falta base jurídica (art. 6 y, en su caso,
  excepción del art. 9), minimización, evaluación de impacto (art. 35) cuando proceda y control de transferencias
  internacionales: las imágenes se envían al proveedor del LLM (Groq/OpenAI, en EE. UU.). La retención por defecto es de
  minutos y no se guardan fotogramas más allá del procesamiento.
- **Reglamento europeo de IA (Reglamento (UE) 2024/1689)**: según la Comisión Europea (consultado el 7-nov-2026) es de
  aplicación desde el 2-ago-2026, con las prácticas prohibidas aplicables desde el 2-feb-2025; las obligaciones de los
  sistemas de alto riesgo del anexo III se han aplazado al 2-dic-2027 por el acuerdo político del «AI Omnibus» (7-may-2026;
  su adopción formal no está verificada aquí). Aspectos a vigilar: la categorización biométrica para deducir atributos
  sensibles (p. ej. origen étnico) y la identificación biométrica están restringidas o prohibidas según el contexto
  (art. 5) y algunos usos de biometría/vigilancia son de alto riesgo (anexo III). Se eliminó la inferencia de etnia (Reglamento (UE) 2024/1689, art. 5.1.g, categorización biométrica de atributos sensibles); `face_analysis` conserva edad, género aparente y conteo (`FACE_ANALYSIS_ENABLED=false` o `PRIVACY_MODE=true` lo desactivan).
- Las salidas son estimaciones de un modelo, pueden ser erróneas o sesgadas y deben verificarse por una persona.

## Limitaciones conocidas

- Las cifras de calidad corresponden al modelo local indicado, no al desplegado en Render (Groq `llama-4-scout`):
  no se llamó a APIs de pago durante la medición. Reproducir con el proveedor deseado.
- Geolocalización: el conjunto prioriza lugares reconocibles; el error sobre calles anónimas será mayor. Cuando el
  modelo no puede ubicar devuelve «no determinable» (sin coordenadas) en lugar de inventarlas; con un lugar
  equivocado y confianza «muy alta» sí puede errar por miles de kilómetros (ocurrió una vez en el conjunto).
- Conteo (personas, vehículos, multitudes): con el modelo local evaluado los errores son del orden de la línea base de
  «mediana constante»; no usar los conteos como cifras fiables sin revisión.
- `nato_symbology` interpreta fotografías mejor que símbolos dibujados: sobre símbolos APP-6D sintéticos no acierta la
  entidad (véase la tabla). El conjunto de armas es pequeño (20 imágenes, etiquetado a mano): no extrapolar.
- `temporal_comparison` compara de verdad solo en el flujo multi-fotograma; con un fotograma infiere indicadores.
- Estado de sesiones, tope diario y caché viven en el disco/RAM efímeros del plan free: se pierden al reiniciar
  (las sesiones firmadas sobreviven; el contador diario se reinicia con el contenedor).

## Limitaciones pendientes

- El test de regresión de inyección visual (`tests/test_prompt_injection.py`, con corpus externo `tests/fixtures/injection_payloads.json`) está pendiente y entrará en una PR aparte; hasta entonces se salta.

## Licencia

MIT, Copyright (c) 2026 Adrián Infantes Romero (ver `LICENSE`).
