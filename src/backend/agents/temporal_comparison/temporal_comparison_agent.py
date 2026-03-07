"""
Temporal Comparison Agent for military-grade change detection intelligence.

Military Intelligence Analysis including:
- Scene change detection indicators from single-image evidence
- Construction, demolition, and structural modification tracking
- Activity level assessment (personnel, vehicles, logistics)
- Strategic posture classification (BUILDUP/WITHDRAWAL/FORTIFICATION/NORMAL/CRISIS)
- Environmental and terrain change indicators
- Estimated chronology of detected changes
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
from ...models.agent_results import TemporalComparisonResult
from ...utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ...utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ...utils.metrics_utils import _noop_decorator, track_agent_metrics
from ...utils.retry_utils import agent_retry
from ...utils.timeout_utils import with_timeout
from .prompts import TEMPORAL_COMPARISON_PROMPT
from .response_parser import TemporalComparisonResponseParser

logger = logging.getLogger(__name__)


class TemporalComparisonAgent:
    """
    Agent specialized in military-grade temporal change detection.

    Capabilities:
    - Scene change indicator detection from single-image evidence
    - Construction and demolition activity identification
    - Activity level and type assessment
    - Strategic posture classification
    - Environmental change indicators
    - Event chronology estimation
    """

    def __init__(self) -> None:
        """Initialize Temporal Comparison Agent."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.3,  # Balanced for change inference
            **({"base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
        )

        self.parser = TemporalComparisonResponseParser()

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

        logger.info("🕐 TemporalComparisonAgent initialized (Military Change Detection)")

    def _analyze_internal(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """Internal analysis method with temporal comparison prompt."""
        logger.info("🕐 Starting military temporal change analysis...")

        context_section = f"CONTEXTO ADICIONAL: {context}" if context else ""
        prompt = TEMPORAL_COMPARISON_PROMPT.format(context=context_section)

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

        logger.info("✅ Temporal change analysis complete")

        parsed_data = self.parser.parse(analysis_text)

        return {
            "agent": "temporal_comparison",
            "status": "success",
            "analysis": analysis_text,
            "summary": parsed_data.get("summary"),
            "structural_changes": parsed_data.get("structural_changes", {}),
            "activity_detection": parsed_data.get("activity_detection", {}),
            "strategic_posture": parsed_data.get("strategic_posture", {}),
            "environmental_changes": parsed_data.get("environmental_changes", {}),
            "chronology": parsed_data.get("chronology", []),
            "limitations": parsed_data.get("limitations", []),
        }

    @(track_agent_metrics("temporal_comparison") if METRICS_ENABLED else _noop_decorator)
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
        Analyze image for temporal change indicators and strategic posture.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with temporal change intelligence
        """
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "temporal_comparison", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached temporal comparison result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "temporal_comparison", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = TemporalComparisonResult(**result)
                return validated.model_dump()
            except PydanticValidationError as validation_error:
                logger.warning("⚠️ Result validation failed: %s", validation_error)
                return result

        except TimeoutError as e:
            logger.error("⏱️ Temporal comparison timeout: %s", e)
            return self._build_error_result(str(e), status="timeout")

        except (OpenAIRateLimitError, OpenAITimeoutError, OpenAIAPIError) as e:
            logger.error("❌ OpenAI API error in temporal comparison: %s", e)
            return self._build_error_result(f"OpenAI API error: {e}")

        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid input to temporal comparison: %s", e)
            return self._build_error_result(f"Invalid input: {e}")

    def _build_error_result(self, error_message: str, status: str = "error") -> dict[str, Any]:
        """Build standardized error result with all required fields."""
        return {
            "agent": "temporal_comparison",
            "status": status,
            "error": error_message,
            "analysis": f"Temporal comparison failed: {error_message}",
            "summary": None,
            "structural_changes": {
                "active_construction": None,
                "recent_damage": None,
                "temporary_structures": [],
                "estimated_age": None,
            },
            "activity_detection": {
                "activity_level": None,
                "predominant_type": None,
                "unusual_patterns": None,
            },
            "strategic_posture": {
                "classification": None,
                "confidence": None,
                "evidence": None,
            },
            "environmental_changes": {
                "vegetation": None,
                "terrain": None,
                "climate_indicators": None,
            },
            "chronology": [],
            "limitations": [error_message],
        }
