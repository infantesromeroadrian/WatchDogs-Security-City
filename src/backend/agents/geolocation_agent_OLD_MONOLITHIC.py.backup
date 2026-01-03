"""
Geolocation Agent for identifying location details from images using GPT-5.1.
Specialized in: Country, City, District, Street, Coordinates estimation.
"""

import logging
import re
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_MAX_TOKENS,
    AGENT_TIMEOUT_SECONDS,
    AGENT_RETRY_MAX_ATTEMPTS,
    AGENT_RETRY_MIN_WAIT,
    AGENT_RETRY_MAX_WAIT,
    CACHE_ENABLED,
    CACHE_TTL_SECONDS,
    CIRCUIT_BREAKER_ENABLED,
    METRICS_ENABLED,
)
from ..utils.retry_utils import agent_retry
from ..utils.timeout_utils import with_timeout
from ..utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ..utils.metrics_utils import track_agent_metrics, _noop_decorator
from ..utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ..models.agent_results import GeolocationResult

logger = logging.getLogger(__name__)


class GeolocationAgent:
    """Agent specialized in geolocation analysis from visual clues."""

    def __init__(self):
        """Initialize Geolocation Agent with GPT-5.1 model."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=0.2,  # Low temperature for precise location identification
        )

        # Initialize circuit breaker ONCE per agent instance (shared state)
        if CIRCUIT_BREAKER_ENABLED:
            from ..config import (
                CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            )

            self.breaker = CircuitBreaker(
                failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            )
        else:
            self.breaker = None

        logger.info("ℹ️ GeolocationAgent initialized")

    def _analyze_internal(self, image_base64: str, context: str = "") -> Dict[str, Any]:
        """Internal analysis method."""
        logger.info("ℹ️ Starting geolocation analysis...")

        prompt = f"""Eres un experto en GEOLOCALIZACIÓN y análisis OSINT de imágenes.

{f"CONTEXTO: {context}" if context else ""}

Tu tarea es IDENTIFICAR LA UBICACIÓN geográfica basándote en pistas visuales de la imagen.

Analiza TODOS los elementos que pueden revelar ubicación:

## 1. IDENTIFICADORES DIRECTOS:
   - Nombres de calles, plazas, edificios
   - Señales de tráfico con nombres de lugares
   - Carteles de negocios con direcciones
   - Matrículas de vehículos (formato puede indicar país/región)
   - Códigos postales visibles

## 2. CARACTERÍSTICAS ARQUITECTÓNICAS:
   - Estilo de edificios (colonial, moderno, mediterráneo, etc.)
   - Tipo de construcción característico de región
   - Materiales de construcción típicos
   - Altura y densidad de edificios

## 3. SEÑALIZACIÓN Y MOBILIARIO URBANO:
   - Estilo de señales de tráfico
   - Diseño de semáforos, farolas, papeleras
   - Formato de placas de calle
   - Tipo de pavimento y aceras

## 4. VEGETACIÓN Y CLIMA:
   - Tipo de árboles y plantas (flora regional)
   - Condiciones climáticas aparentes
   - Altitud aparente (montaña, llanura, costa)

## 5. INFRAESTRUCTURA:
   - Tipo de red eléctrica (cables aéreos/subterráneos)
   - Diseño de alcantarillas y drenajes
   - Estilo de vallas y cercas

## 6. ELEMENTOS CULTURALES:
   - Idioma visible en carteles
   - Símbolos o banderas
   - Tipo de vehículos (modelos comunes en región)
   - Vestimenta de personas (si visible)

## 7. CONTEXTO GEOGRÁFICO:
   - Latitud aproximada (basándote en sombras, iluminación)
   - Hemisferio (norte/sur)
   - Proximidad a costa, montaña, desierto

## FORMATO DE RESPUESTA REQUERIDO:

**UBICACIÓN IDENTIFICADA:**
- País: [nombre del país o "No determinado"]
- Región/Estado/Provincia: [si identificable]
- Ciudad: [nombre de ciudad o "No determinado"]
- Distrito/Barrio: [si identificable]
- Calle/Plaza: [nombre específico si visible]
- Coordenadas estimadas: [lat, lon] o "No estimables"

**NIVEL DE CONFIANZA:**
- Muy Alto / Alto / Medio / Bajo / Muy Bajo

**PISTAS CLAVE UTILIZADAS:**
- Lista de 3-5 elementos que permitieron la identificación

**RAZONAMIENTO:**
- Explicación breve del proceso deductivo

**RECOMENDACIONES PARA VERIFICACIÓN:**
- Sugerencias para confirmar la ubicación (búsquedas, referencias)

IMPORTANTE:
- Si NO puedes determinar ubicación exacta, indica "No determinado" pero explica por qué
- Sé HONESTO sobre el nivel de confianza
- NO inventes ubicaciones sin evidencia visual clara
- Prioriza PRECISIÓN sobre especulación

