"""
NATO APP-6 Symbology Response Parser

Parses structured NATO symbology intelligence from LLM responses including:
- Identified entities with SIDC codes and affiliations
- Force composition counts (friendly/hostile/neutral/unknown)
- Operational environment (domain, weather impact, terrain)
- Recommended tactical graphic overlays
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class NATOSymbologyResponseParser:
    """Parse structured NATO APP-6D symbology intelligence from LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract NATO symbology intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed NATO symbology data
        """
        return {
            "summary": self._parse_summary(text),
            "identified_entities": self._parse_entities(text),
            "force_composition": self._parse_force_composition(text),
            "operational_environment": self._parse_operational_environment(text),
            "tactical_graphics": self._parse_tactical_graphics(text),
            "limitations": self._parse_limitations(text),
        }

    def _parse_summary(self, text: str) -> str | None:
        """Extract NATO symbology summary."""
        match = re.search(
            r"RESUMEN\s*SIMBOLOG[ÍI]A:\s*\n?(.*?)(?=\n\n|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            summary = match.group(1).strip()
            summary = re.sub(r"^\[|\]$", "", summary).strip()
            return summary if summary else None
        return None

    def _parse_entities(self, text: str) -> list[dict[str, Any]]:
        """Extract identified entities with SIDC codes."""
        section_match = re.search(
            r"ENTIDADES\s*IDENTIFICADAS:\s*(.*?)(?=###|COMPOSICI[ÓO]N|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)

        entities = []
        for item in items[:20]:
            item = item.strip()
            if not item:
                continue

            entity: dict[str, Any] = {
                "description": item,
                "sidc": None,
                "affiliation": None,
                "dimension": None,
                "function_id": None,
                "confidence": None,
            }

            # Extract SIDC code
            sidc_match = re.search(r"SIDC:\s*\[?([A-Z0-9\-]+)\]?", item, re.IGNORECASE)
            if sidc_match:
                entity["sidc"] = sidc_match.group(1).strip()

            # Extract affiliation
            affil_match = re.search(
                r"Afiliaci[óo]n:\s*\[?(FRIEND|HOSTILE|NEUTRAL|UNKNOWN|"
                r"AMIGO|HOSTIL|NEUTRAL|DESCONOCIDO|[^\]\|]+)\]?",
                item,
                re.IGNORECASE,
            )
            if affil_match:
                entity["affiliation"] = affil_match.group(1).strip().upper()

            # Extract dimension
            dim_match = re.search(
                r"Dimensi[óo]n:\s*\[?(tierra|aire|mar|espacio|subsuperficie|[^\]\|]+)\]?",
                item,
                re.IGNORECASE,
            )
            if dim_match:
                entity["dimension"] = dim_match.group(1).strip()

            # Extract function
            func_match = re.search(
                r"Funci[óo]n:\s*\[?([^\]\|]+)\]?",
                item,
                re.IGNORECASE,
            )
            if func_match:
                entity["function_id"] = func_match.group(1).strip()

            # Extract confidence
            conf_match = re.search(
                r"Confianza:\s*\[?(Alta|Media|Baja|[^\]\|]+)\]?",
                item,
                re.IGNORECASE,
            )
            if conf_match:
                entity["confidence"] = conf_match.group(1).strip()

            # Clean description to just the entity name
            desc_match = re.search(r"^(?:Entidad\s*\d+:\s*)?\[?([^\]\|]+)", item)
            if desc_match:
                clean_desc = desc_match.group(1).strip()
                if clean_desc:
                    entity["description"] = clean_desc

            entities.append(entity)

        return entities

    def _parse_force_composition(self, text: str) -> dict[str, Any]:
        """Extract force composition counts."""
        composition: dict[str, Any] = {
            "friendly": 0,
            "hostile": 0,
            "neutral": 0,
            "unknown": 0,
        }

        section_match = re.search(
            r"COMPOSICI[ÓO]N\s*DE\s*FUERZAS:\s*(.*?)(?=###|ENTORNO|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return composition

        section = section_match.group(1)

        # Friendly
        friend_match = re.search(
            r"(?:Amigos?|FRIEND)\s*\(?(?:FRIEND)?\)?:\*\*\s*\[?(\d+|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if friend_match:
            try:
                composition["friendly"] = int(friend_match.group(1).strip())
            except ValueError:
                pass

        # Hostile
        hostile_match = re.search(
            r"(?:Hostiles?|HOSTILE)\s*\(?(?:HOSTILE)?\)?:\*\*\s*\[?(\d+|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if hostile_match:
            try:
                composition["hostile"] = int(hostile_match.group(1).strip())
            except ValueError:
                pass

        # Neutral
        neutral_match = re.search(
            r"(?:Neutrales?|NEUTRAL)\s*\(?(?:NEUTRAL)?\)?:\*\*\s*\[?(\d+|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if neutral_match:
            try:
                composition["neutral"] = int(neutral_match.group(1).strip())
            except ValueError:
                pass

        # Unknown
        unknown_match = re.search(
            r"(?:Desconocidos?|UNKNOWN)\s*\(?(?:UNKNOWN)?\)?:\*\*\s*\[?(\d+|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if unknown_match:
            try:
                composition["unknown"] = int(unknown_match.group(1).strip())
            except ValueError:
                pass

        return composition

    def _parse_operational_environment(self, text: str) -> dict[str, Any]:
        """Extract operational environment assessment."""
        env: dict[str, Any] = {
            "domain": None,
            "weather_impact": None,
            "terrain_classification": None,
        }

        section_match = re.search(
            r"ENTORNO\s*OPERACIONAL:\s*(.*?)(?=###|GR[ÁA]FICOS|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return env

        section = section_match.group(1)

        # Domain
        domain_match = re.search(
            r"Dominio:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if domain_match:
            env["domain"] = domain_match.group(1).strip()

        # Weather impact
        weather_match = re.search(
            r"Impacto\s*meteorol[óo]gico:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if weather_match:
            env["weather_impact"] = weather_match.group(1).strip()

        # Terrain
        terrain_match = re.search(
            r"Clasificaci[óo]n\s*de\s*terreno:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if terrain_match:
            env["terrain_classification"] = terrain_match.group(1).strip()

        return env

    def _parse_tactical_graphics(self, text: str) -> list[str]:
        """Extract recommended tactical graphic overlays."""
        section_match = re.search(
            r"GR[ÁA]FICOS\s*T[ÁA]CTICOS:\s*(.*?)(?=###|LIMITACIONES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:10]

    def _parse_limitations(self, text: str) -> list[str]:
        """Extract analysis limitations."""
        section_match = re.search(
            r"LIMITACIONES:\s*(.*?)(?=###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()][:10]
