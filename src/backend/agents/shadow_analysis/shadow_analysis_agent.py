"""
Shadow/Sun Analysis Agent for military-grade temporal and geographic intelligence.

Military Intelligence Analysis including:
- Sun position estimation (azimuth, elevation)
- Shadow angle measurement and consistency verification
- Time-of-day estimation from shadow geometry
- Season inference from sun elevation patterns
- Geographic hemisphere determination
- Artificial vs natural lighting distinction
- Forensic consistency check for image manipulation detection
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
from ...models.agent_results import ShadowAnalysisResult
from ...utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ...utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ...utils.metrics_utils import _noop_decorator, track_agent_metrics
from ...utils.retry_utils import agent_retry
from ...utils.timeout_utils import with_timeout
from .prompts import SHADOW_ANALYSIS_PROMPT
from .response_parser import ShadowAnalysisResponseParser

logger = logging.getLogger(__name__)


class ShadowAnalysisAgent:
    """
    Agent specialized in military-grade shadow and sun analysis.

    Capabilities:
    - Sun position estimation (azimuth, elevation)
    - Shadow angle measurement and consistency check
    - Time-of-day estimation from shadow geometry
    - Season inference from sun elevation patterns
    - Geographic hemisphere determination
    - Artificial vs natural lighting distinction
    - Forensic consistency check for manipulation detection
    """

    def __init__(self) -> None:
        """Initialize Shadow Analysis Agent."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.2,  # Precision for geometric calculations
            **({"base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
        )

        self.parser = ShadowAnalysisResponseParser()

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

        logger.info("🌅 ShadowAnalysisAgent initialized (Military Solar Intelligence)")

    def _analyze_internal(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """Internal analysis method with shadow analysis prompt."""
        logger.info("🌅 Starting military shadow & sun analysis...")

        context_section = f"CONTEXTO ADICIONAL: {context}" if context else ""
        prompt = SHADOW_ANALYSIS_PROMPT.format(context=context_section)

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

        logger.info("✅ Shadow & sun analysis complete")

        parsed_data = self.parser.parse(analysis_text)

        return {
            "agent": "shadow_analysis",
            "status": "success",
            "analysis": analysis_text,
            "summary": parsed_data.get("summary"),
            "shadow_geometry": parsed_data.get("shadow_geometry", {}),
            "sun_position": parsed_data.get("sun_position", {}),
            "time_estimate": parsed_data.get("time_estimate", {}),
            "season_inference": parsed_data.get("season_inference", {}),
            "lighting_analysis": parsed_data.get("lighting_analysis", {}),
            "forensic_indicators": parsed_data.get("forensic_indicators", []),
            "limitations": parsed_data.get("limitations", []),
        }

    @(track_agent_metrics("shadow_analysis") if METRICS_ENABLED else _noop_decorator)
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
        Analyze image for shadow geometry, sun position, and temporal intelligence.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with shadow intelligence including time and season estimates
        """
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "shadow_analysis", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached shadow analysis result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "shadow_analysis", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = ShadowAnalysisResult(**result)
                return validated.model_dump()
            except PydanticValidationError as validation_error:
                logger.warning("⚠️ Result validation failed: %s", validation_error)
                return result

        except TimeoutError as e:
            logger.error("⏱️ Shadow analysis timeout: %s", e)
            return self._build_error_result(str(e), status="timeout")

        except (OpenAIRateLimitError, OpenAITimeoutError, OpenAIAPIError) as e:
            logger.error("❌ OpenAI API error in shadow analysis: %s", e)
            return self._build_error_result(f"OpenAI API error: {e}")

        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid input to shadow analysis: %s", e)
            return self._build_error_result(f"Invalid input: {e}")

    def _build_error_result(self, error_message: str, status: str = "error") -> dict[str, Any]:
        """Build standardized error result with all required fields."""
        return {
            "agent": "shadow_analysis",
            "status": status,
            "error": error_message,
            "analysis": f"Shadow analysis failed: {error_message}",
            "summary": None,
            "shadow_geometry": {
                "direction": None,
                "length_ratio": None,
                "consistency": None,
            },
            "sun_position": {
                "azimuth_estimate": None,
                "elevation_estimate": None,
                "hemisphere": None,
            },
            "time_estimate": {
                "time_range": None,
                "confidence": None,
                "evidence": None,
            },
            "season_inference": {
                "estimated_season": None,
                "confidence": None,
                "evidence": None,
            },
            "lighting_analysis": {
                "primary_source": None,
                "artificial_sources": None,
                "consistency": None,
            },
            "forensic_indicators": [],
            "limitations": [error_message],
        }
