"""Custom exceptions used across backend modules."""

from openai import (
    APIError as OpenAIAPIError,
    APITimeoutError as OpenAITimeoutError,
    RateLimitError as OpenAIRateLimitError,
)
from pydantic import ValidationError as PydanticValidationError



class AgentValidationError(Exception):
    """Raised when agent result validation fails."""


class ImageProcessingError(Exception):
    """Raised when image processing fails."""


__all__ = [
    "AgentValidationError",
    "StructuredOutputError",
    "ImageProcessingError",
    "OpenAIAPIError",
    "OpenAITimeoutError",
    "OpenAIRateLimitError",
    "PydanticValidationError",
]


class StructuredOutputError(ValueError):
    """The model reply could not be turned into a valid structured result (retryable)."""
