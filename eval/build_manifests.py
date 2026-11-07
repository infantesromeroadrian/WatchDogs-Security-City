"""One-off helper that produced eval/data/coco_counts.json from the official COCO val2017 annotations.

Selection is deterministic (image-id order, fixed caps) so the committed manifest can be audited
and regenerated. Only metadata is stored; images are downloaded by ``fetch_data.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# COCO license ids that permit this use (attribution / share-alike / no known restrictions / US gov)
ALLOWED_LICENSES = {4, 5, 7, 8}
VEHICLE_CATS = {"car", "motorcycle", "bus", "truck", "bicycle"}  # bicycle excluded below
VEHICLE_CATS.discard("bicycle")


def build(instances_path: Path, out: Path) -> None:
    data = json.loads(instances_path.read_text())
    cats = {c["id"]: c["name"] for c in data["categories"]}
    lic = {li["id"]: li for li in data["licenses"]}
    per_image: dict[int, dict] = {}
    for img in data["images"]:
        if img["license"] in ALLOWED_LICENSES:
            per_image[img["id"]] = {"img": img, "person": 0, "vehicle": 0, "crowd": False}
    for ann in data["annotations"]:
        rec = per_image.get(ann["image_id"])
        if rec is None:
            continue
        if ann["iscrowd"]:
            rec["crowd"] = True
        name = cats[ann["category_id"]]
        if name == "person":
            rec["person"] += 1
        elif name in VEHICLE_CATS:
            rec["vehicle"] += 1

    def pick(pred, n):
        """Evenly spaced picks (in image-id order) from everything that matches ``pred``."""
        chosen = [r for _, r in sorted(per_image.items()) if not r["crowd"] and pred(r)]
        step = max(1, len(chosen) // n)
        return chosen[::step][:n]

    def stratified(key, lo, hi, per_value, extra=lambda r: True):
        """``per_value`` images for each count in [lo, hi] (first in image-id order)."""
        rows = [r for _, r in sorted(per_image.items()) if not r["crowd"] and extra(r)]
        out = []
        for value in range(lo, hi + 1):
            out += [r for r in rows if r[key] == value][:per_value]
        return out

    sets = {
        "people": stratified("person", 1, 10, 2),
        "vehicles": stratified("vehicle", 1, 10, 2, lambda r: r["person"] <= 3),
        "crowd": pick(lambda r: 11 <= r["person"] <= 40, 10),
    }
    manifest = {
        "source": "COCO val2017 (https://cocodataset.org); annotations CC BY 4.0; images keep their Flickr licence",
        "counts_note": "Counts come from COCO instance annotations (non-crowd, visible instances).",
        "sets": {
            name: [
                {
                    "id": r["img"]["id"],
                    "file_name": r["img"]["file_name"],
                    "url": r["img"]["coco_url"],
                    "flickr_url": r["img"]["flickr_url"],
                    "license": lic[r["img"]["license"]]["name"],
                    "persons": r["person"],
                    "vehicles": r["vehicle"],
                }
                for r in rows
            ]
            for name, rows in sets.items()
        },
    }
    out.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print({k: len(v) for k, v in sets.items()})


if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]))
