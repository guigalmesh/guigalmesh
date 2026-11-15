#!/usr/bin/env python3
"""CGA dithered assets for the profile README.

Run from the repo root:
  python3 .github/scripts/cga_assets.py          # header GIF + section strips + stats card
  python3 .github/scripts/cga_assets.py stats    # only the stats card (used by the workflow)

Needs Pillow and NumPy. Fonts: DejaVu Sans Mono (installed on most Linux systems).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = Path("assets/cga")
SCALE = 3  # every logical pixel becomes SCALE x SCALE screen pixels

# CGA palette 1, high intensity: black, magenta, cyan, white
PALETTE = ["#000000", "#ff55ff", "#55ffff", "#ffffff"]
BLACK, MAGENTA, CYAN, WHITE = range(4)

BANDS = 3.0      # marble stripes across the value range
CONTRAST = 1.6
DARKEN = 0.32    # 0..1, shifts the marble towards black
WAVE_FRAMES = 64  # more frames per loop = slower waves
WAVE_MS = 80

HEADER_TITLE = "GUIGALMESH"
HEADER_SUB = "cybersecurity @ forte security"
SECTIONS = {
    "about": "01  about",
    "projects": "02  projects",
    "stack": "03  stack",
    "stats": "04  stats",
    "contact": "05  contact",
}

# Text cards use a smaller pixel (2x) so long lines stay easy to read.
TEXT_SCALE = 2
ABOUT = [
    ("work", "cybersecurity @ Forte Security"),
    ("studying", "Information Systems @ UFSM"),
    ("core", "C, Linux & low-level"),
    ("security", "web security, networking"),
    ("exploring", "Python & machine learning · Haskell · Java"),
]
PROJECTS = [
    ("analisador-de-headerhttp", "Security header grader in Haskell + web front-end"),
    ("visualizador-algoritmos", "Sorting visualizer in pure C + Allegro 5"),
    ("ml-rotofauna-atropelada", "ML pipeline predicting wildlife roadkill"),
    ("simple-keylogger-c", "Linux keylogger client/server in C"),
    ("general-deck-game", "Auto-battler in Java + LibGDX"),
    ("jogo-da-forca-mips", "Hangman in MIPS Assembly"),
]

BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]) / 64.0


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf", size)


def palette_bytes() -> list[int]:
    pal = []
    for c in PALETTE:
        pal += [int(c[i:i + 2], 16) for i in (1, 3, 5)]
    return pal + [0] * (768 - len(pal))


def to_image(idx: np.ndarray, scale: int = SCALE) -> Image.Image:
    im = Image.fromarray(idx.astype(np.uint8), "P")
    im.putpalette(palette_bytes())
    h, w = idx.shape
    return im.resize((w * scale, h * scale), Image.NEAREST)


# ---- dithering --------------------------------------------------------------

def field(t: float, w: int, h: int, ox: float = 0, oy: float = 0) -> np.ndarray:
    """Seamlessly looping marble-like wave field in [0, 1]. t in [0, 2*pi)."""
    y, x = np.mgrid[0:h, 0:w].astype(float)
    x += ox
    y += oy
    wx = x + 18 * np.sin(y * 0.045 + t) + 10 * np.sin(y * 0.11 - 2 * t)
    wy = y + 14 * np.cos(x * 0.032 - t) + 6 * np.cos(x * 0.09 + t)
    v = (
        np.sin(wx * 0.045 + 2.2 * np.sin(wy * 0.05 + t))
        + 0.6 * np.sin((wx + wy) * 0.03 - t)
        + 0.4 * np.cos(wy * 0.08 + np.sin(wx * 0.02) * 3 + 2 * t)
    )
    v = (v + 2.0) / 4.0  # fixed normalisation keeps strips consistent with the header
    v = 0.5 + 0.5 * np.sin(v * np.pi * BANDS)
    return np.clip((v - 0.5) * CONTRAST + 0.5 - DARKEN, 0, 1)


def mosaic(w: int, h: int, seed: int) -> np.ndarray:
    """Dither cell size per pixel: mostly 1, some glitchy blocks at 2 or 4."""
    rng = np.random.default_rng(seed)
    m = np.ones((h, w), dtype=int)
    bs = 10
    for by in range(0, h, bs):
        for bx in range(0, w, bs):
            r = rng.random()
            if r < 0.10:
                m[by:by + bs, bx:bx + bs] = 2
            elif r < 0.14:
                m[by:by + bs, bx:bx + bs] = 4
    return m


def dither(v: np.ndarray, cell: np.ndarray | int = 1) -> np.ndarray:
    h, w = v.shape
    y, x = np.mgrid[0:h, 0:w]
    thr = BAYER8[(y // cell) % 8, (x // cell) % 8]
    return np.floor(v * 3 + thr).clip(0, 3)


def bayer_fill(w: int, h: int, level: float) -> np.ndarray:
    """Boolean ordered-dither pattern with the given density (0..1)."""
    y, x = np.mgrid[0:h, 0:w]
    return BAYER8[y % 8, x % 8] < level


# ---- text -------------------------------------------------------------------

def draw_text(mask_size, items):
    """items: list of (x, y, text, font). Returns boolean ink mask (crisp, no AA)."""
    img = Image.new("L", mask_size, 0)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    for x, y, text, f in items:
        # align every string on the same cap-height top, so lowercase words line up
        ref = d.textbbox((0, 0), "Ag", font=f)
        d.text((x, y - ref[1]), text, font=f, fill=255)
    return np.array(img) > 0


def text_size(text, f):
    b = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), text, font=f)
    return b[2] - b[0], b[3] - b[1]


# ---- assets -----------------------------------------------------------------

def header(frames: int = WAVE_FRAMES, frame_ms: int = WAVE_MS) -> None:
    W, H = 300, 110
    cell = mosaic(W, H, seed=7)
    big, small = font(22, bold=True), font(9)
    tw, th = text_size(HEADER_TITLE, big)
    sw, _ = text_size(HEADER_SUB, small)
    px, py = 14, H - 48
    panel = np.zeros((H, W), bool)
    panel[py - 6:py + th + 7, px - 6:px + tw + 7] = True
    panel[py + th + 8:py + th + 23, px - 6:px + sw + 7] = True
    ink = draw_text((W, H), [(px, py, HEADER_TITLE, big), (px, py + th + 10, HEADER_SUB, small)])

    out = []
    for i in range(frames):
        idx = dither(field(2 * np.pi * i / frames, W, H), cell)
        idx[panel] = BLACK
        idx[ink] = WHITE
        out.append(to_image(idx))
    path = OUT / "header.gif"
    out[0].save(path, save_all=True, append_images=out[1:], duration=frame_ms, loop=0, optimize=True)
    print(f"{path}  {path.stat().st_size / 1024:.0f} KB")


def section(name: str, label: str, n: int) -> None:
    W, H = 300, 20
    v = field(0.9 * n, W, H, ox=n * 137, oy=n * 53)
    idx = dither(v, mosaic(W, H, seed=n))
    f = font(11, bold=True)
    tw, th = text_size(label, f)
    panel_w = tw + 16
    idx[:, :panel_w] = BLACK
    idx[:, panel_w:panel_w + 2] = CYAN  # thin cyan edge between label and marble
    ink = draw_text((W, H), [(8, (H - th) // 2, label, f)])
    idx[ink] = WHITE
    path = OUT / f"section-{name}.png"
    to_image(idx).save(path, optimize=True)


def stats_card(d: dict) -> None:
    W, H = 450, 130
    idx = np.full((H, W), BLACK)
    idx[dithered_frame(W, H)] = MAGENTA

    big, small = font(13, bold=True), font(12)
    pad = 14
    top = d["langs"].most_common(4)
    head = [(pad, 12, "SYSTEM STATS", big)]
    handle = "@guigalmesh"
    head_dim = [(W - pad - text_size(handle, small)[0], 13, handle, small)]
    idx[32:33, pad:W - pad] = CYAN

    keys, vals = [], []
    rows = [
        ("repos", str(d["repos"])),
        ("stars", str(d["stars"])),
        ("contribs/yr", str(d["contrib"])),
        ("main", top[0][0].lower() if top else "-"),
    ]
    for i, (k, v) in enumerate(rows):
        y = 44 + i * 20
        keys.append((pad, y, k, small))
        vals.append((150 - text_size(v, small)[0], y, v, small))

    total = sum(d["langs"].values()) or 1
    lx, bx, bw = 176, 268, 120
    fills = [WHITE, CYAN, MAGENTA, CYAN]
    densities = [1.0, 0.75, 0.75, 0.4]
    for i, (name, val) in enumerate(top):
        y = 44 + i * 20
        pct = val / total
        keys.append((lx, y, name[:10].lower(), small))
        pct_txt = f"{100 * pct:.0f}%"
        vals.append((W - pad - text_size(pct_txt, small)[0], y, pct_txt, small))
        w = max(2, round(bw * pct))
        bar = np.zeros((H, W), bool)
        bar[y:y + 9, bx:bx + w] = True
        idx[bar & bayer_fill(W, H, densities[i])] = fills[i]
        track = np.zeros((H, W), bool)
        track[y + 8:y + 9, bx + w:bx + bw] = True
        idx[track & bayer_fill(W, H, 0.25)] = MAGENTA
    idx[draw_text((W, H), head)] = WHITE
    idx[draw_text((W, H), head_dim)] = MAGENTA
    idx[draw_text((W, H), keys)] = CYAN
    idx[draw_text((W, H), vals)] = WHITE
    path = OUT / "stats.png"
    to_image(idx, TEXT_SCALE).save(path, optimize=True)
    print(path)


def dithered_frame(w: int, h: int, color: int = MAGENTA, t: int = 2) -> np.ndarray:
    frame = np.zeros((h, w), bool)
    frame[:t, :] = frame[-t:, :] = frame[:, :t] = frame[:, -t:] = True
    return frame & bayer_fill(w, h, 0.5)


def about_card() -> None:
    W = 450
    label_f, text_f = font(12, bold=True), font(12)
    row_h, pad = 20, 14
    H = pad * 2 + row_h * len(ABOUT) - 6
    idx = np.full((H, W), BLACK)
    idx[dithered_frame(W, H)] = MAGENTA
    labels, values = [], []
    lw = max(text_size(k, label_f)[0] for k, _ in ABOUT)
    for i, (k, v) in enumerate(ABOUT):
        y = pad + i * row_h
        # small cyan block as a bullet
        idx[y + 2:y + 8, pad:pad + 6] = CYAN
        labels.append((pad + 14, y, k, label_f))
        values.append((pad + 14 + lw + 18, y, v, text_f))
    idx[draw_text((W, H), labels)] = CYAN
    idx[draw_text((W, H), values)] = WHITE
    to_image(idx, TEXT_SCALE).save(OUT / "about.png", optimize=True)


def project_card(n: int, name: str, desc: str) -> None:
    W, H = 450, 40
    name_f, desc_f = font(12, bold=True), font(11)
    idx = np.full((H, W), BLACK)
    idx[dithered_frame(W, H, t=1)] = MAGENTA
    # index tag on the left
    tag = f"{n:02d}"
    tw, _ = text_size(tag, name_f)
    idx[:, : tw + 20] = CYAN
    tag_ink = draw_text((W, H), [(10, 14, tag, name_f)])
    idx[tag_ink] = BLACK
    x = tw + 32
    idx[draw_text((W, H), [(x, 8, name, name_f)])] = CYAN
    idx[draw_text((W, H), [(x, 24, desc, desc_f)])] = WHITE
    # arrow on the right hints that the card is a link
    idx[draw_text((W, H), [(W - 22, 14, "->", name_f)])] = MAGENTA
    to_image(idx, TEXT_SCALE).save(OUT / f"project-{n}.png", optimize=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(Path(__file__).parent))
    from stats import collect  # noqa: E402  (same folder)

    if sys.argv[1:] != ["stats"]:
        header()
        for n, (name, label) in enumerate(SECTIONS.items(), 1):
            section(name, label, n)
        about_card()
        for n, (name, desc) in enumerate(PROJECTS, 1):
            project_card(n, name, desc)
    stats_card(collect())


if __name__ == "__main__":
    main()
