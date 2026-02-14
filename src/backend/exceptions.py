"""Custom exceptions used across backend modules."""


class AgentValidationError(Exception):
    """Raised when agent result validation fails."""


class ImageProcessingError(Exception):
    """Raised when image processing fails."""


from openai import (
    APIError as OpenAIAPIError,
    APITimeoutError as OpenAITimeoutError,
    RateLimitError as OpenAIRateLimitError,
)
from pydantic import ValidationError as PydanticValidationError

__all__ = [
    "AgentValidationError",
    "ImageProcessingError",
    "OpenAIAPIError",
    "OpenAITimeoutError",
    "OpenAIRateLimitError",
    "PydanticValidationError",
]
