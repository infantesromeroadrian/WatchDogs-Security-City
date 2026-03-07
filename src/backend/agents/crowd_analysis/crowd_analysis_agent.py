"""
Crowd Analysis Agent for military-grade crowd intelligence.

Military Intelligence Analysis including:
- Crowd density estimation (persons per area)
- Demographic composition analysis
- Movement patterns and flow detection
- Anomalous behavior identification
- Group formation analysis
- Panic/distress indicators and security concerns
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
from ...models.agent_results import CrowdAnalysisResult
from ...utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ...utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ...utils.metrics_utils import _noop_decorator, track_agent_metrics
from ...utils.retry_utils import agent_retry
from ...utils.timeout_utils import with_timeout
from .prompts import CROWD_ANALYSIS_PROMPT
from .response_parser import CrowdAnalysisResponseParser

logger = logging.getLogger(__name__)


class CrowdAnalysisAgent:
    """
    Agent specialized in military-grade crowd analysis.

    Capabilities:
    - Crowd density estimation (persons per area)
    - Demographic composition analysis
    - Movement patterns and flow detection
    - Anomalous behavior identification
    - Group formation analysis
    - Panic/distress indicators
    """

    def __init__(self) -> None:
        """Initialize Crowd Analysis Agent."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.3,  # Moderate for behavioral inference
            **({"base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
        )

        self.parser = CrowdAnalysisResponseParser()

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

        logger.info("👥 CrowdAnalysisAgent initialized (Military Crowd Intelligence)")

    def _analyze_internal(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """Internal analysis method with crowd analysis prompt."""
        logger.info("👥 Starting military crowd analysis...")

        context_section = f"CONTEXTO ADICIONAL: {context}" if context else ""
        prompt = CROWD_ANALYSIS_PROMPT.format(context=context_section)

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

        logger.info("✅ Crowd analysis complete")

        parsed_data = self.parser.parse(analysis_text)

        return {
            "agent": "crowd_analysis",
            "status": "success",
            "analysis": analysis_text,
            "summary": parsed_data.get("summary"),
            "density_estimate": parsed_data.get("density_estimate", {}),
            "demographics": parsed_data.get("demographics", {}),
            "movement_patterns": parsed_data.get("movement_patterns", {}),
            "behavioral_assessment": parsed_data.get("behavioral_assessment", {}),
            "security_concerns": parsed_data.get("security_concerns", []),
            "limitations": parsed_data.get("limitations", []),
        }

    @(track_agent_metrics("crowd_analysis") if METRICS_ENABLED else _noop_decorator)
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
        Analyze image for crowd density, demographics, and behavioral patterns.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with crowd intelligence including density and behavioral assessment
        """
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "crowd_analysis", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached crowd analysis result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "crowd_analysis", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = CrowdAnalysisResult(**result)
                return validated.model_dump()
            except PydanticValidationError as validation_error:
                logger.warning("⚠️ Result validation failed: %s", validation_error)
                return result

        except TimeoutError as e:
            logger.error("⏱️ Crowd analysis timeout: %s", e)
            return self._build_error_result(str(e), status="timeout")

        except (OpenAIRateLimitError, OpenAITimeoutError, OpenAIAPIError) as e:
            logger.error("❌ OpenAI API error in crowd analysis: %s", e)
            return self._build_error_result(f"OpenAI API error: {e}")

        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid input to crowd analysis: %s", e)
            return self._build_error_result(f"Invalid input: {e}")

    def _build_error_result(self, error_message: str, status: str = "error") -> dict[str, Any]:
        """Build standardized error result with all required fields."""
        return {
            "agent": "crowd_analysis",
            "status": status,
            "error": error_message,
            "analysis": f"Crowd analysis failed: {error_message}",
            "summary": None,
            "density_estimate": {
                "total_count": None,
                "density_level": None,
                "zones": {},
            },
            "demographics": {},
            "movement_patterns": {},
            "behavioral_assessment": {
                "general_mood": None,
                "anomalous_behaviors": None,
                "group_formations": None,
            },
            "security_concerns": [],
            "limitations": [error_message],
        }
