"""
Multi-Monitor Layout Response Parser

Parses structured command center display intelligence from LLM responses including:
- Scene complexity (level, detail density, priority agents, recommended panels)
- Layout recommendation (monitor count, primary/secondary displays, layout type)
- Information density (critical data points, zoom areas, declutter suggestions)
- Alert priorities (prioritized alerts with panel and action recommendations)
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class MultiMonitorResponseParser:
    """Parse structured multi-monitor layout intelligence from LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract multi-monitor layout intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed multi-monitor layout data
        """
        return {
            "summary": self._parse_summary(text),
            "scene_complexity": self._parse_scene_complexity(text),
            "layout_recommendation": self._parse_layout_recommendation(text),
            "information_density": self._parse_information_density(text),
            "alert_priorities": self._parse_alert_priorities(text),
            "limitations": self._parse_limitations(text),
        }

    def _parse_summary(self, text: str) -> str | None:
        """Extract layout recommendation summary."""
        match = re.search(
            r"RESUMEN\s*LAYOUT:\s*\n?(.*?)(?=\n\n|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            summary = match.group(1).strip()
            summary = re.sub(r"^\[|\]$", "", summary).strip()
            return summary if summary else None
        return None

    def _parse_scene_complexity(self, text: str) -> dict[str, Any]:
        """Extract scene complexity assessment."""
        complexity: dict[str, Any] = {
            "level": None,
            "detail_density": None,
            "priority_agents": [],
            "recommended_panels": None,
        }

        section_match = re.search(
            r"COMPLEJIDAD\s*DE\s*ESCENA:\s*(.*?)(?=###|RECOMENDACI[ÓO]N|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return complexity

        section = section_match.group(1)

        # Level
        level_match = re.search(
            r"Nivel:\*\*\s*\[?(LOW|MEDIUM|HIGH|EXTREME|BAJO|MEDIO|ALTO|EXTREMO|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if level_match:
            complexity["level"] = level_match.group(1).strip().upper()

        # Detail density
        density_match = re.search(
            r"Densidad\s*de\s*detalle:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if density_match:
            complexity["detail_density"] = density_match.group(1).strip()

        # Priority agents
        agents_match = re.search(
            r"Agentes\s*prioritarios:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if agents_match:
            value = agents_match.group(1).strip()
            complexity["priority_agents"] = [a.strip() for a in value.split(",") if a.strip()]

        # Recommended panels
        panels_match = re.search(
            r"Paneles\s*recomendados:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if panels_match:
            complexity["recommended_panels"] = panels_match.group(1).strip()

        return complexity

    def _parse_layout_recommendation(self, text: str) -> dict[str, Any]:
        """Extract multi-monitor layout recommendation."""
        layout: dict[str, Any] = {
            "monitor_count": None,
            "primary_display": None,
            "secondary_displays": [],
            "layout_type": None,
        }

        section_match = re.search(
            r"RECOMENDACI[ÓO]N\s*DE\s*LAYOUT:\s*(.*?)(?=###|DENSIDAD|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return layout

        section = section_match.group(1)

        # Monitor count
        count_match = re.search(
            r"Monitores\s*recomendados:\*\*\s*\[?(\d+|[^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if count_match:
            try:
                layout["monitor_count"] = int(count_match.group(1).strip())
            except ValueError:
                layout["monitor_count"] = count_match.group(1).strip()

        # Primary display
        primary_match = re.search(
            r"Display\s*principal:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if primary_match:
            layout["primary_display"] = primary_match.group(1).strip()

        # Secondary displays
        secondary_match = re.search(
            r"Displays?\s*secundarios?:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if secondary_match:
            value = secondary_match.group(1).strip()
            layout["secondary_displays"] = [s.strip() for s in value.split(",") if s.strip()]

        # Layout type
        type_match = re.search(
            r"Tipo\s*de\s*layout:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if type_match:
            layout["layout_type"] = type_match.group(1).strip()

        return layout

    def _parse_information_density(self, text: str) -> dict[str, Any]:
        """Extract information density analysis."""
        density: dict[str, Any] = {
            "critical_data_points": [],
            "recommended_zoom_areas": [],
            "declutter_suggestions": [],
        }

        section_match = re.search(
            r"DENSIDAD\s*DE\s*INFORMACI[ÓO]N:\s*(.*?)(?=###|PRIORIDADES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return density

        section = section_match.group(1)

        # Critical data points
        critical_match = re.search(
            r"Puntos\s*de\s*datos\s*cr[íi]ticos:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if critical_match:
            value = critical_match.group(1).strip()
            density["critical_data_points"] = [p.strip() for p in value.split(",") if p.strip()]

        # Zoom areas
        zoom_match = re.search(
            r"Zonas\s*de\s*zoom\s*recomendadas:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if zoom_match:
            value = zoom_match.group(1).strip()
            density["recommended_zoom_areas"] = [z.strip() for z in value.split(",") if z.strip()]

        # Declutter suggestions
        declutter_match = re.search(
            r"Sugerencias\s*de\s*simplificaci[óo]n:\*\*\s*\[?([^\]\n]+)\]?",
            section,
            re.IGNORECASE,
        )
        if declutter_match:
            value = declutter_match.group(1).strip()
            density["declutter_suggestions"] = [d.strip() for d in value.split(",") if d.strip()]

        return density

    def _parse_alert_priorities(self, text: str) -> list[dict[str, str]]:
        """Extract prioritized alert list."""
        section_match = re.search(
            r"PRIORIDADES\s*DE\s*ALERTA:\s*(.*?)(?=###|LIMITACIONES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)

        alerts = []
        for item in items[:10]:
            item = item.strip()
            if not item:
                continue

            alert: dict[str, str] = {
                "priority": "MEDIUM",
                "description": item,
            }

            # Extract priority
            priority_match = re.search(
                r"\[?(CRITICAL|HIGH|MEDIUM|LOW|CR[ÍI]TICO|ALTO|MEDIO|BAJO)\]?",
                item,
                re.IGNORECASE,
            )
            if priority_match:
                raw = priority_match.group(1).strip().upper()
                # Normalize to English
                if raw in ("CRÍTICO", "CRITICO"):
                    raw = "CRITICAL"
                elif raw == "ALTO":
                    raw = "HIGH"
                elif raw == "MEDIO":
                    raw = "MEDIUM"
                elif raw == "BAJO":
                    raw = "LOW"
                alert["priority"] = raw

            # Extract panel
            panel_match = re.search(
                r"Panel:\s*\[?([^\]\—\-\n]+)\]?",
                item,
                re.IGNORECASE,
            )
            if panel_match:
                alert["panel"] = panel_match.group(1).strip()

            # Extract action
            action_match = re.search(
                r"Acci[óo]n:\s*\[?([^\]\n]+)\]?",
                item,
                re.IGNORECASE,
            )
            if action_match:
                alert["action"] = action_match.group(1).strip()

            alerts.append(alert)

        return alerts

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
