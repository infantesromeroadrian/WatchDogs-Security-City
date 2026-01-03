"""
Vision Agent for general scene analysis using GPT-5.1.
"""

import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_MAX_TOKENS,
    OPENAI_TEMPERATURE,
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
from ..models.agent_results import VisionResult

logger = logging.getLogger(__name__)


class VisionAgent:
    """Agent specialized in general visual scene analysis."""

    def __init__(self):
        """Initialize Vision Agent with GPT-5.1 model."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE,
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

        logger.info("ℹ️ VisionAgent initialized")

    def _analyze_internal(self, image_base64: str, context: str = "") -> Dict[str, Any]:
        """Internal analysis method (wrapped with retry/timeout)."""
        logger.info("ℹ️ Starting general vision analysis...")

        # Check if this is a specific question or general analysis
        is_specific_question = context and any(
            keyword in context.lower()
            for keyword in [
                "pregunta",
                "question",
                "qué",
                "cuál",
                "cuánto",
                "dónde",
                "cuándo",
                "color",
                "tipo",
                "detalle",
                "específico",
                "roi",
                "región",
            ]
        )

        if is_specific_question:
            # Prompt for specific questions (conversational)
            prompt = f"""{context}

IMPORTANTE: Responde DIRECTAMENTE a la pregunta del usuario de forma concisa y específica.
- Si preguntan sobre un color, objeto o detalle específico, identifícalo claramente.
- Si la pregunta es sobre algo en el ROI, enfócate SOLO en esa región.
- Sé preciso y evita respuestas genéricas o largas descripciones de toda la escena.
- Si no puedes ver claramente lo que preguntan, dilo directamente.

RESPONDE EN ESPAÑOL de forma directa y concisa."""
        else:
            # Prompt for general analysis
            prompt = f"""Describe lo que ves en esta imagen para documentación de investigación.

{f"Contexto: {context}" if context else ""}

Proporciona un análisis estructurado:

1. DESCRIPCIÓN DE LA ESCENA: ¿Qué tipo de entorno se muestra? (tipo de ubicación, contexto, condiciones)

2. ELEMENTOS VISIBLES:
   - Objetos o elementos notables
   - Vehículos (tipo, color si es visible)
   - Señales o texto visible
   - Tecnología o equipamiento

3. CONTEXTO TEMPORAL/ESPACIAL:
   - Hora aproximada del día (basándote en la iluminación)
   - Condiciones climáticas
   - Interior/exterior, urbano/rural

4. PUNTOS DE INTERÉS:
   - Elementos que podrían ser relevantes para la investigación
   - Detalles inusuales o notables

Sé objetivo y factual en tu análisis. RESPONDE EN ESPAÑOL."""

        # Create message with image
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_base64}},
            ]
        )

        # Get response from LLM
        response = self.llm.invoke([message])
        analysis_text = response.content

        logger.info("✅ General vision analysis complete")

        return {
            "agent": "vision",
            "status": "success",
            "analysis": analysis_text,
            "confidence": "high",
        }

    @(track_agent_metrics("vision") if METRICS_ENABLED else _noop_decorator)
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
                    "agent": "vision",
                    "status": "error",
                    "error": "Circuit breaker is open - service temporarily unavailable",
                    "analysis": "Vision analysis unavailable",
                }
        else:
            return self._analyze_internal(image_base64, context)

    def analyze(self, image_base64: str, context: str = "") -> Dict[str, Any]:
        """
        Analyze image for general scene understanding.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context or specific questions

        Returns:
            Dict with analysis results (validated with Pydantic)
        """
        try:
            # Check cache first
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "vision", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached vision result")
                    return cached

            # Execute analysis with protection (retry, timeout, metrics)
            result = self._analyze_with_protection(image_base64, context)

            # Cache result if successful
            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "vision", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            # Validate result with Pydantic
            try:
                validated = VisionResult(**result)
                return validated.model_dump()
            except Exception as validation_error:
                logger.warning(
                    f"⚠️ Result validation failed: {validation_error}, returning raw result"
                )
                return result

        except TimeoutError as e:
            logger.error(f"⏱️ Vision analysis timeout: {e}")
            return {
                "agent": "vision",
                "status": "timeout",
                "error": str(e),
                "analysis": "Vision analysis timed out",
            }
        except Exception as e:
            logger.error(f"❌ Vision analysis failed: {e}")
            return {
                "agent": "vision",
                "status": "error",
                "error": str(e),
                "analysis": "Vision analysis failed",
            }
