"""Pure metric functions (no I/O, no network) used by the evaluation runner."""

from __future__ import annotations

import math
import re
import statistics
from collections.abc import Sequence


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres (mean Earth radius 6371.0088 km)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(a))


def geolocation_summary(errors_km: Sequence[float | None]) -> dict:
    """Median error and share within 25 / 200 km. ``None`` = no usable prediction (counts as a miss)."""
    n = len(errors_km)
    valid = [e for e in errors_km if e is not None]
    return {
        "n": n,
        "n_with_prediction": len(valid),
        "median_error_km": round(statistics.median(valid), 1) if valid else None,
        "within_25km_pct": round(100 * sum(e <= 25 for e in valid) / n, 1) if n else None,
        "within_200km_pct": round(100 * sum(e <= 200 for e in valid) / n, 1) if n else None,
    }


def levenshtein(a: str, b: str) -> int:
    """Edit distance (insert / delete / substitute, unit cost)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def normalize_text(text: str) -> str:
    """Upper-case and drop whitespace / separators so layout differences are not errors."""
    return re.sub(r"[\s\-_.·]+", "", text).upper()


def cer(reference: str, hypothesis: str) -> float:
    """Character error rate on normalised text (can exceed 1.0 for long hallucinations)."""
    ref, hyp = normalize_text(reference), normalize_text(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    return levenshtein(ref, hyp) / len(ref)


def count_summary(truth: Sequence[int], predicted: Sequence[int | None]) -> dict:
    """MAE of counts. Missing predictions are scored as predicting 0 (and reported)."""
    n = len(truth)
    filled = [0 if p is None else p for p in predicted]
    abs_err = [abs(t - p) for t, p in zip(truth, filled, strict=True)]
    return {
        "n": n,
        "n_missing": sum(p is None for p in predicted),
        "mae": round(sum(abs_err) / n, 2) if n else None,
        "median_abs_error": statistics.median(abs_err) if abs_err else None,
        "exact_match_pct": round(100 * sum(e == 0 for e in abs_err) / n, 1) if n else None,
        "mean_truth": round(sum(truth) / n, 2) if n else None,
    }


def sidc_fields(sidc: str | None) -> dict[str, str] | None:
    """Split a 20-digit APP-6D SIDC; ``None`` when it is not 20 digits."""
    digits = re.sub(r"\D", "", sidc or "")
    if len(digits) != 20:
        return None
    return {"affiliation": digits[3], "symbol_set": digits[4:6], "entity": digits[10:16]}


def sidc_scores(truth: Sequence[str], predicted: Sequence[str | None]) -> dict:
    """Field-wise and exact accuracy; a missing / malformed SIDC is wrong on every field."""
    n = len(truth)
    hits = {"affiliation": 0, "symbol_set": 0, "entity": 0, "exact_16": 0}
    well_formed = 0
    for t, p in zip(truth, predicted, strict=True):
        tf, pf = sidc_fields(t), sidc_fields(p)
        if tf is None or pf is None:
            continue
        well_formed += 1
        for key in ("affiliation", "symbol_set", "entity"):
            hits[key] += tf[key] == pf[key]
        hits["exact_16"] += tf == pf
    pct = {f"{k}_acc_pct": round(100 * v / n, 1) for k, v in hits.items()} if n else {}
    return {"n": n, "well_formed_sidc_pct": round(100 * well_formed / n, 1) if n else None, **pct}


def binary_scores(truth: Sequence[bool], predicted: Sequence[bool]) -> dict:
    """Accuracy / precision / recall for a yes-no detection task."""
    tp = sum(t and p for t, p in zip(truth, predicted, strict=True))
    fp = sum((not t) and p for t, p in zip(truth, predicted, strict=True))
    fn = sum(t and (not p) for t, p in zip(truth, predicted, strict=True))
    tn = sum((not t) and (not p) for t, p in zip(truth, predicted, strict=True))
    n = len(truth)
    return {
        "n": n,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "accuracy_pct": round(100 * (tp + tn) / n, 1) if n else None,
        "precision_pct": round(100 * tp / (tp + fp), 1) if tp + fp else None,
        "recall_pct": round(100 * tp / (tp + fn), 1) if tp + fn else None,
    }
