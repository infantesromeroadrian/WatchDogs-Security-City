# 🌍 Geolocation Agent - Documentación Completa

**Versión:** 1.0  
**Fecha:** 2026-01-03  
**Agente #4** del sistema WatchDogs Security City

---

## 📋 **Resumen**

El **Geolocation Agent** es un agente especializado en **identificar la ubicación geográfica** a partir de pistas visuales en imágenes. Utiliza GPT-5.1 Vision para analizar elementos arquitectónicos, señalización, vegetación y otros indicadores de ubicación.

---

## 🎯 **Capacidades**

### **1. Identificación Multi-Nivel**
- 🌐 **País**: Identificación del país basándose en arquitectura, señalización, idioma
- 🏙️ **Ciudad**: Detección de ciudad por monumentos, características únicas
- 🏘️ **Distrito/Barrio**: Identificación de zona específica
- 🛣️ **Calle/Plaza**: Lectura de nombres en placas y señales
- 📍 **Coordenadas**: Estimación de latitud/longitud

### **2. Análisis de Pistas Visuales**

| Categoría | Elementos Analizados |
|-----------|---------------------|
| **Arquitectura** | Estilo de edificios, materiales, altura, densidad |
| **Señalización** | Formato de placas, diseño de señales de tráfico |
| **Mobiliario Urbano** | Farolas, semáforos, papeleras, bancos |
| **Vegetación** | Flora regional, tipo de árboles |
| **Infraestructura** | Cables eléctricos, alcantarillas, pavimento |
| **Matrículas** | Formato de placas vehiculares |
| **Cultura** | Idioma en carteles, símbolos locales |

### **3. Enriquecimiento Automático**
- 🗺️ **Generación de mapas** con Folium (HTML interactivo)
- 🔄 **Geocoding**: Convierte direcciones en coordenadas
- 🔄 **Reverse Geocoding**: Convierte coordenadas en direcciones
- 📌 **Marcadores** en mapa con información contextual

---

## 🧠 **Comportamiento del LLM**

### **Configuración**
```python
model = "gpt-5.1"  # Vision multimodal
temperature = 0.2   # MUY BAJA para precisión en ubicaciones
max_tokens = 3000
```

### **Prompt Especializado**

El agente recibe este prompt estructurado:

```
Eres un experto en GEOLOCALIZACIÓN y análisis OSINT de imágenes.

Tu tarea es IDENTIFICAR LA UBICACIÓN geográfica basándote en pistas visuales.

Analiza TODOS los elementos que pueden revelar ubicación:

1. IDENTIFICADORES DIRECTOS:
   - Nombres de calles, plazas, edificios
   - Señales de tráfico con nombres
   - Carteles con direcciones
   - Matrículas (formato indica país/región)

2. CARACTERÍSTICAS ARQUITECTÓNICAS:
   - Estilo de edificios (colonial, moderno, mediterráneo)
   - Materiales de construcción típicos
   - Altura y densidad

3. SEÑALIZACIÓN Y MOBILIARIO URBANO:
   - Estilo de señales de tráfico
   - Diseño de semáforos, farolas
   - Tipo de pavimento

4. VEGETACIÓN Y CLIMA:
   - Flora regional
   - Condiciones climáticas
   - Altitud (montaña, llanura, costa)

5. INFRAESTRUCTURA:
   - Red eléctrica (aérea/subterránea)
   - Alcantarillas, drenajes

6. ELEMENTOS CULTURALES:
   - Idioma en carteles
   - Símbolos o banderas
   - Tipo de vehículos comunes

7. CONTEXTO GEOGRÁFICO:
   - Latitud aproximada (sombras, iluminación)
   - Hemisferio norte/sur

FORMATO DE RESPUESTA:
- País: [nombre]
- Ciudad: [nombre]
- Distrito: [si identificable]
- Calle: [nombre específico]
- Coordenadas: [lat, lon]
- Nivel de Confianza: Alto/Medio/Bajo
- Pistas Clave: [lista]
- Razonamiento: [explicación]

IMPORTANTE:
- Si NO puedes determinar, indica "No determinado"
- Sé HONESTO sobre el nivel de confianza
- NO inventes ubicaciones sin evidencia
- Prioriza PRECISIÓN sobre especulación
```

---

## 📊 **Estructura de Resultado**

