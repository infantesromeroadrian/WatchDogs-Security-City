"""Render the README quality tables from metrics.json (the only source of figures).

    python -m eval.update_readme [metrics.json] [README.md]

Replaces the text between ``<!-- metrics:start -->`` and ``<!-- metrics:end -->``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

START, END = "<!-- metrics:start -->", "<!-- metrics:end -->"
SVC_START, SVC_END = "<!-- service:start -->", "<!-- service:end -->"


def _fmt(value: object, suffix: str = "") -> str:
    return "n/d" if value is None else f"{value}{suffix}"


def render(doc: dict) -> str:
    fam = doc["families"]
    backend = doc["backend"]
    lines = [
        f"Modelo evaluado: `{backend['model']}` vía `{backend['provider']}` (`{backend['endpoint_host']}`). "
        f"Generado el {doc['generated_at']} sobre el commit `{doc.get('git_commit')}`. "
        f"{doc['calls']['total']} llamadas a agentes, {doc['calls']['non_success']} sin estado `success`.",
        "",
        "| Familia | Agente | n | Resultado |",
        "|---|---|---|---|",
    ]
    if "geolocation" in fam:
        g = fam["geolocation"]
        lines.append(
            f"| Geolocalización | geolocation | {g['n']} | {g['n_with_prediction']} con coordenadas (el resto: «no determinable»); "
            f"error mediano {_fmt(g['median_error_km'], ' km')} sobre esas; "
            f"{_fmt(g['within_25km_pct'], ' %')} del total a ≤25 km; {_fmt(g['within_200km_pct'], ' %')} a ≤200 km |"
        )
    if "ocr" in fam:
        o = fam["ocr"]
        by_kind = ", ".join(f"{k} {v}" for k, v in o["mean_cer_by_kind"].items())
        lines.append(
            f"| OCR (texto sintético) | ocr | {o['n']} | CER medio {_fmt(o['mean_cer'])} "
            f"(mediana {_fmt(o['median_cer'])}); coincidencia exacta {_fmt(o['exact_match_pct'], ' %')}; {by_kind} |"
        )
    if "counting" in fam:
        for r in fam["counting"]["results"]:
            lines.append(
                f"| Conteo ({r['set']}) | {r['agent']} | {r['n']} | MAE {_fmt(r['mae'])} "
                f"(línea base «mediana constante» {_fmt(r['baseline_mae_constant_median'])}); "
                f"exactos {_fmt(r['exact_match_pct'], ' %')}; sin dato {r['n_missing']} |"
            )
    if "nato" in fam:
        n = fam["nato"]
        lines.append(
            f"| Simbología OTAN (SIDC APP-6D sintético) | nato_symbology | {n['n']} | SIDC bien formado "
            f"{_fmt(n['well_formed_sidc_pct'], ' %')}; afiliación {_fmt(n['affiliation_acc_pct'], ' %')}; "
            f"conjunto de símbolos {_fmt(n['symbol_set_acc_pct'], ' %')}; entidad {_fmt(n['entity_acc_pct'], ' %')}; "
            f"exacto {_fmt(n['exact_16_acc_pct'], ' %')} |"
        )
    if "weapons" in fam:
        w = fam["weapons"]
        lines.append(
            f"| Armas (presencia, conjunto pequeño etiquetado a mano) | weapon_detection | {w['n']} | exactitud "
            f"{_fmt(w['accuracy_pct'], ' %')}; precisión {_fmt(w['precision_pct'], ' %')}; recall "
            f"{_fmt(w['recall_pct'], ' %')} (TP {w['tp']}, FP {w['fp']}, FN {w['fn']}, TN {w['tn']}) |"
        )
    if "latency" in fam:
        lt = fam["latency"]
        full = lt["full_analysis_16_agents"]
        lines += [
            "",
            f"Coste de un análisis completo (16 agentes, un fotograma; media de {lt['images']} imágenes): "
            f"{full['input_tokens']:,} tokens de entrada y {full['output_tokens']:,} de salida; "
            f"{full['sequential_seconds_this_backend']} s sumando los 16 agentes en secuencia en este backend "
            "(en producción los 16 se ejecutan en paralelo).",
        ]
    return "\n".join(lines)


def render_service(svc: dict) -> str:
    return "\n".join(
        [
            f"Medido con `eval.service_probe`: {svc['setup']}.",
            "",
            "| Medida | Valor |",
            "|---|---|",
            f"| Análisis completos simultáneos (16 agentes cada uno) | {svc['concurrent_analyses']} × {svc['rounds']} rondas, "
            f"{svc['analyses_16_of_16_agents_ok']} con 16/16 agentes correctos |",
            f"| Latencia por análisis (mediana / máxima) | {svc['median_latency_s']} s / {svc['max_latency_s']} s "
            "(con 0,5 s por llamada simulada: demuestra el paralelismo, no la latencia de un proveedor real) |",
            f"| Memoria del worker en reposo / tras la carga | {svc['worker_rss_idle_mb']} MB / {svc['worker_rss_after_load_mb']} MB "
            f"(límite del plan free de Render: {svc['render_free_plan_limit_mb']} MB) |",
        ]
    )


def main() -> int:
    metrics_path = Path(sys.argv[1] if len(sys.argv) > 1 else "metrics.json")
    readme_path = Path(sys.argv[2] if len(sys.argv) > 2 else "README.md")
    doc = json.loads(metrics_path.read_text())
    text = readme_path.read_text()
    start, end = text.index(START), text.index(END)
    text = text[: start + len(START)] + "\n" + render(doc) + "\n" + text[end:]
    if "service" in doc:
        start, end = text.index(SVC_START), text.index(SVC_END)
        text = text[: start + len(SVC_START)] + "\n" + render_service(doc["service"]) + "\n" + text[end:]
    readme_path.write_text(text)
    print(f"README updated from {metrics_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
