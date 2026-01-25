"""
Face Analysis Response Parser - CIA-Level OSINT Person Identification

Parses structured person descriptions from LLM responses including:
- Detection summary (count, visibility)
- Per-person detailed descriptors
- Distinguishing marks
- Clothing and accessories
- Confidence levels
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class FaceAnalysisResponseParser:
    """Parse structured person data from face analysis LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract comprehensive person intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed person data including all detected individuals
        """
        return {
            "detection_summary": self._parse_detection_summary(text),
            "persons": self._parse_all_persons(text),
            "most_distinctive_features": self._parse_distinctive_features(text),
            "limitations": self._parse_limitations(text),
        }

    # =========================================================================
    # DETECTION SUMMARY PARSING
    # =========================================================================

    def _parse_detection_summary(self, text: str) -> dict[str, Any]:
        """Extract detection summary (counts and quality)."""
        summary: dict[str, Any] = {
            "total_persons": 0,
            "faces_visible": 0,
            "partial_visibility": 0,
            "identification_quality": "unknown",
        }

        # Total persons
        total_match = re.search(r"Total\s*(?:de)?\s*personas:\s*(\d+)", text, re.IGNORECASE)
        if total_match:
            summary["total_persons"] = int(total_match.group(1))

        # Faces visible
        faces_match = re.search(
            r"Rostros\s*(?:claramente)?\s*visibles:\s*(\d+)", text, re.IGNORECASE
        )
        if faces_match:
            summary["faces_visible"] = int(faces_match.group(1))

        # Partial visibility
        partial_match = re.search(
            r"Personas\s*parcialmente\s*visibles:\s*(\d+)", text, re.IGNORECASE
        )
        if partial_match:
            summary["partial_visibility"] = int(partial_match.group(1))

        # Quality
        quality_match = re.search(
            r"Calidad\s*(?:general)?\s*(?:para)?\s*(?:identificación)?:\s*(Alta|Media|Baja)",
            text,
            re.IGNORECASE,
        )
        if quality_match:
            summary["identification_quality"] = quality_match.group(1).lower()

        return summary

    # =========================================================================
    # PERSON PARSING
    # =========================================================================

    def _parse_all_persons(self, text: str) -> list[dict[str, Any]]:
        """Parse all person descriptions from the response."""
        persons: list[dict[str, Any]] = []

        # Find all person sections (PERSONA 1, PERSONA 2, etc.)
        # Split by "### PERSONA" or "**PERSONA" patterns
        person_sections = re.split(
            r"(?:###\s*)?(?:\*\*)?PERSONA\s*(\d+)", text, flags=re.IGNORECASE
        )

        # Process pairs (number, content)
        for i in range(1, len(person_sections), 2):
            if i + 1 < len(person_sections):
                person_num = person_sections[i]
                person_content = person_sections[i + 1]
                person_data = self._parse_single_person(person_content, int(person_num))
                if person_data:
                    persons.append(person_data)

        # If no structured persons found, try to extract basic info
        if not persons and self._parse_detection_summary(text)["total_persons"] > 0:
            basic_person = self._extract_basic_person_info(text)
            if basic_person:
                persons.append(basic_person)

        return persons

    def _parse_single_person(self, content: str, person_number: int) -> dict[str, Any] | None:
        """Parse a single person's description."""
        person: dict[str, Any] = {
            "person_id": person_number,
            "position": self._extract_position(content),
            "demographics": self._extract_demographics(content),
            "face": self._extract_facial_features(content),
            "distinctive_marks": self._extract_distinctive_marks(content),
            "body": self._extract_body_description(content),
            "clothing": self._extract_clothing(content),
            "accessories": self._extract_accessories(content),
            "context": self._extract_context(content),
            "confidence": self._extract_confidence(content),
        }

        return person

    def _extract_position(self, text: str) -> str | None:
        """Extract person's position in image."""
        match = re.search(
            r"IDENTIFICADOR.*?[:\-]\s*(?:Persona\s*\d+\s*[:\-])?\s*(.+?)(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip().strip("\"'[]")
        return None

    def _extract_demographics(self, text: str) -> dict[str, Any]:
        """Extract demographic estimates (age, gender, ethnicity)."""
        demographics: dict[str, Any] = {
            "age_range": None,
            "age_confidence": None,
            "gender": None,
            "gender_confidence": None,
            "ethnicity_description": None,
        }

        # Age
        age_match = re.search(
            r"Edad\s*(?:aparente)?:\s*(.+?)(?:\s*-\s*Confianza:\s*(Alta|Media|Baja))?(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if age_match:
            demographics["age_range"] = age_match.group(1).strip()
            if age_match.group(2):
                demographics["age_confidence"] = age_match.group(2).lower()

        # Gender
        gender_match = re.search(
            r"Género\s*(?:aparente)?:\s*(.+?)(?:\s*-\s*Confianza:\s*(Alta|Media|Baja))?(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if gender_match:
            demographics["gender"] = gender_match.group(1).strip()
            if gender_match.group(2):
                demographics["gender_confidence"] = gender_match.group(2).lower()

        # Ethnicity
        ethnicity_match = re.search(
            r"Grupo\s*étnico\s*(?:aparente)?:\s*(.+?)(?:\n|$)", text, re.IGNORECASE
        )
        if ethnicity_match:
            demographics["ethnicity_description"] = ethnicity_match.group(1).strip()

        return demographics

    def _extract_facial_features(self, text: str) -> dict[str, str | None]:
        """Extract detailed facial features."""
        features: dict[str, str | None] = {
            "face_shape": None,
            "forehead": None,
            "eyebrows": None,
            "eyes": None,
            "nose": None,
            "mouth": None,
            "ears": None,
            "hair": None,
            "facial_hair": None,
        }

        # Define patterns for each feature
        patterns = {
            "face_shape": r"Forma\s*(?:de)?\s*cara:\s*(.+?)(?:\n|$)",
            "forehead": r"Frente:\s*(.+?)(?:\n|$)",
            "eyebrows": r"Cejas:\s*(.+?)(?:\n|$)",
            "eyes": r"Ojos:\s*(.+?)(?:\n|$)",
            "nose": r"Nariz:\s*(.+?)(?:\n|$)",
            "mouth": r"Boca:\s*(.+?)(?:\n|$)",
            "ears": r"Orejas:\s*(.+?)(?:\n|$)",
            "hair": r"Cabello:\s*(.+?)(?:\n|$)",
            "facial_hair": r"Vello\s*facial:\s*(.+?)(?:\n|$)",
        }

        for feature, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value.lower() not in ["no visible", "no aplica", "n/a", "-"]:
                    features[feature] = value

        return features

    def _extract_distinctive_marks(self, text: str) -> dict[str, list[str]]:
        """Extract distinctive marks (scars, tattoos, piercings, etc.)."""
        marks: dict[str, list[str]] = {
            "scars": [],
            "moles": [],
            "tattoos": [],
            "piercings": [],
            "other": [],
        }

        # Scars
        scars_match = re.search(r"Cicatrices:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if scars_match:
            value = scars_match.group(1).strip()
            if value.lower() not in ["no visibles", "ninguna", "no", "-"]:
                marks["scars"].append(value)

        # Moles
        moles_match = re.search(r"Lunares:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if moles_match:
            value = moles_match.group(1).strip()
            if value.lower() not in ["no visibles", "ninguno", "no", "-"]:
                marks["moles"].append(value)

        # Tattoos
        tattoos_match = re.search(r"Tatuajes:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if tattoos_match:
            value = tattoos_match.group(1).strip()
            if value.lower() not in ["no visibles", "ninguno", "no", "-"]:
                marks["tattoos"].append(value)

        # Piercings
        piercings_match = re.search(r"Piercings:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if piercings_match:
            value = piercings_match.group(1).strip()
            if value.lower() not in ["no visibles", "ninguno", "no", "-"]:
                marks["piercings"].append(value)

        # Other marks
        other_match = re.search(r"Otras\s*marcas:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if other_match:
            value = other_match.group(1).strip()
            if value.lower() not in [
                "ninguna notable",
                "ninguna",
                "no",
                "-",
            ]:
                marks["other"].append(value)

        return marks

    def _extract_body_description(self, text: str) -> dict[str, str | None]:
        """Extract body characteristics."""
        body: dict[str, str | None] = {
            "height": None,
            "build": None,
            "posture": None,
        }

        height_match = re.search(r"Altura\s*(?:aparente)?:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if height_match:
            body["height"] = height_match.group(1).strip()

        build_match = re.search(r"Complexión:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if build_match:
            body["build"] = build_match.group(1).strip()

        posture_match = re.search(r"Postura:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if posture_match:
            body["posture"] = posture_match.group(1).strip()

        return body

    def _extract_clothing(self, text: str) -> dict[str, str | None]:
        """Extract clothing description."""
        clothing: dict[str, str | None] = {
            "upper": None,
            "lower": None,
            "footwear": None,
        }

        upper_match = re.search(r"Superior:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if upper_match:
            clothing["upper"] = upper_match.group(1).strip()

        lower_match = re.search(r"Inferior:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if lower_match:
            clothing["lower"] = lower_match.group(1).strip()

        footwear_match = re.search(r"Calzado:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if footwear_match:
            value = footwear_match.group(1).strip()
            if value.lower() not in ["no visible", "-"]:
                clothing["footwear"] = value

        return clothing

    def _extract_accessories(self, text: str) -> list[str]:
        """Extract list of accessories."""
        accessories_match = re.search(
            r"Accesorios:\s*(.+?)(?:\n\n|\*\*|###|$)", text, re.IGNORECASE | re.DOTALL
        )
        if not accessories_match:
            return []

        accessories_text = accessories_match.group(1)

        # Extract individual items (comma-separated or bullet points)
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", accessories_text)
        if not items:
            # Try comma-separated
            items = [
                item.strip()
                for item in accessories_text.split(",")
                if item.strip() and item.strip().lower() not in ["ninguno", "no", "-"]
            ]

        return items

    def _extract_context(self, text: str) -> dict[str, str | None]:
        """Extract contextual information."""
        context: dict[str, str | None] = {
            "activity": None,
            "expression": None,
            "distinctive_elements": None,
        }

        activity_match = re.search(
            r"Actividad\s*(?:aparente)?:\s*(.+?)(?:\n|$)", text, re.IGNORECASE
        )
        if activity_match:
            context["activity"] = activity_match.group(1).strip()

        expression_match = re.search(r"Expresión(?:/Estado)?:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if expression_match:
            context["expression"] = expression_match.group(1).strip()

        distinctive_match = re.search(
            r"Elementos\s*distintivos:\s*(.+?)(?:\n|$)", text, re.IGNORECASE
        )
        if distinctive_match:
            context["distinctive_elements"] = distinctive_match.group(1).strip()

        return context

    def _extract_confidence(self, text: str) -> dict[str, str | None]:
        """Extract confidence level and justification."""
        confidence: dict[str, str | None] = {
            "level": None,
            "justification": None,
        }

        # Look for confidence section
        confidence_match = re.search(
            r"NIVEL\s*DE\s*CONFIANZA\s*GENERAL:\s*(Alto|Medio|Bajo)",
            text,
            re.IGNORECASE,
        )
        if confidence_match:
            confidence["level"] = confidence_match.group(1).lower()

        # Look for justification
        justification_match = re.search(
            r"Justificación:\s*(.+?)(?:\n\n|###|$)", text, re.IGNORECASE | re.DOTALL
        )
        if justification_match:
            confidence["justification"] = justification_match.group(1).strip()

        return confidence

    def _extract_basic_person_info(self, text: str) -> dict[str, Any] | None:
        """Extract basic person info when structured parsing fails."""
        # Attempt to extract any person-related information
        person: dict[str, Any] = {
            "person_id": 1,
            "position": None,
            "demographics": self._extract_demographics(text),
            "face": self._extract_facial_features(text),
            "distinctive_marks": self._extract_distinctive_marks(text),
            "body": self._extract_body_description(text),
            "clothing": self._extract_clothing(text),
            "accessories": self._extract_accessories(text),
            "context": self._extract_context(text),
            "confidence": {"level": "low", "justification": "Unstructured parsing"},
        }

        # Check if we got any meaningful data
        has_data = (
            person["demographics"]["age_range"]
            or person["demographics"]["gender"]
            or person["face"]["hair"]
            or person["clothing"]["upper"]
        )

        return person if has_data else None

    # =========================================================================
    # DISTINCTIVE FEATURES AND LIMITATIONS
    # =========================================================================

    def _parse_distinctive_features(self, text: str) -> list[str]:
        """Extract the most distinctive features for identification."""
        features_section = re.search(
            r"CARACTERÍSTICAS\s*MÁS\s*DISTINTIVAS.*?:(.*?)(?:###|LIMITACIONES|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if not features_section:
            return []

        features_text = features_section.group(1)
        features = re.findall(r"[-•\d.]+\s*(.+?)(?:\n|$)", features_text)

        return [f.strip() for f in features if f.strip()][:10]

    def _parse_limitations(self, text: str) -> list[str]:
        """Extract analysis limitations."""
        limitations_section = re.search(
            r"LIMITACIONES.*?:(.*?)(?:###|$)", text, re.IGNORECASE | re.DOTALL
        )

        if not limitations_section:
            return []

        limitations_text = limitations_section.group(1)
        limitations = re.findall(r"[-•]\s*(.+?)(?:\n|$)", limitations_text)

        return [lim.strip() for lim in limitations if lim.strip()][:5]
