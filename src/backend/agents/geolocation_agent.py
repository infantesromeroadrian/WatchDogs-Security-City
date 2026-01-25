"""
Geolocation Agent for identifying location details from images using GPT-5.1.

CIA-Level OSINT Analysis including:
- Hierarchical location (Country → Region → City → District → Street → Number)
- Coordinates with confidence radius
- Evidence chain with individual confidence scores
- Temporal analysis (time, season, date estimates)
- Verification suggestions

REFACTORED: Prompt and parsing logic extracted to separate modules
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from ..config import (
    AGENT_RETRY_MAX_ATTEMPTS,
    AGENT_RETRY_MAX_WAIT,
    AGENT_RETRY_MIN_WAIT,
    AGENT_TIMEOUT_SECONDS,
    CACHE_ENABLED,
    CACHE_TTL_SECONDS,
    CIRCUIT_BREAKER_ENABLED,
    METRICS_ENABLED,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from ..exceptions import (
    OpenAIAPIError,
    OpenAIRateLimitError,
    OpenAITimeoutError,
    PydanticValidationError,
)
from ..models.agent_results import GeolocationResult
from ..utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ..utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ..utils.metrics_utils import _noop_decorator, track_agent_metrics
from ..utils.retry_utils import agent_retry
from ..utils.timeout_utils import with_timeout
from .geolocation.prompts import GEOLOCATION_PROMPT
from .geolocation.response_parser import GeolocationResponseParser

logger = logging.getLogger(__name__)


class GeolocationAgent:
    """
    Agent specialized in CIA-level geolocation analysis from visual clues.

    Uses advanced OSINT techniques including:
    - Sun shadow analysis for latitude/time estimation
    - Infrastructure pattern recognition (power grids, road markings, bollards)
    - Vegetation species identification for climate zones
    - Cultural and temporal markers
    - Cross-reference verification chains
    """

    def __init__(self) -> None:
        """Initialize Geolocation Agent with GPT-5.1 model."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.2,  # Low temperature for precise location identification
        )

        # Initialize response parser
        self.parser = GeolocationResponseParser()

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

        logger.info("ℹ️ GeolocationAgent initialized (CIA-level OSINT)")

    def _analyze_internal(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """
        Internal analysis method with CIA-level prompt.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with comprehensive geolocation intelligence
        """
        logger.info("ℹ️ Starting CIA-level geolocation analysis...")

        # Format prompt with context (using template from prompts.py)
        context_section = f"CONTEXTO ADICIONAL: {context}" if context else ""
        prompt = GEOLOCATION_PROMPT.format(context=context_section)

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_base64}},
            ]
        )

        response = self.llm.invoke([message])

        # Handle response content type
        geolocation_text = response.content
        if isinstance(geolocation_text, list):
            # If content is a list, join text parts
            geolocation_text = " ".join(
                item.get("text", str(item)) if isinstance(item, dict) else str(item)
                for item in geolocation_text
            )

        logger.info("✅ Geolocation analysis complete")

        # Parse response using enhanced parser
        parsed_data = self.parser.parse(geolocation_text)

        # Build comprehensive result with all CIA-level fields
        return {
            "agent": "geolocation",
            "status": "success",
            "analysis": geolocation_text,
            # Core location data
            "location": parsed_data.get("location", {}),
            "coordinates": parsed_data.get("coordinates"),
            # Confidence levels
            "confidence": parsed_data.get("confidence", "unknown"),
            "confidence_by_level": parsed_data.get("confidence_by_level", {}),
            # Evidence and analysis
            "evidence_chain": parsed_data.get("evidence_chain", []),
            "key_clues": parsed_data.get("key_clues", []),
            # Temporal analysis
            "temporal_analysis": parsed_data.get("temporal_analysis", {}),
            # Limitations and verification
            "limitations": parsed_data.get("limitations", []),
            "verification_suggestions": parsed_data.get("verification_suggestions", {}),
        }

    @(track_agent_metrics("geolocation") if METRICS_ENABLED else _noop_decorator)
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
                # Use shared circuit breaker instance
                return self.breaker.call(self._analyze_internal, image_base64, context)
            except CircuitBreakerOpenError as e:
                logger.error(f"❌ Circuit breaker OPEN: {e}")
                return self._build_error_result(
                    "Circuit breaker is open - service temporarily unavailable"
                )
        else:
            return self._analyze_internal(image_base64, context)

    def analyze(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """
        Analyze image for geolocation clues using CIA-level OSINT techniques.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with comprehensive geolocation results including:
            - Hierarchical location (country → street level)
            - Coordinates with confidence radius
            - Evidence chain with confidence scores
            - Temporal analysis
            - Verification suggestions
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
            except PydanticValidationError as validation_error:
                logger.warning(f"⚠️ Result validation failed: {validation_error}")
                return result

        except TimeoutError as e:
            logger.error(f"⏱️ Geolocation analysis timeout: {e}")
            return self._build_error_result(str(e), status="timeout")

        except (OpenAIRateLimitError, OpenAITimeoutError, OpenAIAPIError) as e:
            logger.error(f"❌ OpenAI API error in geolocation analysis: {e}")
            return self._build_error_result(f"OpenAI API error: {e}")

        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid input to geolocation analysis: {e}")
            return self._build_error_result(f"Invalid input: {e}")

    def _build_error_result(self, error_message: str, status: str = "error") -> dict[str, Any]:
        """Build standardized error result with all required fields."""
        return {
            "agent": "geolocation",
            "status": status,
            "error": error_message,
            "analysis": f"Geolocation analysis failed: {error_message}",
            "location": {},
            "coordinates": None,
            "confidence": "unknown",
            "confidence_by_level": {},
            "evidence_chain": [],
            "key_clues": [],
            "temporal_analysis": {},
            "limitations": [error_message],
            "verification_suggestions": {},
        }
