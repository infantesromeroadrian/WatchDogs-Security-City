"""
Geolocation Result Combination
Single Responsibility: Combine geolocation data from multiple frames
Max: 100 lines
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class GeolocationCombiner:
    """Combines geolocation results from multiple frames"""

    @staticmethod
    def combine_results(individual_results: list) -> Dict[str, Any]:
        """
        Combine geolocation results from multiple frames.

        Accumulates clues and attempts to determine most likely location.

        Args:
            individual_results: List of frame analysis results

        Returns:
            Dict with combined geolocation data
        """
        all_clues = []
        all_locations = []
        confidence_scores = []

        for result_data in individual_results:
            result = result_data.get("result", {})
            json_result = result.get("json", {})
            agents = json_result.get("agents", {})
            geo = agents.get("geolocation", {})

            if geo.get("key_clues"):
                all_clues.extend(geo["key_clues"])

            if geo.get("location"):
                all_locations.append(geo["location"])

            if geo.get("confidence"):
                confidence_scores.append(geo["confidence"])

        # Determine most common/likely location
        if all_locations:
            # Simple: take location with highest confidence (first for now)
            best_location = all_locations[0]

            return {
                "combined_clues": all_clues,
                "most_likely_location": best_location,
                "all_detected_locations": all_locations,
                "total_clues_found": len(all_clues),
                "confidence": "MEDIUM" if len(all_clues) > 5 else "LOW",
            }
        else:
            return {
                "combined_clues": all_clues,
                "most_likely_location": None,
                "total_clues_found": len(all_clues),
                "confidence": "VERY LOW",
                "note": "No se pudo determinar ubicación con certeza",
            }
