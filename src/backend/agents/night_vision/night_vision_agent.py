"""
Night Vision Enhancement Agent for military-grade low-light intelligence.

Military Intelligence Analysis including:
- Low-light scene enhancement and interpretation
- Light source identification and classification
- Infrared/thermal signature inference from visible cues
- Night activity pattern detection (personnel, vehicles, operations)
- Covert activity indicators (concealment, blacked-out vehicles)
- Tactical night vulnerability assessment
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
from ...models.agent_results import NightVisionResult
from ...utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ...utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ...utils.metrics_utils import _noop_decorator, track_agent_metrics
from ...utils.retry_utils import agent_retry
from ...utils.timeout_utils import with_timeout
from .prompts import NIGHT_VISION_PROMPT
from .response_parser import NightVisionResponseParser

logger = logging.getLogger(__name__)


class NightVisionAgent:
    """
    Agent specialized in military-grade night vision and low-light analysis.

    Capabilities:
    - Low-light scene interpretation
    - Light source identification and classification
    - Thermal signature inference
    - Night activity pattern detection
    - Covert activity indicator identification
    - Tactical night vulnerability assessment
    """

    def __init__(self) -> None:
        """Initialize Night Vision Agent."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.2,  # Precision for low-light analysis
            **({"base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
        )

        self.parser = NightVisionResponseParser()

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

        logger.info("🌙 NightVisionAgent initialized (Military Low-Light Intelligence)")

    def _analyze_internal(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """Internal analysis method with night vision prompt."""
        logger.info("🌙 Starting military night vision analysis...")

        context_section = f"CONTEXTO ADICIONAL: {context}" if context else ""
        prompt = NIGHT_VISION_PROMPT.format(context=context_section)

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

        logger.info("✅ Night vision analysis complete")

        parsed_data = self.parser.parse(analysis_text)

        return {
            "agent": "night_vision",
            "status": "success",
            "analysis": analysis_text,
            "summary": parsed_data.get("summary"),
            "visibility_conditions": parsed_data.get("visibility_conditions", {}),
            "light_sources": parsed_data.get("light_sources", {}),
            "nocturnal_activity": parsed_data.get("nocturnal_activity", {}),
            "covert_indicators": parsed_data.get("covert_indicators", {}),
            "tactical_assessment": parsed_data.get("tactical_assessment", {}),
            "limitations": parsed_data.get("limitations", []),
        }

    @(track_agent_metrics("night_vision") if METRICS_ENABLED else _noop_decorator)
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
        Analyze image for night vision intelligence and tactical assessment.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with night vision intelligence including tactical assessment
        """
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "night_vision", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached night vision result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "night_vision", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = NightVisionResult(**result)
                return validated.model_dump()
            except PydanticValidationError as validation_error:
                logger.warning("⚠️ Result validation failed: %s", validation_error)
                return result

        except TimeoutError as e:
            logger.error("⏱️ Night vision timeout: %s", e)
            return self._build_error_result(str(e), status="timeout")

        except (OpenAIRateLimitError, OpenAITimeoutError, OpenAIAPIError) as e:
            logger.error("❌ OpenAI API error in night vision: %s", e)
            return self._build_error_result(f"OpenAI API error: {e}")

        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid input to night vision: %s", e)
            return self._build_error_result(f"Invalid input: {e}")

    def _build_error_result(self, error_message: str, status: str = "error") -> dict[str, Any]:
        """Build standardized error result with all required fields."""
        return {
            "agent": "night_vision",
            "status": status,
            "error": error_message,
            "analysis": f"Night vision analysis failed: {error_message}",
            "summary": None,
            "visibility_conditions": {
                "illumination_level": None,
                "observation_range": None,
                "image_quality": None,
            },
            "light_sources": {
                "total_count": None,
                "dominant_type": None,
                "anomalous_sources": None,
            },
            "nocturnal_activity": {
                "activity_level": None,
                "personnel_detected": None,
                "active_vehicles": None,
                "operations": None,
            },
            "covert_indicators": {
                "concealment_detected": None,
                "thermal_signatures": None,
                "suspicion_level": None,
            },
            "tactical_assessment": {
                "vulnerabilities": None,
                "surveillance_coverage": None,
                "night_risk_level": None,
            },
            "limitations": [error_message],
        }
