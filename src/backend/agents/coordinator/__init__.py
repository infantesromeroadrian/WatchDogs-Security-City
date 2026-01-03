"""
Coordinator Module - Clean Architecture
Refactored into modular components following SOLID principles
"""

from .coordinator import CoordinatorAgent
from .state import AnalysisState

__all__ = ["CoordinatorAgent", "AnalysisState"]
