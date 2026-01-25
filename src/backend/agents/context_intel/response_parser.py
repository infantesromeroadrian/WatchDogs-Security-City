"""
Context Intelligence Response Parser - Temporal and Cultural Inference

Parses structured contextual intelligence from LLM responses including:
- Temporal analysis (time, day, season, era)
- Cultural and socioeconomic indicators
- Event classification
- Environmental conditions
- Key inferences with confidence levels
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class ContextIntelResponseParser:
    """Parse structured contextual intelligence data from LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract comprehensive contextual intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed contextual intelligence data
        """
        return {
            "executive_summary": self._parse_executive_summary(text),
            "temporal_analysis": self._parse_temporal_analysis(text),
            "sociocultural_analysis": self._parse_sociocultural_analysis(text),
            "event_classification": self._parse_event_classification(text),
            "environmental_conditions": self._parse_environmental_conditions(text),
            "anomalies": self._parse_anomalies(text),
            "key_inferences": self._parse_key_inferences(text),
            "limitations": self._parse_limitations(text),
            "open_questions": self._parse_open_questions(text),
        }

    # =========================================================================
    # EXECUTIVE SUMMARY
    # =========================================================================

    def _parse_executive_summary(self, text: str) -> str | None:
        """Extract executive summary."""
        match = re.search(
            r"RESUMEN\s*EJECUTIVO:\s*\n?(.*?)(?=\n\n|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            summary = match.group(1).strip()
            # Clean up brackets if present
            summary = re.sub(r"^\[|\]$", "", summary).strip()
            return summary if summary else None
        return None

    # =========================================================================
    # TEMPORAL ANALYSIS
    # =========================================================================

    def _parse_temporal_analysis(self, text: str) -> dict[str, Any]:
        """Extract temporal analysis data."""
        temporal: dict[str, Any] = {
            "time_of_day": self._extract_temporal_item(text, "Hora estimada"),
            "day_type": self._extract_temporal_item(text, "Día de la semana"),
            "season": self._extract_temporal_item(text, "Estación"),
            "era": self._extract_temporal_item(text, "Época/Era"),
            "specific_date": self._extract_temporal_item(text, "Fecha específica"),
        }
        return temporal

    def _extract_temporal_item(self, text: str, field_name: str) -> dict[str, Any]:
        """Extract a temporal analysis item with value, confidence, and evidence."""
        item: dict[str, Any] = {
            "value": None,
            "confidence": None,
            "evidence": [],
        }

        # Pattern: **Field:** [Value] - Confianza: [Level]
        pattern = rf"\*\*{field_name}:\*\*\s*\[?([^\]\n-]+)\]?\s*(?:-\s*Confianza:\s*\[?(Alta|Media|Baja)\]?)?"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            item["value"] = match.group(1).strip()
            if match.group(2):
                item["confidence"] = match.group(2).strip().lower()

        # Extract evidence
        evidence_pattern = rf"{field_name}.*?(?:\n-\s*Evidencia:\s*(.*?)(?=\n\n|\*\*|###|$))"
        evidence_match = re.search(evidence_pattern, text, re.IGNORECASE | re.DOTALL)
        if evidence_match:
            evidence_text = evidence_match.group(1)
            items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", evidence_text)
            if items:
                item["evidence"] = [e.strip() for e in items if e.strip()]
            elif evidence_text.strip():
                # Single line evidence
                item["evidence"] = [evidence_text.strip()]

        return item

    # =========================================================================
    # SOCIOCULTURAL ANALYSIS
    # =========================================================================

    def _parse_sociocultural_analysis(self, text: str) -> dict[str, Any]:
        """Extract sociocultural analysis data."""
        socio: dict[str, Any] = {
            "socioeconomic_level": None,
            "socioeconomic_indicators": [],
            "cultural_context": None,
            "cultural_indicators": [],
            "political_situation": None,
            "political_indicators": [],
        }

        # Socioeconomic level
        socio_match = re.search(
            r"Nivel\s*socioeconómico[^:]*:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if socio_match:
            socio["socioeconomic_level"] = socio_match.group(1).strip()

        # Socioeconomic indicators
        socio["socioeconomic_indicators"] = self._extract_indicators(
            text, r"Nivel\s*socioeconómico.*?Indicadores:\s*(.*?)(?=\n\n|\*\*|###|$)"
        )

        # Cultural context
        cultural_match = re.search(
            r"Contexto\s*cultural:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if cultural_match:
            socio["cultural_context"] = cultural_match.group(1).strip()

        # Cultural indicators
        socio["cultural_indicators"] = self._extract_indicators(
            text, r"Contexto\s*cultural.*?Indicadores:\s*(.*?)(?=\n\n|\*\*|###|$)"
        )

        # Political situation
        political_match = re.search(
            r"Situación\s*política[^:]*:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if political_match:
            socio["political_situation"] = political_match.group(1).strip()

        return socio

    def _extract_indicators(self, text: str, pattern: str) -> list[str]:
        """Extract list of indicators from a section."""
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not match:
            return []

        indicators_text = match.group(1)
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", indicators_text)

        if not items:
            # Try comma-separated or single line
            items = [i.strip() for i in indicators_text.split(",") if i.strip()]

        return [i.strip() for i in items if i.strip()][:10]

    # =========================================================================
    # EVENT CLASSIFICATION
    # =========================================================================

    def _parse_event_classification(self, text: str) -> dict[str, Any]:
        """Extract event classification data."""
        event: dict[str, Any] = {
            "event_type": None,
            "event_subtype": None,
            "primary_purpose": None,
            "social_dynamics": None,
        }

        # Event type
        type_match = re.search(
            r"Tipo\s*de\s*evento:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if type_match:
            event["event_type"] = type_match.group(1).strip()

        # Subtype
        subtype_match = re.search(
            r"Subtipo:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if subtype_match:
            event["event_subtype"] = subtype_match.group(1).strip()

        # Purpose
        purpose_match = re.search(
            r"Propósito\s*principal:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if purpose_match:
            event["primary_purpose"] = purpose_match.group(1).strip()

        # Social dynamics
        dynamics_match = re.search(
            r"Dinámica\s*social:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if dynamics_match:
            event["social_dynamics"] = dynamics_match.group(1).strip()

        return event

    # =========================================================================
    # ENVIRONMENTAL CONDITIONS
    # =========================================================================

    def _parse_environmental_conditions(self, text: str) -> dict[str, Any]:
        """Extract environmental and weather conditions."""
        env: dict[str, Any] = {
            "weather": None,
            "temperature": None,
            "special_conditions": None,
        }

        # Weather/Climate
        weather_match = re.search(
            r"Clima:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if weather_match:
            env["weather"] = weather_match.group(1).strip()

        # Temperature
        temp_match = re.search(
            r"Temperatura\s*aparente:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if temp_match:
            env["temperature"] = temp_match.group(1).strip()

        # Special conditions
        special_match = re.search(
            r"Condiciones\s*especiales:\*\*\s*\[?([^\]\n]+)\]?",
            text,
            re.IGNORECASE,
        )
        if special_match:
            value = special_match.group(1).strip()
            if value.lower() not in ["ninguna", "ninguno", "n/a", "-"]:
                env["special_conditions"] = value

        return env

    # =========================================================================
    # ANOMALIES
    # =========================================================================

    def _parse_anomalies(self, text: str) -> list[str]:
        """Extract anomalies and elements of interest."""
        section_match = re.search(
            r"ANOMALÍAS\s*Y\s*ELEMENTOS\s*DE\s*INTERÉS:\s*(.*?)(?=###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)

        # Check for "none" patterns
        if re.search(r"ninguna|ninguno|no\s+se\s+detectan", section_text, re.IGNORECASE):
            return []

        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:10]

    # =========================================================================
    # KEY INFERENCES
    # =========================================================================

    def _parse_key_inferences(self, text: str) -> list[dict[str, Any]]:
        """Extract key inferences with confidence levels."""
        inferences: list[dict[str, Any]] = []

        section_match = re.search(
            r"INFERENCIAS\s*CLAVE:\s*(.*?)(?=###|LIMITACIONES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return inferences

        section_text = section_match.group(1)

        # Pattern: 1. [Inference] - Confianza: [%]
        pattern = re.compile(
            r"(\d+)\.\s*\[?(.+?)\]?\s*-\s*Confianza:\s*\[?(\d+)%?\]?",
            re.IGNORECASE,
        )

        for match in pattern.finditer(section_text):
            inferences.append(
                {
                    "order": int(match.group(1)),
                    "inference": match.group(2).strip(),
                    "confidence_percent": int(match.group(3)),
                }
            )

        # Sort by order
        inferences.sort(key=lambda x: x.get("order", 0))

        return inferences

    # =========================================================================
    # LIMITATIONS
    # =========================================================================

    def _parse_limitations(self, text: str) -> list[str]:
        """Extract analysis limitations."""
        section_match = re.search(
            r"LIMITACIONES\s*DEL\s*ANÁLISIS:\s*(.*?)(?=###|PREGUNTAS|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)

        return [item.strip() for item in items if item.strip()][:10]

    # =========================================================================
    # OPEN QUESTIONS
    # =========================================================================

    def _parse_open_questions(self, text: str) -> list[str]:
        """Extract open questions that couldn't be answered."""
        section_match = re.search(
            r"PREGUNTAS\s*ABIERTAS:\s*(.*?)(?=━|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)

        return [item.strip() for item in items if item.strip()][:10]