RESPONDE EN ESPAÑOL de forma estructurada siguiendo el formato exacto."""

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_base64}},
            ]
        )

        response = self.llm.invoke([message])
        geolocation_text = response.content

        logger.info("✅ Geolocation analysis complete")

        # Extract structured data from response
        parsed_data = self._parse_geolocation_response(geolocation_text)

        return {
            "agent": "geolocation",
            "status": "success",
            "analysis": geolocation_text,
            "confidence": parsed_data.get("confidence", "unknown"),
            "location": parsed_data.get("location", {}),
            "coordinates": parsed_data.get("coordinates"),
            "key_clues": parsed_data.get("key_clues", []),
        }

    def _parse_geolocation_response(self, text: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract structured location data.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed location data
        """
        parsed = {
            "location": {},
            "confidence": "unknown",
            "coordinates": None,
            "key_clues": [],
        }

        # Extract country
        country_match = re.search(r"País:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if country_match:
            parsed["location"]["country"] = country_match.group(1).strip()

        # Extract city
        city_match = re.search(r"Ciudad:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if city_match:
            parsed["location"]["city"] = city_match.group(1).strip()

        # Extract district
        district_match = re.search(
            r"Distrito/Barrio:\s*(.+?)(?:\n|$)", text, re.IGNORECASE
        )
        if district_match:
            parsed["location"]["district"] = district_match.group(1).strip()

        # Extract street
        street_match = re.search(r"Calle/Plaza:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if street_match:
            parsed["location"]["street"] = street_match.group(1).strip()

        # Extract coordinates (various formats)
        coords_patterns = [
            r"Coordenadas.*?:\s*\[?\s*(-?\d+\.?\d*),\s*(-?\d+\.?\d*)\s*\]?",
            r"lat[itude]*:\s*(-?\d+\.?\d*).*?lon[gitude]*:\s*(-?\d+\.?\d*)",
            r"(-?\d+\.\d+),\s*(-?\d+\.\d+)",
        ]

        for pattern in coords_patterns:
            coords_match = re.search(pattern, text, re.IGNORECASE)
            if coords_match:
                try:
                    lat = float(coords_match.group(1))
                    lon = float(coords_match.group(2))
                    # Validate coordinates range
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        parsed["coordinates"] = {"lat": lat, "lon": lon}
                        break
                except (ValueError, IndexError):
                    continue

        # Extract confidence level
        confidence_match = re.search(
            r"NIVEL DE CONFIANZA.*?:\s*(Muy Alto|Alto|Medio|Bajo|Muy Bajo)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if confidence_match:
            parsed["confidence"] = confidence_match.group(1).lower()

        # Extract key clues (simple list extraction)
        clues_section = re.search(
            r"PISTAS CLAVE.*?:(.*?)(?:\*\*|$)", text, re.IGNORECASE | re.DOTALL
        )
        if clues_section:
            clues_text = clues_section.group(1)
            # Extract bullet points or numbered items
            clues = re.findall(r"[-•\d.]+\s*(.+?)(?:\n|$)", clues_text)
            parsed["key_clues"] = [c.strip() for c in clues if c.strip()][:5]

        return parsed

    @(track_agent_metrics("geolocation") if METRICS_ENABLED else _noop_decorator)
    @with_timeout(AGENT_TIMEOUT_SECONDS)
    @agent_retry(
        max_attempts=AGENT_RETRY_MAX_ATTEMPTS,
        min_wait=AGENT_RETRY_MIN_WAIT,
        max_wait=AGENT_RETRY_MAX_WAIT,
    )
    def _analyze_with_protection(
        self, image_base64: str, context: str = ""
    ) -> Dict[str, Any]:
        """Analyze with retry, timeout, and circuit breaker protection."""
        if self.breaker:
            try:
                # Use shared circuit breaker instance
                return self.breaker.call(self._analyze_internal, image_base64, context)
            except CircuitBreakerOpenError as e:
                logger.error(f"❌ Circuit breaker OPEN: {e}")
                return {
                    "agent": "geolocation",
                    "status": "error",
                    "error": "Circuit breaker is open - service temporarily unavailable",
                    "analysis": "Geolocation analysis unavailable",
                    "location": {},
                }
        else:
            return self._analyze_internal(image_base64, context)

    def analyze(self, image_base64: str, context: str = "") -> Dict[str, Any]:
        """
        Analyze image for geolocation clues.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with geolocation results including location data and coordinates
        """
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "geolocation", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached geolocation result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "geolocation", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = GeolocationResult(**result)
                return validated.model_dump()
            except Exception as validation_error:
                logger.warning(f"⚠️ Result validation failed: {validation_error}")
                return result

        except TimeoutError as e:
            logger.error(f"⏱️ Geolocation analysis timeout: {e}")
            return {
                "agent": "geolocation",
                "status": "timeout",
                "error": str(e),
                "analysis": "Geolocation analysis timed out",
                "location": {},
            }
        except Exception as e:
            logger.error(f"❌ Geolocation analysis failed: {e}")
            return {
                "agent": "geolocation",
                "status": "error",
                "error": str(e),
                "analysis": "Geolocation analysis failed",
                "location": {},
            }
