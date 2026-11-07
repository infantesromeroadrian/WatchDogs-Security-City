"""
Vision-LLM provider abstraction.

All providers are reached through the OpenAI-compatible chat API, so a single
client class covers OpenAI, Groq and Ollama. The provider only selects the
default endpoint and model; ``OPENAI_BASE_URL`` / ``OPENAI_MODEL`` /
``OPENAI_API_KEY`` still override each piece individually.

    LLM_PROVIDER=groq    -> https://api.groq.com/openai/v1
    LLM_PROVIDER=openai  -> https://api.openai.com/v1
    LLM_PROVIDER=ollama  -> http://localhost:11434/v1   (local, no key)
    LLM_PROVIDER=custom  -> OPENAI_BASE_URL is mandatory
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from openai import LengthFinishReasonError

from .. import config
from ..exceptions import StructuredOutputError

logger = logging.getLogger(__name__)

# provider -> (base_url, default model). The default model is documented in README.
PROVIDER_PRESETS: dict[str, tuple[str | None, str]] = {
    "groq": ("https://api.groq.com/openai/v1", "meta-llama/llama-4-scout-17b-16e-instruct"),
    "openai": (None, "gpt-4.1-mini"),
    "ollama": ("http://localhost:11434/v1", "qwen3-vl:8b-instruct"),
    "custom": (None, "gpt-4.1-mini"),
}


@dataclass(frozen=True)
class ProviderSettings:
    """Resolved connection settings for the vision LLM."""

    provider: str
    base_url: str | None
    model: str
    api_key: str
    timeout_seconds: float
    max_tokens: int


def get_provider_settings() -> ProviderSettings:
    """Resolve settings from configuration (env overrides win over presets)."""
    provider = config.LLM_PROVIDER
    if provider not in PROVIDER_PRESETS:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Use one of: {', '.join(PROVIDER_PRESETS)}"
        )
    preset_url, preset_model = PROVIDER_PRESETS[provider]
    base_url = config.OPENAI_BASE_URL or preset_url
    if provider == "custom" and not base_url:
        raise ValueError("LLM_PROVIDER=custom requires OPENAI_BASE_URL")
    # The client refuses an empty key; use a placeholder so the app can start and
    # /api/health reports "degraded" instead of crashing at import time.
    api_key = config.OPENAI_API_KEY or ("ollama" if provider == "ollama" else "unset")
    return ProviderSettings(
        provider=provider,
        base_url=base_url,
        model=config.OPENAI_MODEL or preset_model,
        api_key=api_key,
        timeout_seconds=config.LLM_TIMEOUT_SECONDS,
        max_tokens=config.OPENAI_MAX_TOKENS,
    )


# Process-wide cap on in-flight LLM requests: 16 agents x N frames would otherwise hit
# provider rate limits (and the 0.1 CPU Render plan) all at once.
_LLM_SLOTS = threading.BoundedSemaphore(config.LLM_MAX_CONCURRENCY)


_usage_lock = threading.Lock()
_usage = {"calls": 0, "input_tokens": 0, "output_tokens": 0}


def get_usage_totals(reset: bool = False) -> dict[str, int]:
    """Cumulative LLM usage of this process (used by the evaluation harness for cost)."""
    with _usage_lock:
        snapshot = dict(_usage)
        if reset:
            for key in _usage:
                _usage[key] = 0
    return snapshot


def _record_usage(response: Any) -> None:
    meta = getattr(response, "usage_metadata", None)
    if not isinstance(meta, dict):
        meta = {}
    with _usage_lock:
        _usage["calls"] += 1
        _usage["input_tokens"] += int(meta.get("input_tokens") or 0)
        _usage["output_tokens"] += int(meta.get("output_tokens") or 0)


class _GuardedChat:
    """Wraps a chat model: bounded concurrency and, optionally, a JSON-schema directive.

    Agents keep calling ``llm.invoke([HumanMessage(...)])``. When ``instructions`` is
    set, they are appended to the text part of the human message (JSON mode is
    enabled on the underlying client).
    """

    def __init__(self, llm: ChatOpenAI, instructions: str | None = None) -> None:
        self._llm = llm
        self._instructions = instructions

    def __getattr__(self, name: str) -> Any:
        return getattr(self._llm, name)

    def invoke(self, messages: Any, **kwargs: Any) -> Any:
        if self._instructions and isinstance(messages, list):
            messages = [self._patch(m) for m in messages]
        # Hard stop before spending provider quota (also covers retries and background paths)
        from ..services.llm_budget import current_principal, get_budget

        get_budget().reserve(1, current_principal.get())
        try:
            with _LLM_SLOTS:
                response = self._llm.invoke(messages, **kwargs)
        except LengthFinishReasonError as exc:
            # The model hit the output cap mid-JSON (typically a repetition loop). The openai client
            # raises a non-APIError exception that no agent handles; treat it as an unparsable reply
            # so the retry layer gets one more attempt and the agent then reports an error result.
            raise StructuredOutputError("model output truncated at the token cap") from exc
        _record_usage(response)
        return response

    def _patch(self, message: BaseMessage) -> BaseMessage:
        if not self._instructions or not isinstance(message, HumanMessage) or not isinstance(message.content, list):
            return message
        parts = []
        done = False
        for part in message.content:
            if not done and isinstance(part, dict) and part.get("type") == "text":
                part = {**part, "text": f"{part['text']}\n\n{self._instructions}"}
                done = True
            parts.append(part)
        return HumanMessage(content=parts)


def build_chat_model(
    temperature: float | None = None,
    schema: type | None = None,
) -> Any:
    """Build the chat model for an agent.

    Args:
        temperature: Sampling temperature (defaults to OPENAI_TEMPERATURE).
        schema: Optional pydantic model. When given, the model is asked for a
            JSON object conforming to it (JSON mode + schema instructions).
    """
    s = get_provider_settings()
    kwargs: dict[str, Any] = {
        "model": s.model,
        "api_key": s.api_key,
        "temperature": config.OPENAI_TEMPERATURE if temperature is None else temperature,
        "timeout": s.timeout_seconds,  # real HTTP timeout: cancels the socket, unlike a thread timeout
        "max_retries": 0,  # retries are handled once, by agent_retry (tenacity)
    }
    # Output cap. langchain-openai sends ``max_tokens`` as ``max_completion_tokens``, which OpenAI
    # accepts but Ollama and many OpenAI-compatible servers silently IGNORE (a looping 8B model then
    # generated until the context was full: measured 5 688 tokens against a 4 096 cap). So only the
    # OpenAI API gets the modern field; everything else gets the classic ``max_tokens``.
    model_kwargs: dict[str, Any] = {}
    if s.provider == "openai":
        kwargs["max_tokens"] = s.max_tokens
    else:
        kwargs["extra_body"] = {"max_tokens": s.max_tokens}  # merged raw into the request JSON
    if s.base_url:
        kwargs["base_url"] = s.base_url
    if schema is not None:
        model_kwargs["response_format"] = {"type": "json_object"}
    if model_kwargs:
        kwargs["model_kwargs"] = model_kwargs
    llm = ChatOpenAI(**kwargs)
    if schema is None:
        return _GuardedChat(llm)
    from .structured import format_instructions

    return _GuardedChat(llm, format_instructions(schema))


def message_text(content: Any) -> str:
    """Normalise LangChain message content (str or list of parts) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            item.get("text", str(item)) if isinstance(item, dict) else str(item)
            for item in content
        )
    return str(content)