### **JSON de Salida**
```json
{
  "agent": "geolocation",
  "status": "success",
  "confidence": "alto",
  "location": {
    "country": "España",
    "city": "Madrid",
    "district": "Salamanca",
    "street": "Calle de Serrano"
  },
  "coordinates": {
    "lat": 40.4168,
    "lon": -3.7038
  },
  "key_clues": [
    "Señal de tráfico estilo español",
    "Matrícula formato español visible",
    "Arquitectura típica de Madrid centro",
    "Cartel con texto en español",
    "Nombre de calle visible: 'Calle Serrano'"
  ],
  "analysis": "...texto completo del análisis...",
  "map_path": "data/maps/map_40.4168_-3.7038.html",
  "map_url": "/maps/map_40.4168_-3.7038.html",
  "geocoded_address": "Calle de Serrano, 28, Madrid, España"
}
```

---

## 🗺️ **Integración con Mapas**

### **Generación Automática de Mapas**

Cuando el agente identifica coordenadas, el sistema **automáticamente**:

1. ✅ Genera mapa HTML interactivo con **Folium**
2. ✅ Añade **marcador rojo** en ubicación
3. ✅ Añade **círculo azul** (~100m radio) mostrando área aproximada
4. ✅ Guarda en `data/maps/map_{lat}_{lon}.html`
5. ✅ Retorna URL para acceso: `/maps/map_{lat}_{lon}.html`

### **Ejemplo de Mapa Generado**
```python
import folium

m = folium.Map(
    location=[40.4168, -3.7038],
    zoom_start=15,
    tiles='OpenStreetMap'
)

folium.Marker(
    location=[40.4168, -3.7038],
    popup="Madrid, España",
    icon=folium.Icon(color='red', icon='info-sign')
).add_to(m)

folium.Circle(
    location=[40.4168, -3.7038],
    radius=100,  # metros
    color='blue',
    fillOpacity=0.2
).add_to(m)

m.save("mapa.html")
```

---

## 🔄 **Geocoding y Reverse Geocoding**

### **Forward Geocoding** (Dirección → Coordenadas)
```python
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="watchdogs-osint-v1.0")
location = geolocator.geocode("Madrid, Spain")

print(f"Lat: {location.latitude}, Lon: {location.longitude}")
# Output: Lat: 40.4167754, Lon: -3.7037902
```

### **Reverse Geocoding** (Coordenadas → Dirección)
```python
location = geolocator.reverse((40.4168, -3.7038), language='es')

print(location.address)
# Output: "Plaza de España, Moncloa-Aravaca, Madrid, ..."
```

---

## 🚀 **Uso en el Sistema**

### **Ejecución Automática**

El agente se ejecuta **automáticamente** en paralelo con los otros 3 agentes:

```
Usuario → Captura Frame → Coordinator
                              │
      ┌───────────────────────┼───────────────────────┬───────────────────┐
      │                       │                       │                   │
    Vision                   OCR                  Detection          Geolocation
   (contexto)              (texto)               (objetos)          (ubicación)
      │                       │                       │                   │
      └───────────────────────┼───────────────────────┴───────────────────┘
                              │
                          Combinar
                              │
                    Reporte Unificado + Mapa
```

### **API Endpoint**

El endpoint `/api/analyze-frame` ahora incluye geolocalización:

```javascript
POST /api/analyze-frame
{
  "frame": "data:image/png;base64,...",
  "roi": { "x": 0, "y": 0, "width": 800, "height": 600 },
  "context": ""
}

// Response incluye:
{
  "success": true,
  "results": {
    "json": {
      "agents": {
        "vision": {...},
        "ocr": {...},
        "detection": {...},
        "geolocation": {
          "location": {
            "country": "España",
            "city": "Madrid"
          },
          "coordinates": { "lat": 40.4168, "lon": -3.7038 },
          "map_url": "/maps/map_40.4168_-3.7038.html"
        }
      }
    },
    "text": "...reporte con sección de geolocalización..."
  }
}
```

---

## ⚙️ **Configuración**

### **Variables de Entorno**

Usa las mismas configuraciones que los otros agentes:

```bash
# En .env
AGENT_TIMEOUT_SECONDS=30        # Timeout por agente
AGENT_RETRY_MAX_ATTEMPTS=3      # Reintentos
CACHE_ENABLED=True              # Cachear resultados
CIRCUIT_BREAKER_ENABLED=True    # Protección
```

### **Personalización**

#### **Cambiar Zoom del Mapa**
```python
# En geolocation_service.py, línea 28
zoom_start=15  # Cambiar a 12 (más alejado) o 18 (más cerca)
```

