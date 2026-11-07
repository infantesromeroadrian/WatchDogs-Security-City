"""Download the evaluation images (never committed) and verify their sha256.

    python -m eval.fetch_data            # fetch + verify
    python -m eval.fetch_data --record   # first fetch: write eval/data/checksums.json

Images land in $WATCHDOGS_DATA (default ~/datasets/watchdogs/eval): keep that OUTSIDE any
synced folder and outside the repository. Licences are checked against an allow-list at fetch
time; items whose licence is not allowed are skipped, never downloaded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATA_DIR = Path(os.getenv("WATCHDOGS_DATA", Path.home() / "datasets" / "watchdogs" / "eval"))
MANIFESTS = Path(__file__).parent / "data"
CHECKSUMS = MANIFESTS / "checksums.json"
UA = {"User-Agent": "WatchDogsEval/0.1 (research; https://github.com/infantesromeroadrian/WatchDogs-Security-City)"}
ALLOWED_LICENSE = re.compile(r"^(CC0|Public domain|CC BY(-SA)? [0-9.]+)$")
COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def _get(url: str, retries: int = 6) -> bytes:
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - network flakiness / Commons 429
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
            print(f"  retry {attempt + 1}: {exc}", file=sys.stderr)
    raise RuntimeError("unreachable")


def commons_thumb(title: str) -> tuple[str, str]:
    """Return (1024-px thumbnail URL, licence short name) for a Commons file title."""
    query = urllib.parse.urlencode(
        {"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|extmetadata",
         "iiurlwidth": 1024, "format": "json"}
    )
    page = next(iter(json.loads(_get(f"{COMMONS_API}?{query}"))["query"]["pages"].values()))
    info = page["imageinfo"][0]
    return info["thumburl"], info["extmetadata"]["LicenseShortName"]["value"]


def targets() -> list[dict]:
    """Every downloadable item across the manifests: {key, path, url|title, license}."""
    out: list[dict] = []
    geo = json.loads((MANIFESTS / "geolocation.json").read_text())
    for item in geo["items"]:
        out.append({"key": f"geo/{item['city']}.jpg", "title": item["title"], "license": item["license"]})
    weapons = json.loads((MANIFESTS / "weapons.json").read_text())
    for i, item in enumerate(weapons["items"]):
        label = "pos" if item["weapon_visible"] else "neg"
        out.append({"key": f"weapons/{label}{i:02d}.jpg", "title": item["title"], "license": item["license"]})
    coco = json.loads((MANIFESTS / "coco_counts.json").read_text())
    for setname, rows in coco["sets"].items():
        for row in rows:
            out.append({"key": f"coco/{setname}/{row['file_name']}", "url": row["url"], "license": row["license"]})
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true", help="write checksums.json from this fetch")
    args = parser.parse_args()

    known = json.loads(CHECKSUMS.read_text()) if CHECKSUMS.exists() else {}
    recorded: dict[str, str] = {}
    mismatches = 0
    for item in targets():
        dest = DATA_DIR / item["key"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            if "title" in item:
                url, lic = commons_thumb(item["title"])
                if not ALLOWED_LICENSE.match(lic):
                    print(f"SKIP {item['key']}: licence {lic!r} not allowed")
                    continue
                time.sleep(1.5)
            else:
                url = item["url"]
            dest.write_bytes(_get(url))
            print(f"fetched {item['key']}")
        digest = hashlib.sha256(dest.read_bytes()).hexdigest()
        recorded[item["key"]] = digest
        if item["key"] in known and known[item["key"]] != digest:
            mismatches += 1
            print(f"MISMATCH {item['key']}: expected {known[item['key']][:12]}, got {digest[:12]}")
    if args.record:
        CHECKSUMS.write_text(json.dumps(recorded, indent=1, sort_keys=True) + "\n")
        print(f"recorded {len(recorded)} checksums")
    print(f"done: {len(recorded)} files, {mismatches} checksum mismatches")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
