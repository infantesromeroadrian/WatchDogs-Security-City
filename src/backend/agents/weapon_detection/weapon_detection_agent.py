"""
Weapon/Threat Detection Agent for military-grade threat intelligence.

Military Intelligence Analysis including:
- Firearm identification (type, caliber, condition, status)
- Bladed and improvised weapon detection
- Explosive device indicators (IED, bomb-making materials)
- Military equipment (missiles, launchers, artillery, defense systems)
- Chemical/biological threat indicators
- Threat level assessment and escalation analysis
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
from ...models.agent_results import WeaponDetectionResult
from ...utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ...utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ...utils.metrics_utils import _noop_decorator, track_agent_metrics
from ...utils.retry_utils import agent_retry
from ...utils.timeout_utils import with_timeout
from .prompts import WEAPON_DETECTION_PROMPT
from .response_parser import WeaponDetectionResponseParser

logger = logging.getLogger(__name__)


class WeaponDetectionAgent:
    """
    Agent specialized in military-grade weapon and threat detection.

    Capabilities:
    - Firearm identification (type, caliber, condition)
    - Bladed weapon and improvised weapon detection
    - Explosive device indicators (IED components, bomb-making materials)
    - Military equipment (missiles, launchers, artillery)
    - Chemical/biological threat indicators
    - Threat level assessment and escalation analysis
    """

    def __init__(self) -> None:
        """Initialize Weapon Detection Agent."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0.1,  # Maximum precision for weapon identification
            **({"base_url": OPENAI_BASE_URL} if OPENAI_BASE_URL else {}),
        )

        self.parser = WeaponDetectionResponseParser()

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

        logger.info("🔫 WeaponDetectionAgent initialized (Military Threat Analysis)")

    def _analyze_internal(self, image_base64: str, context: str = "") -> dict[str, Any]:
        """Internal analysis method with weapon detection prompt."""
        logger.info("🔫 Starting military weapon & threat detection...")

        context_section = f"CONTEXTO ADICIONAL: {context}" if context else ""
        prompt = WEAPON_DETECTION_PROMPT.format(context=context_section)

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

        logger.info("✅ Weapon detection & threat analysis complete")

        parsed_data = self.parser.parse(analysis_text)

        return {
            "agent": "weapon_detection",
            "status": "success",
            "analysis": analysis_text,
            "summary": parsed_data.get("summary"),
            "weapons": parsed_data.get("weapons", []),
            "weapon_count": parsed_data.get("weapon_count", 0),
            "explosive_indicators": parsed_data.get("explosive_indicators", []),
            "military_equipment": parsed_data.get("military_equipment", []),
            "threat_assessment": parsed_data.get("threat_assessment", {}),
            "limitations": parsed_data.get("limitations", []),
        }

    @(track_agent_metrics("weapon_detection") if METRICS_ENABLED else _noop_decorator)
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
        Analyze image for weapon and threat detection.

        Args:
            image_base64: Base64 encoded image with data URI
            context: Optional context for analysis

        Returns:
            Dict with weapon intelligence including threat assessment
        """
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "weapon_detection", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached weapon detection result")
                    return cached

            result = self._analyze_with_protection(image_base64, context)

            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "weapon_detection", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)

            try:
                validated = WeaponDetectionResult(**result)
                return validated.model_dump()
            except PydanticValidationError as validation_error:
                logger.warning("⚠️ Result validation failed: %s", validation_error)
                return result

        except TimeoutError as e:
            logger.error("⏱️ Weapon detection timeout: %s", e)
            return self._build_error_result(str(e), status="timeout")

        except (OpenAIRateLimitError, OpenAITimeoutError, OpenAIAPIError) as e:
            logger.error("❌ OpenAI API error in weapon detection: %s", e)
            return self._build_error_result(f"OpenAI API error: {e}")

        except (ValueError, TypeError) as e:
            logger.error("❌ Invalid input to weapon detection: %s", e)
            return self._build_error_result(f"Invalid input: {e}")

    def _build_error_result(self, error_message: str, status: str = "error") -> dict[str, Any]:
        """Build standardized error result with all required fields."""
        return {
            "agent": "weapon_detection",
            "status": status,
            "error": error_message,
            "analysis": f"Weapon detection failed: {error_message}",
            "summary": None,
            "weapons": [],
            "weapon_count": 0,
            "explosive_indicators": [],
            "military_equipment": [],
            "threat_assessment": {
                "threat_level": None,
                "immediate_threats": None,
                "escalation_risk": None,
            },
            "limitations": [error_message],
        }