#### **Cambiar Radio del Círculo**
```python
# En geolocation_service.py, línea 48
radius=100  # metros (cambiar según precisión deseada)
```

#### **Cambiar Idioma de Geocoding**
```python
# En geolocation_service.py, línea 138
language='es'  # Cambiar a 'en', 'fr', etc.
```

---

## 📈 **Nivel de Confianza**

El agente reporta nivel de confianza basándose en:

| Nivel | Descripción | Ejemplo |
|-------|-------------|---------|
| **Muy Alto** | Nombre de calle + coordenadas visibles | Placa de calle legible + GPS en pantalla |
| **Alto** | Múltiples pistas directas | Nombre de ciudad + arquitectura característica |
| **Medio** | Pistas indirectas pero claras | Estilo arquitectónico + vegetación regional |
| **Bajo** | Pocas pistas, región amplia | Solo tipo de clima y vegetación genérica |
| **Muy Bajo** | Insuficiente información | Imagen interior sin pistas externas |

---

## 🎯 **Casos de Uso**

### **1. Investigación OSINT**
Identificar ubicación de imagen sin metadata:
- Análisis de fotos de redes sociales
- Verificación de ubicación de videos
- Geolocalización de imágenes satelitales

### **2. Verificación de Ubicación**
Confirmar veracidad de ubicación reportada:
- Comparar ubicación declarada vs real
- Detectar manipulación de contexto

### **3. Análisis Forense**
Determinar lugar de incidente:
- Ubicación de incidentes de seguridad
- Análisis de escenas de crimen

---

## 🔒 **Consideraciones de Privacidad**

⚠️ **IMPORTANTE**:
- El agente **NO accede a metadata** de imágenes (EXIF, GPS)
- Solo analiza **contenido visual**
- Mapas generados **almacenados localmente**
- No se envían ubicaciones a servicios terceros (excepto OpenAI para análisis)

---

## 📝 **Ejemplo Completo**

### **Input**
Imagen de calle con:
- Cartel: "Calle Gran Vía, 28"
- Señal de tráfico española
- Arquitectura de Madrid centro
- Matrícula española visible

### **Output**
```
🌍 ANÁLISIS DE GEOLOCALIZACIÓN

UBICACIÓN IDENTIFICADA:
- País: España
- Región: Comunidad de Madrid
- Ciudad: Madrid
- Distrito: Centro
- Calle: Gran Vía

Coordenadas estimadas: [40.4200, -3.7050]

NIVEL DE CONFIANZA: Muy Alto

PISTAS CLAVE UTILIZADAS:
1. Cartel visible con texto "Calle Gran Vía, 28"
2. Señal de tráfico formato español
3. Arquitectura característica de Madrid centro (edificios de 6-7 plantas)
4. Matrícula formato español en vehículo (####-XXX)
5. Estilo de farolas típico de Gran Vía

RAZONAMIENTO:
La presencia del cartel con nombre de calle "Gran Vía" 
combinado con el número de edificio (28) permite ubicación 
precisa. La arquitectura modernista y altura de edificios 
confirma la zona centro de Madrid. Las señales de tráfico 
y matrícula confirman España como país.

RECOMENDACIONES PARA VERIFICACIÓN:
- Buscar "Gran Vía 28 Madrid" en Google Maps
- Verificar fachada de edificio con Street View
- Confirmar comercios visibles en la dirección

📍 Coordenadas: 40.42, -3.705
🗺️ Mapa interactivo generado: /maps/map_40.42_-3.705.html
```

---

## 🛠️ **Troubleshooting**

### **Problema: "No se pudo estimar ubicación"**
**Causa**: Imagen sin pistas visuales claras  
**Solución**: Proporcionar contexto adicional o usar región de interés (ROI)

### **Problema: "Geocoding timeout"**
**Causa**: Servicio Nominatim lento o saturado  
**Solución**: Aumentar timeout en `.env` o reintentar más tarde

### **Problema: "Mapa no se genera"**
**Causa**: Coordenadas inválidas o directorio no existe  
**Solución**: Verificar que `data/maps/` existe y coordenadas están en rango válido

---

## 📚 **Referencias**

- **Folium**: https://python-visualization.github.io/folium/
- **GeoPy**: https://geopy.readthedocs.io/
- **Nominatim**: https://nominatim.org/
- **OpenStreetMap**: https://www.openstreetmap.org/

---

**Creado por:** Gentleman-AI  
**Fecha:** 2026-01-03  
**Versión:** 1.0
