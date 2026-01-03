"""
Detection Agent for object and person detection using GPT-5.1 (Improved with retry, timeout, caching, metrics).
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
from ..models.agent_results import DetectionResult

logger = logging.getLogger(__name__)


class DetectionAgent:
    """Agent specialized in object and person detection."""

    def __init__(self):
        """Initialize Detection Agent with GPT-5.1 model."""
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

        logger.info("ℹ️ DetectionAgent initialized")

    def _analyze_internal(self, image_base64: str, context: str = "") -> Dict[str, Any]:
        """Internal analysis method."""
        logger.info("ℹ️ Starting object/person detection...")

        prompt = f"""Cataloga los objetos y elementos visibles en esta imagen para documentación.

{f"Contexto: {context}" if context else ""}

Proporciona un inventario:

1. OBJETOS DETECTADOS:
   - Recuento y tipo de elementos visibles
   - Posición en la escena
   - Características generales

2. VEHÍCULOS (si los hay):
   - Tipo (coche, motocicleta, camión, bicicleta)
   - Color aproximado
   - Características notables

3. INFRAESTRUCTURA:
   - Edificios o estructuras
   - Equipamiento o instalaciones
   - Características ambientales notables

4. DETALLES TÉCNICOS:
   - Calidad de la imagen
   - Condiciones de visibilidad
   - Elementos que limiten la visibilidad

Sé factual y objetivo. RESPONDE EN ESPAÑOL."""

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_base64}},
            ]
        )

        response = self.llm.invoke([message])
        detection_text = response.content

        logger.info("✅ Object/person detection complete")

        return {
            "agent": "detection",
            "status": "success",
            "analysis": detection_text,
            "confidence": "high",
        }

    @(track_agent_metrics("detection") if METRICS_ENABLED else _noop_decorator)
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
                    "agent": "detection",
                    "status": "error",
                    "error": "Circuit breaker is open - service temporarily unavailable",
                    "analysis": "Detection analysis unavailable",
                }
        else:
            return self._analyze_internal(image_base64, context)

    def analyze(self, image_base64: str, context: str = "") -> Dict[str, Any]:
        """Detect and catalog objects and people in image."""
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "detection", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached detection result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "detection", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = DetectionResult(**result)
                return validated.model_dump()
            except Exception as validation_error:
                logger.warning(f"⚠️ Result validation failed: {validation_error}")
                return result

        except TimeoutError as e:
            logger.error(f"⏱️ Detection analysis timeout: {e}")
            return {
                "agent": "detection",
                "status": "timeout",
                "error": str(e),
                "analysis": "Detection analysis timed out",
            }
        except Exception as e:
            logger.error(f"❌ Detection analysis failed: {e}")
            return {
                "agent": "detection",
                "status": "error",
                "error": str(e),
                "analysis": "Detection analysis failed",
            }
