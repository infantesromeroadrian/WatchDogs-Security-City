"""
Forensic Analysis Response Parser - Image Authenticity Verification

Parses structured forensic analysis from LLM responses including:
- Authenticity verdict and confidence
- Integrity score
- Anomaly detection by category
- Suspicious regions
- Evidence chain
- Manipulation hypotheses
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class ForensicResponseParser:
    """Parse structured forensic data from image analysis LLM responses."""

    def parse(self, text: str) -> dict[str, Any]:
        """
        Parse LLM response to extract comprehensive forensic intelligence.

        Args:
            text: Raw LLM response

        Returns:
            Dict with parsed forensic data including verdicts and anomalies
        """
        return {
            "verdict": self._parse_verdict(text),
            "integrity_score": self._parse_integrity_score(text),
            "anomalies": self._parse_anomalies(text),
            "suspicious_regions": self._parse_suspicious_regions(text),
            "evidence_chain": self._parse_evidence_chain(text),
            "manipulation_hypothesis": self._parse_manipulation_hypothesis(text),
            "image_quality": self._parse_image_quality(text),
            "recommendations": self._parse_recommendations(text),
        }

    # =========================================================================
    # VERDICT PARSING
    # =========================================================================

    def _parse_verdict(self, text: str) -> dict[str, Any]:
        """Extract authenticity verdict and confidence."""
        verdict: dict[str, Any] = {
            "classification": "indeterminada",
            "confidence": "media",
            "justification": None,
        }

        # Classification
        classification_match = re.search(
            r"Clasificación:\s*\[?\s*(AUTÉNTICA|PROBABLEMENTE AUTÉNTICA|INDETERMINADA|"
            r"PROBABLEMENTE MANIPULADA|MANIPULADA|GENERADA POR IA)\s*\]?",
            text,
            re.IGNORECASE,
        )
        if classification_match:
            verdict["classification"] = classification_match.group(1).strip().lower()

        # Confidence
        confidence_match = re.search(
            r"Confianza:\s*\[?\s*(Muy Alta|Alta|Media|Baja|Muy Baja)\s*\]?",
            text,
            re.IGNORECASE,
        )
        if confidence_match:
            verdict["confidence"] = confidence_match.group(1).strip().lower()

        # Justification
        justification_match = re.search(
            r"Justificación\s*(?:breve)?:\s*\[?\s*(.+?)\s*\]?(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if justification_match:
            verdict["justification"] = justification_match.group(1).strip()

        return verdict

    # =========================================================================
    # INTEGRITY SCORE
    # =========================================================================

    def _parse_integrity_score(self, text: str) -> int | None:
        """Extract integrity score (0-100)."""
        score_match = re.search(
            r"PUNTUACIÓN\s*DE\s*INTEGRIDAD:\s*\[?\s*(\d{1,3})\s*\]?",
            text,
            re.IGNORECASE,
        )
        if score_match:
            score = int(score_match.group(1))
            return min(100, max(0, score))  # Clamp to 0-100

        # Alternative pattern
        alt_match = re.search(r"Integridad:\s*(\d{1,3})", text, re.IGNORECASE)
        if alt_match:
            return min(100, max(0, int(alt_match.group(1))))

        return None

    # =========================================================================
    # ANOMALIES PARSING
    # =========================================================================

    def _parse_anomalies(self, text: str) -> dict[str, Any]:
        """Extract anomalies detected in each category."""
        anomalies: dict[str, Any] = {
            "compression_artifacts": self._extract_anomaly_list(
                text, r"Compresión\s*y\s*Artefactos.*?:(.*?)(?=\*\*|\n\n|$)"
            ),
            "lighting_shadows": self._extract_anomaly_list(
                text, r"Iluminación\s*y\s*Sombras.*?:(.*?)(?=\*\*|\n\n|$)"
            ),
            "perspective_geometry": self._extract_anomaly_list(
                text, r"Perspectiva\s*y\s*Geometría.*?:(.*?)(?=\*\*|\n\n|$)"
            ),
            "color_tonality": self._extract_anomaly_list(
                text, r"Color\s*y\s*Tonalidad.*?:(.*?)(?=\*\*|\n\n|$)"
            ),
            "manipulation_specific": self._parse_manipulation_specific(text),
            "semantic_content": self._extract_anomaly_list(
                text, r"Contenido\s*Semántico.*?:(.*?)(?=###|\n\n|$)"
            ),
        }

        return anomalies

    def _extract_anomaly_list(self, text: str, pattern: str) -> list[str]:
        """Extract list of anomalies from a section."""
        section_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not section_match:
            return []

        section_text = section_match.group(1)

        # Check for "none detected" patterns
        none_patterns = [
            "ninguna detectada",
            "ninguno",
            "consistente",
            "coherente",
            "natural",
            "no detectado",
        ]
        for none_pattern in none_patterns:
            if none_pattern in section_text.lower():
                return []

        # Extract bullet points
        items = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)
        return [item.strip() for item in items if item.strip()]

    def _parse_manipulation_specific(self, text: str) -> dict[str, dict[str, Any]]:
        """Parse specific manipulation detection results."""
        manipulations: dict[str, dict[str, Any]] = {
            "copy_paste": {"detected": False, "details": None},
            "splicing": {"detected": False, "details": None},
            "retouching": {"detected": False, "details": None},
            "ai_generated": {"detected": False, "details": None},
        }

        # Copy-paste
        cp_match = re.search(
            r"Copy-paste:\s*\[?\s*(Detectado|No detectado)\s*\]?\s*(?:-\s*(.+?))?(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if cp_match:
            manipulations["copy_paste"]["detected"] = cp_match.group(1).lower() == "detectado"
            if cp_match.group(2):
                manipulations["copy_paste"]["details"] = cp_match.group(2).strip()

        # Splicing
        splice_match = re.search(
            r"Splicing:\s*\[?\s*(Detectado|No detectado)\s*\]?\s*(?:-\s*(.+?))?(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if splice_match:
            manipulations["splicing"]["detected"] = splice_match.group(1).lower() == "detectado"
            if splice_match.group(2):
                manipulations["splicing"]["details"] = splice_match.group(2).strip()

        # Retouching
        retouch_match = re.search(
            r"Retoque:\s*\[?\s*(Detectado|No detectado)\s*\]?\s*(?:-\s*(.+?))?(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if retouch_match:
            manipulations["retouching"]["detected"] = retouch_match.group(1).lower() == "detectado"
            if retouch_match.group(2):
                manipulations["retouching"]["details"] = retouch_match.group(2).strip()

        # AI Generation
        ai_match = re.search(
            r"Generación\s*IA:\s*\[?\s*(Detectado|No detectado)\s*\]?\s*(?:-\s*(.+?))?(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if ai_match:
            manipulations["ai_generated"]["detected"] = ai_match.group(1).lower() == "detectado"
            if ai_match.group(2):
                manipulations["ai_generated"]["details"] = ai_match.group(2).strip()

        return manipulations

    # =========================================================================
    # SUSPICIOUS REGIONS
    # =========================================================================

    def _parse_suspicious_regions(self, text: str) -> list[str]:
        """Extract list of suspicious regions in the image."""
        section_match = re.search(
            r"REGIONES\s*SOSPECHOSAS:(.*?)(?=###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)

        # Check for "none" patterns
        if re.search(r"ninguna|no\s+hay|no\s+se\s+detectan", section_text, re.IGNORECASE):
            return []

        # Extract regions (location descriptions)
        regions = re.findall(r"[-•\d.]+\s*(.+?)(?:\n|$)", section_text)
        return [r.strip() for r in regions if r.strip()][:10]

    # =========================================================================
    # EVIDENCE CHAIN
    # =========================================================================

    def _parse_evidence_chain(self, text: str) -> list[dict[str, Any]]:
        """Extract ordered evidence chain."""
        evidence_list: list[dict[str, Any]] = []

        section_match = re.search(
            r"CADENA\s*DE\s*EVIDENCIAS:(.*?)(?=###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return evidence_list

        section_text = section_match.group(1)

        # Pattern: 1. [Evidence] - Peso: [Weight] - Indica: [Indicates]
        evidence_pattern = re.compile(
            r"(\d+)\.\s*\[?(.+?)\]?\s*-\s*Peso:\s*\[?(Alto|Medio|Bajo)\]?\s*-\s*Indica:\s*\[?(.+?)\]?(?:\n|$)",
            re.IGNORECASE,
        )

        for match in evidence_pattern.finditer(section_text):
            evidence_list.append(
                {
                    "order": int(match.group(1)),
                    "evidence": match.group(2).strip(),
                    "weight": match.group(3).strip().lower(),
                    "indicates": match.group(4).strip(),
                }
            )

        # Sort by order
        evidence_list.sort(key=lambda x: x.get("order", 0))

        return evidence_list

    # =========================================================================
    # MANIPULATION HYPOTHESIS
    # =========================================================================

    def _parse_manipulation_hypothesis(self, text: str) -> str | None:
        """Extract manipulation hypothesis if detected."""
        hypothesis_match = re.search(
            r"HIPÓTESIS\s*DE\s*MANIPULACIÓN:(.*?)(?=###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not hypothesis_match:
            return None

        hypothesis = hypothesis_match.group(1).strip()

        # Check for "no manipulation" patterns
        if re.search(
            r"no\s+se\s+detecta|no\s+aplica|imagen\s+auténtica",
            hypothesis,
            re.IGNORECASE,
        ):
            return None

        # Clean up the text
        hypothesis = re.sub(r"^\s*[-•]\s*", "", hypothesis)
        hypothesis = re.sub(r"\n+", " ", hypothesis).strip()

        return hypothesis if hypothesis else None

    # =========================================================================
    # IMAGE QUALITY
    # =========================================================================

    def _parse_image_quality(self, text: str) -> dict[str, Any]:
        """Extract image quality assessment for analysis."""
        quality: dict[str, Any] = {
            "resolution": None,
            "compression": None,
            "limiting_factors": [],
        }

        # Resolution
        resolution_match = re.search(
            r"Resolución:\s*\[?\s*(Suficiente|Limitada|Insuficiente)\s*\]?",
            text,
            re.IGNORECASE,
        )
        if resolution_match:
            quality["resolution"] = resolution_match.group(1).strip().lower()

        # Compression
        compression_match = re.search(
            r"Compresión:\s*\[?\s*(Baja|Media|Alta|Muy alta)\s*\]?",
            text,
            re.IGNORECASE,
        )
        if compression_match:
            quality["compression"] = compression_match.group(1).strip().lower()

        # Limiting factors
        factors_match = re.search(
            r"Factores\s*limitantes:\s*\[?(.+?)\]?(?:\n|###|$)",
            text,
            re.IGNORECASE,
        )
        if factors_match:
            factors_text = factors_match.group(1)
            factors = re.findall(r"[-•]\s*(.+?)(?:,|\n|$)", factors_text)
            if not factors:
                factors = [f.strip() for f in factors_text.split(",") if f.strip()]
            quality["limiting_factors"] = [f.strip() for f in factors if f.strip()]

        return quality

    # =========================================================================
    # RECOMMENDATIONS
    # =========================================================================

    def _parse_recommendations(self, text: str) -> list[str]:
        """Extract recommendations for further verification."""
        section_match = re.search(
            r"RECOMENDACIONES:(.*?)(?=━|###|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            return []

        section_text = section_match.group(1)

        recommendations = re.findall(r"[-•]\s*(.+?)(?:\n|$)", section_text)

        return [r.strip() for r in recommendations if r.strip()][:10]
