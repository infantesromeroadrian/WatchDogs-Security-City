"""
Multi-Monitor Layout Agent Module - Military Intelligence Block 3

This module provides command center display optimization including:
- Scene complexity assessment for display configuration
- Multi-monitor layout recommendations
- Information density analysis and panel prioritization
- Alert priority classification
- Zoom area and declutter suggestions
"""

from .multi_monitor_agent import MultiMonitorAgent
from .prompts import MULTI_MONITOR_PROMPT
from .response_parser import MultiMonitorResponseParser

__all__ = [
    "MULTI_MONITOR_PROMPT",
    "MultiMonitorAgent",
    "MultiMonitorResponseParser",
]
