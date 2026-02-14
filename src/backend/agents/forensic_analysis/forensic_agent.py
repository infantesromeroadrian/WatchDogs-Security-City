"""
Forensic Analysis Agent for image authenticity verification using GPT-5.1.

CIA-Level OSINT Analysis including:
- Manipulation detection (copy-paste, splicing, retouching)
- Compression artifact analysis
- Lighting and shadow consistency
- Perspective and geometry verification
- AI-generated content detection
- Digital fingerprint analysis
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
from ...models.agent_results import ForensicAnalysisResult
from ...utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ...utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ...utils.metrics_utils import _noop_decorator, track_agent_metrics
from ...utils.retry_utils import agent_retry
from ...utils.timeout_utils import with_timeout
from .prompts import FORENSIC_ANALYSIS_PROMPT
from .response_parser import ForensicResponseParser

logger = logging.getLogger(__name__)


class ForensicAnalysisAgent:
    """
    Agent specialized in CIA-level image forensic analysis and authenticity verification.

    Uses forensic-level analysis techniques including:
    - JPEG compression artifact analysis
    - Lighting and shadow consistency checking
    - Perspective and geometric analysis
    - Color and tonality verification
    - Copy-paste / splicing detection
    - AI-generated content identification
    - Re-compression trace detection
    """

    def __init__(self) -> None:
        """Initialize Forensic Analysis Agent with GPT-5.1 model."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.1,  # Very low temperature for objective forensic analysis
            **({"base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
        )

        # Initialize response parser
        self.parser = ForensicResponseParser()

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

        logger.info("🔬 ForensicAnalysisAgent initialized (CIA-level image forensics)")

    def _analyze_internal(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """
        Internal analysis method with forensic-level prompt.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with comprehensive forensic intelligence
        """
        logger.info("🔬 Starting CIA-level forensic image analysis...")

        # Format prompt with context
        context_section = f"CONTEXTO ADICIONAL: {context}" if context else ""
        prompt = FORENSIC_ANALYSIS_PROMPT.format(context=context_section)

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

        logger.info("✅ Forensic analysis complete")

        # Parse response using enhanced parser
        parsed_data = self.parser.parse(analysis_text)

        # Build comprehensive result
        return {
            "agent": "forensic_analysis",
            "status": "success",
            "analysis": analysis_text,
            # Verdict
            "verdict": parsed_data.get("verdict", {}),
            "integrity_score": parsed_data.get("integrity_score"),
            # Anomalies by category
            "anomalies": parsed_data.get("anomalies", {}),
            # Detection details
            "suspicious_regions": parsed_data.get("suspicious_regions", []),
            "evidence_chain": parsed_data.get("evidence_chain", []),
            "manipulation_hypothesis": parsed_data.get("manipulation_hypothesis"),
            # Quality assessment
            "image_quality": parsed_data.get("image_quality", {}),
            # Follow-up
            "recommendations": parsed_data.get("recommendations", []),
        }

    @(track_agent_metrics("forensic_analysis") if METRICS_ENABLED else _noop_decorator)
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
        Analyze image for authenticity and manipulation detection.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with comprehensive forensic analysis including:
            - Authenticity verdict with confidence
            - Integrity score (0-100)
            - Detected anomalies by category
            - Suspicious regions
            - Evidence chain
            - Manipulation hypothesis
            - Recommendations for verification
        """
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "forensic_analysis", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached forensic analysis result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "forensic_analysis", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = ForensicAnalysisResult(**result)
                return validated.model_dump()
            except PydanticValidationError as validation_error:
                logger.warning("⚠️ Result validation failed: %s", validation_error)
                return result

        except TimeoutError as e:
            logger.error("⏱️ Forensic analysis timeout: %s", e)
            return self._build_error_result(str(e), status="timeout")

        except (OpenAIRateLimitError, OpenAITimeoutError, OpenAIAPIError) as e:
            logger.error("❌ OpenAI API error in forensic analysis: %s", e)
            return self._build_error_result(f"OpenAI API error: {e}")

        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid input to forensic analysis: %s", e)
            return self._build_error_result(f"Invalid input: {e}")

    def _build_error_result(self, error_message: str, status: str = "error") -> dict[str, Any]:
        """Build standardized error result with all required fields."""
        return {
            "agent": "forensic_analysis",
            "status": status,
            "error": error_message,
            "analysis": f"Forensic analysis failed: {error_message}",
            "verdict": {
                "classification": "indeterminada",
                "confidence": "muy baja",
                "justification": f"Error: {error_message}",
            },
            "integrity_score": None,
            "anomalies": {
                "compression_artifacts": [],
                "lighting_shadows": [],
                "perspective_geometry": [],
                "color_tonality": [],
                "manipulation_specific": {
                    "copy_paste": {"detected": False, "details": None},
                    "splicing": {"detected": False, "details": None},
                    "retouching": {"detected": False, "details": None},
                    "ai_generated": {"detected": False, "details": None},
                },
                "semantic_content": [],
            },
            "suspicious_regions": [],
            "evidence_chain": [],
            "manipulation_hypothesis": None,
            "image_quality": {
                "resolution": None,
                "compression": None,
                "limiting_factors": [error_message],
            },
            "recommendations": [],
        }
