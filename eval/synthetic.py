"""Synthetic evaluation sets with known ground truth (nothing third-party is redistributed).

* OCR: plate-like and sign-like text rendered with PIL on varied backgrounds, mild rotation, blur, noise.
* NATO: APP-6D symbols rendered with milsymbol (MIT) from known 20-digit SIDCs. Requires ``node``, ``npm``
  and ``rsvg-convert`` (librsvg2-bin).
"""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DATA_DIR = Path(os.getenv("WATCHDOGS_DATA", Path.home() / "datasets" / "watchdogs" / "eval"))
MILSYMBOL_VERSION = "3.0.5"

# Entities taken from milsymbol's own APP-6D tables (symbol set 10 = land unit, 15 = land equipment).
NATO_ENTITIES = {
    ("10", "121100"): "infantry",
    ("10", "120500"): "armour",
    ("10", "121300"): "reconnaissance",
    ("10", "120400"): "anti-tank",
    ("15", "110900"): "howitzer",
    ("15", "111000"): "missile launcher",
}
NATO_AFFILIATIONS = {"3": "friend", "6": "hostile", "4": "neutral", "1": "unknown"}

_FONT_CANDIDATES = ("DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial Bold.ttf")


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _plate(rng: random.Random) -> str:
    letters = "BCDFGHJKLMNPRSTVWXYZ"
    style = rng.choice(["es", "de", "uk"])
    if style == "es":
        return f"{rng.randint(1000, 9999)} {''.join(rng.choice(letters) for _ in range(3))}"
    if style == "de":
        return f"{''.join(rng.choice(letters) for _ in range(rng.choice([1, 2, 3])))} {''.join(rng.choice(letters) for _ in range(2))} {rng.randint(10, 9999)}"
    return f"{''.join(rng.choice(letters) for _ in range(2))}{rng.randint(10, 99)} {''.join(rng.choice(letters) for _ in range(3))}"


_SIGNS = [
    "FARMACIA 24 HORAS", "SALIDA DE EMERGENCIA", "CALLE MAYOR 15", "HOTEL CENTRAL", "NO ENTRAR",
    "AEROPUERTO", "BANK OF TRUST", "PARKING LEVEL 2", "ESTACION NORTE", "CAFE DEL MAR",
    "ZONA RESTRINGIDA", "OPEN 9 TO 18",
]


def make_ocr_set(out_dir: Path | None = None, seed: int = 7) -> list[dict]:
    """Create 24 images (12 plates, 12 signs); return [{file, text, kind}]."""
    out = (out_dir or DATA_DIR / "ocr")
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    items = [(_plate(rng), "plate") for _ in range(12)] + [(t, "sign") for t in _SIGNS]
    meta = []
    for i, (text, kind) in enumerate(items):
        w, h = (640, 220) if kind == "plate" else (900, 260)
        bg = (rng.randint(170, 255), rng.randint(170, 255), rng.randint(120, 255)) if kind == "plate" \
            else (rng.randint(10, 90), rng.randint(10, 90), rng.randint(60, 140))
        fg = (15, 15, 15) if kind == "plate" else (245, 245, 245)
        img = Image.new("RGB", (w, h), bg)
        draw = ImageDraw.Draw(img)
        font = _font(110 if kind == "plate" else 90)
        box = draw.textbbox((0, 0), text, font=font)
        draw.text(((w - (box[2] - box[0])) / 2 - box[0], (h - (box[3] - box[1])) / 2 - box[1]), text, font=font, fill=fg)
        img = img.rotate(rng.uniform(-4, 4), expand=True, fillcolor=bg, resample=Image.BICUBIC)
        img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0, 1.2)))
        px = img.load()
        for _ in range(img.width * img.height // 40):  # light salt-and-pepper noise
            x, y = rng.randrange(img.width), rng.randrange(img.height)
            v = rng.randint(0, 255)
            px[x, y] = (v, v, v)
        name = f"{kind}{i:02d}.png"
        img.save(out / name)
        meta.append({"file": name, "text": text, "kind": kind})
    (out / "truth.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    return meta


def make_nato_set(out_dir: Path | None = None) -> list[dict]:
    """Render 24 symbols (4 affiliations x 6 entities); return [{file, sidc, ...}]."""
    out = out_dir or DATA_DIR / "nato"
    out.mkdir(parents=True, exist_ok=True)
    node_dir = DATA_DIR / "node"
    for tool in ("node", "npm", "rsvg-convert"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"{tool} is required to render NATO symbols")
    if not (node_dir / "node_modules" / "milsymbol").exists():
        node_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["npm", "install", "--prefix", str(node_dir), f"milsymbol@{MILSYMBOL_VERSION}"],
                       check=True, capture_output=True)
    sidcs = []
    for aff, aff_name in NATO_AFFILIATIONS.items():
        for (symbol_set, entity), ent_name in NATO_ENTITIES.items():
            sidcs.append({"sidc": f"100{aff}{symbol_set}0000{entity}0000", "affiliation": aff_name, "entity": ent_name})
    script = (
        "import ms from 'milsymbol'; import fs from 'fs';"
        "const [, , list, dir] = process.argv;"
        "for (const s of JSON.parse(fs.readFileSync(list, 'utf8')))"
        " fs.writeFileSync(`${dir}/${s.sidc}.svg`, new ms.Symbol(s.sidc, {size: 140}).asSVG());"
    )
    (node_dir / "render.mjs").write_text(script)
    (node_dir / "list.json").write_text(json.dumps(sidcs))
    subprocess.run(["node", str(node_dir / "render.mjs"), str(node_dir / "list.json"), str(out)], check=True,
                   cwd=node_dir)
    meta = []
    for s in sidcs:
        svg, png = out / f"{s['sidc']}.svg", out / f"{s['sidc']}.png"
        subprocess.run(["rsvg-convert", "-b", "white", "-w", "512", str(svg), "-o", str(png)], check=True)
        meta.append({**s, "file": png.name})
    (out / "truth.json").write_text(json.dumps(meta, indent=1))
    return meta
