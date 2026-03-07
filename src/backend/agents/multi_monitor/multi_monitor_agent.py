"""
Multi-Monitor Layout Agent for command center display optimization.

Military Intelligence Analysis including:
- Scene complexity assessment for display configuration
- Multi-monitor layout recommendations (count, arrangement, type)
- Information density analysis and panel prioritization
- Alert priority classification and recommended actions
- Zoom area identification and declutter suggestions
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
from ...models.agent_results import MultiMonitorResult
from ...utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ...utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ...utils.metrics_utils import _noop_decorator, track_agent_metrics
from ...utils.retry_utils import agent_retry
from ...utils.timeout_utils import with_timeout
from .prompts import MULTI_MONITOR_PROMPT
from .response_parser import MultiMonitorResponseParser

logger = logging.getLogger(__name__)


class MultiMonitorAgent:
    """
    Agent specialized in command center multi-monitor display optimization.

    Capabilities:
    - Scene complexity assessment
    - Multi-monitor layout recommendations
    - Information density analysis
    - Alert priority classification
    - Zoom area and declutter suggestions
    """

    def __init__(self) -> None:
        """Initialize Multi-Monitor Layout Agent."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.3,  # Balanced for layout inference
            **({"base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
        )

        self.parser = MultiMonitorResponseParser()

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

        logger.info("🖥️ MultiMonitorAgent initialized (Command Center Display Optimization)")

    def _analyze_internal(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """Internal analysis method with multi-monitor layout prompt."""
        logger.info("🖥️ Starting command center layout analysis...")

        context_section = f"CONTEXTO ADICIONAL: {context}" if context else ""
        prompt = MULTI_MONITOR_PROMPT.format(context=context_section)

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

        logger.info("✅ Multi-monitor layout analysis complete")

        parsed_data = self.parser.parse(analysis_text)

        return {
            "agent": "multi_monitor",
            "status": "success",
            "analysis": analysis_text,
            "summary": parsed_data.get("summary"),
            "scene_complexity": parsed_data.get("scene_complexity", {}),
            "layout_recommendation": parsed_data.get("layout_recommendation", {}),
            "information_density": parsed_data.get("information_density", {}),
            "alert_priorities": parsed_data.get("alert_priorities", []),
            "limitations": parsed_data.get("limitations", []),
        }

    @(track_agent_metrics("multi_monitor") if METRICS_ENABLED else _noop_decorator)
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
        Analyze image for optimal command center display configuration.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with multi-monitor layout intelligence
        """
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "multi_monitor", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached multi-monitor layout result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "multi_monitor", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = MultiMonitorResult(**result)
                return validated.model_dump()
            except PydanticValidationError as validation_error:
                logger.warning("⚠️ Result validation failed: %s", validation_error)
                return result

        except TimeoutError as e:
            logger.error("⏱️ Multi-monitor layout timeout: %s", e)
            return self._build_error_result(str(e), status="timeout")

        except (OpenAIRateLimitError, OpenAITimeoutError, OpenAIAPIError) as e:
            logger.error("❌ OpenAI API error in multi-monitor layout: %s", e)
            return self._build_error_result(f"OpenAI API error: {e}")

        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid input to multi-monitor layout: %s", e)
            return self._build_error_result(f"Invalid input: {e}")

    def _build_error_result(self, error_message: str, status: str = "error") -> dict[str, Any]:
        """Build standardized error result with all required fields."""
        return {
            "agent": "multi_monitor",
            "status": status,
            "error": error_message,
            "analysis": f"Multi-monitor layout analysis failed: {error_message}",
            "summary": None,
            "scene_complexity": {
                "level": None,
                "detail_density": None,
                "priority_agents": [],
                "recommended_panels": None,
            },
            "layout_recommendation": {
                "monitor_count": None,
                "primary_display": None,
                "secondary_displays": [],
                "layout_type": None,
            },
            "information_density": {
                "critical_data_points": [],
                "recommended_zoom_areas": [],
                "declutter_suggestions": [],
            },
            "alert_priorities": [],
            "limitations": [error_message],
        }
