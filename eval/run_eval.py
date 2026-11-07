"""Quality evaluation: one command writes metrics.json.

    python -m eval.fetch_data                       # once: download images (outside the repo)
    LLM_PROVIDER=ollama OPENAI_MODEL=qwen3-vl:8b-instruct \
        python -m eval.run_eval --out metrics.json

Provider/model come from the normal application settings, so the same command evaluates
any backend. Every figure in the README is read from the resulting metrics.json.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import statistics
import subprocess
import sys
import time
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Any

# Evaluation must measure the model, not caches or open circuit breakers.
os.environ["CACHE_ENABLED"] = "false"
os.environ["CIRCUIT_BREAKER_ENABLED"] = "false"
os.environ["METRICS_ENABLED"] = "false"
# The evaluation is an offline tool: it must neither consume nor be stopped by the application's
# daily LLM budget (its counters live in a throw-away database).
os.environ["LLM_DAILY_CALL_LIMIT"] = "100000000"
os.environ["LLM_DAILY_CALL_LIMIT_PER_USER"] = "100000000"
os.environ["LLM_BUDGET_DB"] = "/tmp/watchdogs-eval-budget.sqlite3"
os.environ.setdefault("AGENT_RETRY_MAX_ATTEMPTS", "2")
os.environ.setdefault("FLASK_ENV", "production")  # quiet logging

from src.backend.llm import get_provider_settings, get_usage_totals  # noqa: E402

from . import metrics as M  # noqa: E402
from . import synthetic  # noqa: E402
from .fetch_data import DATA_DIR, MANIFESTS  # noqa: E402

ALL_FAMILIES = ("geolocation", "ocr", "counting", "nato", "weapons", "latency")


def _b64(path: Path) -> str:
    mime = "image/png" if path.suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


class Runner:
    """Holds agents (built lazily) and per-call bookkeeping."""

    def __init__(self, run_dir: Path, limit: int | None) -> None:
        self.run_dir = run_dir
        self.limit = limit
        self._agents: dict[str, Any] = {}
        self.calls: dict[str, list[dict]] = defaultdict(list)
        self.items_log = (run_dir / "items.jsonl").open("a")

    def agent(self, name: str) -> Any:
        if name not in self._agents:
            from src.backend.agents.coordinator.agent_runners import AgentRunners

            if not hasattr(self, "_runners"):
                self._runners = AgentRunners()
            self._agents[name] = getattr(self._runners, f"{name}_agent")
        return self._agents[name]

    def call(self, agent_name: str, image: Path, tag: str) -> dict:
        """Run one agent on one image; never raises. Records latency, tokens and status."""
        before = get_usage_totals()
        start = time.perf_counter()
        try:
            result = self.agent(agent_name).analyze(_b64(image), "")
        except Exception as exc:  # noqa: BLE001 - an agent crash is a data point, not a harness failure
            result = {"status": "exception", "error": f"{type(exc).__name__}: {exc}",
                      "trace": traceback.format_exc()[-800:]}
        seconds = time.perf_counter() - start
        after = get_usage_totals()
        record = {
            "agent": agent_name, "tag": tag, "status": result.get("status"), "seconds": round(seconds, 2),
            "input_tokens": after["input_tokens"] - before["input_tokens"],
            "output_tokens": after["output_tokens"] - before["output_tokens"],
        }
        self.calls[agent_name].append(record)
        self.items_log.write(json.dumps({**record, "result": result}, ensure_ascii=False, default=str) + "\n")
        self.items_log.flush()
        print(f"  {agent_name:20} {tag:36} {record['status']:9} {seconds:6.1f}s", flush=True)
        return result

    def cap(self, rows: list) -> list:
        return rows[: self.limit] if self.limit else rows


# ----------------------------------------------------------------- families
def eval_geolocation(r: Runner) -> dict:
    items = r.cap(json.loads((MANIFESTS / "geolocation.json").read_text())["items"])
    errors: list[float | None] = []
    per_item = []
    for it in items:
        res = r.call("geolocation", DATA_DIR / "geo" / f"{it['city']}.jpg", it["city"])
        coords = res.get("coordinates") or {}
        lat, lon = coords.get("lat"), coords.get("lon")
        err = M.haversine_km(it["lat"], it["lon"], lat, lon) if lat is not None and lon is not None else None
        errors.append(err)
        per_item.append({"city": it["city"], "error_km": None if err is None else round(err, 1),
                         "predicted_city": (res.get("location") or {}).get("city"),
                         "stated_confidence": res.get("confidence")})
    return {"agent": "geolocation", **M.geolocation_summary(errors), "items": per_item}


def eval_ocr(r: Runner) -> dict:
    ocr_dir = DATA_DIR / "ocr"
    meta = json.loads((ocr_dir / "truth.json").read_text()) if (ocr_dir / "truth.json").exists() \
        else synthetic.make_ocr_set()
    meta = r.cap(meta)
    by_kind: dict[str, list[float]] = defaultdict(list)
    exact: list[bool] = []
    per_item = []
    for it in meta:
        res = r.call("ocr", ocr_dir / it["file"], it["file"])
        hyp = " ".join(res.get("extracted_text") or [])
        c = M.cer(it["text"], hyp)
        by_kind[it["kind"]].append(c)
        exact.append(M.normalize_text(it["text"]) == M.normalize_text(hyp))
        per_item.append({"file": it["file"], "truth": it["text"], "read": hyp, "cer": round(c, 3)})
    all_cer = [c for v in by_kind.values() for c in v]
    return {
        "agent": "ocr", "n": len(all_cer), "dataset": "synthetic text images (PIL, seed 7)",
        "mean_cer": round(statistics.mean(all_cer), 3) if all_cer else None,
        "median_cer": round(statistics.median(all_cer), 3) if all_cer else None,
        "exact_match_pct": round(100 * sum(exact) / len(exact), 1) if exact else None,
        "mean_cer_by_kind": {k: round(statistics.mean(v), 3) for k, v in by_kind.items()},
        "items": per_item,
    }


def _get(d: dict, *path: str) -> Any:
    for key in path:
        d = (d or {}).get(key) if isinstance(d, dict) else None
    return d


def _count_block(name: str, truth: list[int], pred: list[int | None]) -> dict:
    summary = M.count_summary(truth, pred)
    med = statistics.median(truth) if truth else 0
    summary["baseline_mae_constant_median"] = round(sum(abs(t - med) for t in truth) / len(truth), 2) if truth else None
    return {"task": name, **summary}


def eval_counting(r: Runner) -> dict:
    coco = json.loads((MANIFESTS / "coco_counts.json").read_text())["sets"]
    out: list[dict] = []
    plans = [
        ("people", "persons", [("detection", ("total_people",)), ("face_analysis", ("detection_summary", "total_persons"))]),
        ("vehicles", "vehicles", [("detection", ("total_vehicles",)), ("vehicle_detection", ("vehicle_count",))]),
        ("crowd", "persons", [("crowd_analysis", ("density_estimate", "total_count")), ("detection", ("total_people",))]),
    ]
    for setname, truth_key, agents in plans:
        rows = r.cap(coco[setname])
        for agent_name, path in agents:
            truth, pred = [], []
            for row in rows:
                res = r.call(agent_name, DATA_DIR / "coco" / setname / row["file_name"], f"{setname}/{row['file_name']}")
                value = _get(res, *path)
                truth.append(row[truth_key])
                pred.append(value if isinstance(value, int) else None)
            out.append({"agent": agent_name, "set": setname, **_count_block(f"{setname}: {'.'.join(path)}", truth, pred)})
    return {"dataset": "COCO val2017 (licences BY / BY-SA / no-known-restrictions)", "results": out}


def eval_nato(r: Runner) -> dict:
    nato_dir = DATA_DIR / "nato"
    meta = json.loads((nato_dir / "truth.json").read_text()) if (nato_dir / "truth.json").exists() \
        else synthetic.make_nato_set()
    meta = r.cap(meta)
    truth, pred = [], []
    per_item = []
    for it in meta:
        res = r.call("nato_symbology", nato_dir / it["file"], it["file"])
        entities = res.get("identified_entities") or []
        sidc = entities[0].get("sidc") if entities else None
        truth.append(it["sidc"])
        pred.append(sidc)
        per_item.append({"truth": it["sidc"], "predicted": sidc, "entities_returned": len(entities)})
    return {"agent": "nato_symbology", "dataset": "synthetic APP-6D symbols (milsymbol 3.0.5, MIT), 4 affiliations x 6 entities",
            **M.sidc_scores(truth, pred), "items": per_item}


def eval_weapons(r: Runner) -> dict:
    items = r.cap(json.loads((MANIFESTS / "weapons.json").read_text())["items"])
    truth, pred = [], []
    for i, it in enumerate(items):
        label = "pos" if it["weapon_visible"] else "neg"
        res = r.call("weapon_detection", DATA_DIR / "weapons" / f"{label}{i:02d}.jpg", f"{label}{i:02d}")
        count = res.get("weapon_count") or len(res.get("weapons") or [])
        truth.append(it["weapon_visible"])
        pred.append(bool(count))
    return {"agent": "weapon_detection", "dataset": "Wikimedia Commons PD/CC0, maintainer-labelled (small)",
            **M.binary_scores(truth, pred)}


def eval_latency(r: Runner) -> dict:
    """All 16 agents on a few images: per-agent latency and tokens (full-analysis totals)."""
    coco = json.loads((MANIFESTS / "coco_counts.json").read_text())["sets"]["people"]
    picks = [coco[i] for i in (2, 8, 14)][: (r.limit or 3)]
    names = ["vision", "ocr", "detection", "geolocation", "face_analysis", "forensic_analysis", "context_intel",
             "vehicle_detection", "weapon_detection", "crowd_analysis", "shadow_analysis",
             "infrastructure_analysis", "temporal_comparison", "night_vision", "nato_symbology", "multi_monitor"]
    mark = {n: len(r.calls[n]) for n in names}
    statuses: dict[str, list[str]] = defaultdict(list)
    for row in picks:
        for n in names:
            res = r.call(n, DATA_DIR / "coco" / "people" / row["file_name"], f"latency/{row['file_name']}")
            statuses[n].append(str(res.get("status")))
    per_agent = {}
    tot_in = tot_out = tot_s = 0.0
    for n in names:
        calls = r.calls[n][mark[n]:]
        mi = statistics.mean(c["input_tokens"] for c in calls)
        mo = statistics.mean(c["output_tokens"] for c in calls)
        ms = statistics.mean(c["seconds"] for c in calls)
        per_agent[n] = {"mean_input_tokens": round(mi), "mean_output_tokens": round(mo), "mean_seconds": round(ms, 1),
                        "statuses": statuses[n]}
        tot_in += mi
        tot_out += mo
        tot_s += ms
    return {
        "images": len(picks),
        "per_agent": per_agent,
        "full_analysis_16_agents": {
            "input_tokens": round(tot_in), "output_tokens": round(tot_out),
            "sequential_seconds_this_backend": round(tot_s, 1),
            "note": "sequential time on the evaluated backend; production runs the 16 agents in parallel",
        },
    }


FAMILIES = {"geolocation": eval_geolocation, "ocr": eval_ocr, "counting": eval_counting, "nato": eval_nato,
            "weapons": eval_weapons, "latency": eval_latency}


def _git_sha() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=Path(__file__).parent.parent, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", default=",".join(ALL_FAMILIES))
    ap.add_argument("--limit", type=int, default=None, help="cap items per family (smoke test)")
    ap.add_argument("--out", default="metrics.json")
    args = ap.parse_args()

    settings = get_provider_settings()
    run_dir = DATA_DIR / "runs" / dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    runner = Runner(run_dir, args.limit)
    get_usage_totals(reset=True)

    result: dict[str, Any] = {}
    for fam in args.families.split(","):
        print(f"== {fam}", flush=True)
        result[fam] = FAMILIES[fam](runner)

    statuses = [c["status"] for calls in runner.calls.values() for c in calls]
    doc = {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "git_commit": _git_sha(),
        "backend": {"provider": settings.provider, "model": settings.model,
                    "endpoint_host": (settings.base_url or "").split("//")[-1].split("/")[0] or "api.openai.com"},
        "limit_per_family": args.limit,
        "calls": {"total": len(statuses), "non_success": sum(s != "success" for s in statuses)},
        "usage": get_usage_totals(),
        "families": result,
    }
    Path(args.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {args.out}; item-level log: {run_dir}/items.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
