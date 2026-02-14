"""
Context Intelligence Agent for temporal and cultural inference using GPT-5.1.

CIA-Level OSINT Analysis including:
- Temporal analysis (time of day, season, era, specific dates)
- Cultural and socioeconomic indicators
- Event and activity classification
- Environmental conditions
- Anomaly detection
- Key inferences with confidence levels
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
from ...models.agent_results import ContextIntelResult
from ...utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ...utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ...utils.metrics_utils import _noop_decorator, track_agent_metrics
from ...utils.retry_utils import agent_retry
from ...utils.timeout_utils import with_timeout
from .prompts import CONTEXT_INTEL_PROMPT
from .response_parser import ContextIntelResponseParser

logger = logging.getLogger(__name__)


class ContextIntelAgent:
    """
    Agent specialized in CIA-level contextual intelligence extraction.

    Uses advanced inference techniques including:
    - Temporal analysis (when was this taken?)
    - Cultural context (what culture/society is this?)
    - Socioeconomic indicators (what economic level?)
    - Event classification (what's happening?)
    - Anomaly detection (what's unusual?)
    - Environmental conditions (weather, season)
    """

    def __init__(self) -> None:
        """Initialize Context Intelligence Agent with GPT-5.1 model."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.3,  # Slightly higher for inferential reasoning
            **({"base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
        )

        # Initialize response parser
        self.parser = ContextIntelResponseParser()

        # Initialize circuit breaker (lazy import to avoid circular deps)
        if CIRCUIT_BREAKER_ENABLED:
            from ...config import (  # noqa: PLC0415
                CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            )

            self.breaker = CircuitBreaker(
                failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            )
        else:
            self.breaker = None

        logger.info("🧠 ContextIntelAgent initialized (CIA-level temporal/cultural inference)")

    def _analyze_internal(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """
        Internal analysis method with context intelligence prompt.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with comprehensive contextual intelligence
        """
        logger.info("🧠 Starting CIA-level contextual intelligence analysis...")

        # Format prompt with context
        context_section = f"CONTEXTO ADICIONAL: {context}" if context else ""
        prompt = CONTEXT_INTEL_PROMPT.format(context=context_section)

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_base64}},
            ]
        )

        response = self.llm.invoke([message])

        # Handle response content type
        analysis_text = response.content
        if isinstance(analysis_text, list):
            analysis_text = " ".join(
                item.get("text", str(item)) if isinstance(item, dict) else str(item)
                for item in analysis_text
            )

        logger.info("✅ Context intelligence analysis complete")

        # Parse response using enhanced parser
        parsed_data = self.parser.parse(analysis_text)

        # Build comprehensive result
        return {
            "agent": "context_intel",
            "status": "success",
            "analysis": analysis_text,
            # Core intelligence
            "executive_summary": parsed_data.get("executive_summary"),
            "temporal_analysis": parsed_data.get("temporal_analysis", {}),
            "sociocultural_analysis": parsed_data.get("sociocultural_analysis", {}),
            "event_classification": parsed_data.get("event_classification", {}),
            "environmental_conditions": parsed_data.get("environmental_conditions", {}),
            # Insights
            "anomalies": parsed_data.get("anomalies", []),
            "key_inferences": parsed_data.get("key_inferences", []),
            # Metadata
            "limitations": parsed_data.get("limitations", []),
            "open_questions": parsed_data.get("open_questions", []),
        }

    @(track_agent_metrics("context_intel") if METRICS_ENABLED else _noop_decorator)
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
        Analyze image for contextual intelligence using CIA-level inference.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with comprehensive contextual intelligence including:
            - Executive summary
            - Temporal analysis (time, day, season, era)
            - Sociocultural analysis
            - Event classification
            - Environmental conditions
            - Anomalies and key inferences
            - Limitations and open questions
        """
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "context_intel", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached context intel result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "context_intel", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = ContextIntelResult(**result)
                return validated.model_dump()
            except PydanticValidationError as validation_error:
                logger.warning("⚠️ Result validation failed: %s", validation_error)
                return result

        except TimeoutError as e:
            logger.error("⏱️ Context intel timeout: %s", e)
            return self._build_error_result(str(e), status="timeout")

        except (OpenAIRateLimitError, OpenAITimeoutError, OpenAIAPIError) as e:
            logger.error("❌ OpenAI API error in context intel: %s", e)
            return self._build_error_result(f"OpenAI API error: {e}")

        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid input to context intel: %s", e)
            return self._build_error_result(f"Invalid input: {e}")

    def _build_error_result(self, error_message: str, status: str = "error") -> dict[str, Any]:
        """Build standardized error result with all required fields."""
        return {
            "agent": "context_intel",
            "status": status,
            "error": error_message,
            "analysis": f"Context intelligence analysis failed: {error_message}",
            "executive_summary": None,
            "temporal_analysis": {
                "time_of_day": {"value": None, "confidence": None, "evidence": []},
                "day_type": {"value": None, "confidence": None, "evidence": []},
                "season": {"value": None, "confidence": None, "evidence": []},
                "era": {"value": None, "confidence": None, "evidence": []},
                "specific_date": {"value": None, "confidence": None, "evidence": []},
            },
            "sociocultural_analysis": {
                "socioeconomic_level": None,
                "socioeconomic_indicators": [],
                "cultural_context": None,
                "cultural_indicators": [],
                "political_situation": None,
                "political_indicators": [],
            },
            "event_classification": {
                "event_type": None,
                "event_subtype": None,
                "primary_purpose": None,
                "social_dynamics": None,
            },
            "environmental_conditions": {
                "weather": None,
                "temperature": None,
                "special_conditions": None,
            },
            "anomalies": [],
            "key_inferences": [],
            "limitations": [error_message],
            "open_questions": [],
        }
