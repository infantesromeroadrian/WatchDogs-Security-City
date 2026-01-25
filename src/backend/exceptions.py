"""
Custom exceptions for WatchDogs Security City.
Provides specific exception types for better error handling and debugging.
"""


# ============================================================================
# Base Exceptions
# ============================================================================
class WatchDogsError(Exception):
    """Base exception for all WatchDogs-specific errors."""


# ============================================================================
# Agent Exceptions
# ============================================================================
class AgentError(WatchDogsError):
    """Base exception for agent-related errors."""


class AgentTimeoutError(AgentError):
    """Raised when an agent operation times out."""


class AgentValidationError(AgentError):
    """Raised when agent result validation fails."""


class CircuitBreakerError(AgentError):
    """Raised when circuit breaker is open."""


# ============================================================================
# Service Exceptions
# ============================================================================
class ServiceError(WatchDogsError):
    """Base exception for service-related errors."""


class ImageProcessingError(ServiceError):
    """Raised when image processing fails."""


class VideoProcessingError(ServiceError):
    """Raised when video processing fails."""


class MetadataExtractionError(ServiceError):
    """Raised when metadata extraction fails."""


class GeolocationError(ServiceError):
    """Raised when geolocation processing fails."""


# ============================================================================
# API Exceptions
# ============================================================================
class APIError(WatchDogsError):
    """Base exception for API-related errors."""


class InvalidRequestError(APIError):
    """Raised when request validation fails."""


class AuthenticationError(APIError):
    """Raised when authentication fails."""


class RateLimitExceededError(APIError):
    """Raised when rate limit is exceeded."""


class AuthorizationError(APIError):
    """Raised when user lacks required permissions."""


# ============================================================================
# External API Exceptions (re-exported for convenience)
# ============================================================================
# These are re-exported here so imports are consistent
from openai import (
    APIError as OpenAIAPIError,
    APITimeoutError as OpenAITimeoutError,
    RateLimitError as OpenAIRateLimitError,
)
from pydantic import ValidationError as PydanticValidationError

__all__ = [
    # Base
    "WatchDogsError",
    # Agent
    "AgentError",
    "AgentTimeoutError",
    "AgentValidationError",
    "CircuitBreakerError",
    # Service
    "ServiceError",
    "ImageProcessingError",
    "VideoProcessingError",
    "MetadataExtractionError",
    "GeolocationError",
    # API
    "APIError",
    "InvalidRequestError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitExceededError",
    # External (re-exported)
    "OpenAIAPIError",
    "OpenAITimeoutError",
    "OpenAIRateLimitError",
    "PydanticValidationError",
]
