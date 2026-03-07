"""
NATO APP-6 Symbology Agent for military-grade entity classification.

Military Intelligence Analysis including:
- Entity identification and SIDC code assignment per NATO APP-6D
- Affiliation determination (friendly/hostile/neutral/unknown)
- Force composition assessment across detected entities
- Operational environment classification (domain, weather, terrain)
- Tactical graphic overlay recommendations for command displays
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from ...config import (
    AGENT_RETRY_MAX_ATTEMPTS,
    AGENT_RETRY_MAX_WAIT,
    AGENT_RETRY_MIN_WAIT,
    AGENT_TIMEOUT_SECONDS,
    CACHE_ENABLED,
    CACHE_TTL_SECONDS,
    CIRCUIT_BREAKER_ENABLED,
    METRICS_ENABLED,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)
from ...exceptions import (
    OpenAIAPIError,
    OpenAIRateLimitError,
    OpenAITimeoutError,
    PydanticValidationError,
)
from ...models.agent_results import NATOSymbologyResult
from ...utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ...utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ...utils.metrics_utils import _noop_decorator, track_agent_metrics
from ...utils.retry_utils import agent_retry
from ...utils.timeout_utils import with_timeout
from .prompts import NATO_SYMBOLOGY_PROMPT
from .response_parser import NATOSymbologyResponseParser

logger = logging.getLogger(__name__)


class NATOSymbologyAgent:
    """
    Agent specialized in NATO APP-6D standard symbology classification.

    Capabilities:
    - Entity identification and SIDC code assignment
    - Affiliation determination
    - Force composition assessment
    - Operational environment classification
    - Tactical graphic overlay recommendations
    """

    def __init__(self) -> None:
        """Initialize NATO Symbology Agent."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.2,  # Precision-critical for standardized classification
            **({"base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
        )

        self.parser = NATOSymbologyResponseParser()

        if CIRCUIT_BREAKER_ENABLED:
            from ...config import (
                CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            )

            self.breaker = CircuitBreaker(
                failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            )
        else:
            self.breaker = None

        logger.info("⚔️ NATOSymbologyAgent initialized (Military Entity Classification)")

    def _analyze_internal(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """Internal analysis method with NATO symbology prompt."""
        logger.info("⚔️ Starting military NATO symbology analysis...")

        context_section = f"CONTEXTO ADICIONAL: {context}" if context else ""
        prompt = NATO_SYMBOLOGY_PROMPT.format(context=context_section)

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_base64}},
            ]
        )

        response = self.llm.invoke([message])

        analysis_text = response.content
        if isinstance(analysis_text, list):
            analysis_text = " ".join(
                item.get("text", str(item)) if isinstance(item, dict) else str(item)
                for item in analysis_text
            )

        logger.info("✅ NATO symbology analysis complete")

        parsed_data = self.parser.parse(analysis_text)

        return {
            "agent": "nato_symbology",
            "status": "success",
            "analysis": analysis_text,
            "summary": parsed_data.get("summary"),
            "identified_entities": parsed_data.get("identified_entities", []),
            "force_composition": parsed_data.get("force_composition", {}),
            "operational_environment": parsed_data.get("operational_environment", {}),
            "tactical_graphics": parsed_data.get("tactical_graphics", []),
            "limitations": parsed_data.get("limitations", []),
        }

    @(track_agent_metrics("nato_symbology") if METRICS_ENABLED else _noop_decorator)
    @with_timeout(AGENT_TIMEOUT_SECONDS)
    @agent_retry(
        max_attempts=AGENT_RETRY_MAX_ATTEMPTS,
        min_wait=AGENT_RETRY_MIN_WAIT,
        max_wait=AGENT_RETRY_MAX_WAIT,
    )
    def _analyze_with_protection(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """Analyze with retry, timeout, and circuit breaker protection."""
        if self.breaker:
            try:
                return self.breaker.call(self._analyze_internal, image_base64, context)
            except CircuitBreakerOpenError as e:
                logger.error("❌ Circuit breaker OPEN: %s", e)
                return self._build_error_result(
                    "Circuit breaker is open - service temporarily unavailable"
                )
        else:
            return self._analyze_internal(image_base64, context)

    def analyze(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """
        Analyze image for NATO APP-6D entity classification.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with NATO symbology intelligence
        """
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "nato_symbology", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached NATO symbology result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "nato_symbology", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = NATOSymbologyResult(**result)
                return validated.model_dump()
            except PydanticValidationError as validation_error:
                logger.warning("⚠️ Result validation failed: %s", validation_error)
                return result

        except TimeoutError as e:
            logger.error("⏱️ NATO symbology timeout: %s", e)
            return self._build_error_result(str(e), status="timeout")

        except (OpenAIRateLimitError, OpenAITimeoutError, OpenAIAPIError) as e:
            logger.error("❌ OpenAI API error in NATO symbology: %s", e)
            return self._build_error_result(f"OpenAI API error: {e}")

        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid input to NATO symbology: %s", e)
            return self._build_error_result(f"Invalid input: {e}")

    def _build_error_result(self, error_message: str, status: str = "error") -> dict[str, Any]:
        """Build standardized error result with all required fields."""
        return {
            "agent": "nato_symbology",
            "status": status,
            "error": error_message,
            "analysis": f"NATO symbology analysis failed: {error_message}",
            "summary": None,
            "identified_entities": [],
            "force_composition": {
                "friendly": 0,
                "hostile": 0,
                "neutral": 0,
                "unknown": 0,
            },
            "operational_environment": {
                "domain": None,
                "weather_impact": None,
                "terrain_classification": None,
            },
            "tactical_graphics": [],
            "limitations": [error_message],
        }
