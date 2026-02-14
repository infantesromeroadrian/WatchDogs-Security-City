"""
Face Analysis Agent for detailed person identification using GPT-5.1.

CIA-Level OSINT Analysis including:
- Detailed facial feature extraction
- Body characteristics and posture
- Clothing and accessories identification
- Distinguishing marks (scars, tattoos, birthmarks)
- Age, gender, and ethnicity estimation
- Behavioral context analysis
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
from ...models.agent_results import FaceAnalysisResult
from ...utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ...utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ...utils.metrics_utils import _noop_decorator, track_agent_metrics
from ...utils.retry_utils import agent_retry
from ...utils.timeout_utils import with_timeout
from .prompts import FACE_ANALYSIS_PROMPT
from .response_parser import FaceAnalysisResponseParser

logger = logging.getLogger(__name__)


class FaceAnalysisAgent:
    """
    Agent specialized in CIA-level person identification from visual analysis.

    Uses forensic-level analysis techniques including:
    - Comprehensive facial feature mapping
    - Distinctive mark cataloging (scars, tattoos, piercings)
    - Clothing and accessory documentation
    - Behavioral and contextual analysis
    - Multi-person detection and tracking
    """

    def __init__(self) -> None:
        """Initialize Face Analysis Agent with GPT-5.1 model."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.2,  # Low temperature for precise descriptions
            **({"base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
        )

        # Initialize response parser
        self.parser = FaceAnalysisResponseParser()

        # Initialize circuit breaker
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

        logger.info("ℹ️ FaceAnalysisAgent initialized (CIA-level OSINT)")

    def _analyze_internal(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """
        Internal analysis method with forensic-level prompt.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with comprehensive person intelligence
        """
        logger.info("ℹ️ Starting CIA-level face/person analysis...")

        # Format prompt with context
        context_section = f"CONTEXTO ADICIONAL: {context}" if context else ""
        prompt = FACE_ANALYSIS_PROMPT.format(context=context_section)

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

        logger.info("✅ Face/person analysis complete")

        # Parse response using enhanced parser
        parsed_data = self.parser.parse(analysis_text)

        # Build comprehensive result
        return {
            "agent": "face_analysis",
            "status": "success",
            "analysis": analysis_text,
            # Detection summary
            "detection_summary": parsed_data.get("detection_summary", {}),
            # Per-person data
            "persons": parsed_data.get("persons", []),
            "person_count": len(parsed_data.get("persons", [])),
            # Identification aids
            "most_distinctive_features": parsed_data.get("most_distinctive_features", []),
            # Metadata
            "limitations": parsed_data.get("limitations", []),
        }

    @(track_agent_metrics("face_analysis") if METRICS_ENABLED else _noop_decorator)
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
        Analyze image for person identification using forensic-level OSINT techniques.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with comprehensive person analysis including:
            - Detection summary (counts, quality)
            - Per-person detailed descriptors
            - Distinctive features for identification
            - Analysis limitations
        """
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "face_analysis", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached face analysis result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "face_analysis", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = FaceAnalysisResult(**result)
                return validated.model_dump()
            except PydanticValidationError as validation_error:
                logger.warning("⚠️ Result validation failed: %s", validation_error)
                return result

        except TimeoutError as e:
            logger.error("⏱️ Face analysis timeout: %s", e)
            return self._build_error_result(str(e), status="timeout")

        except (OpenAIRateLimitError, OpenAITimeoutError, OpenAIAPIError) as e:
            logger.error("❌ OpenAI API error in face analysis: %s", e)
            return self._build_error_result(f"OpenAI API error: {e}")

        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid input to face analysis: %s", e)
            return self._build_error_result(f"Invalid input: {e}")

    def _build_error_result(self, error_message: str, status: str = "error") -> dict[str, Any]:
        """Build standardized error result with all required fields."""
        return {
            "agent": "face_analysis",
            "status": status,
            "error": error_message,
            "analysis": f"Face analysis failed: {error_message}",
            "detection_summary": {
                "total_persons": 0,
                "faces_visible": 0,
                "partial_visibility": 0,
                "identification_quality": "unknown",
            },
            "persons": [],
            "person_count": 0,
            "most_distinctive_features": [],
            "limitations": [error_message],
        }
