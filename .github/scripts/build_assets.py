#!/usr/bin/env python3
"""Generates the static CRT-style SVGs used by the profile README.

Run from the repo root:  python3 .github/scripts/build_assets.py
Edit LINES / SECTIONS below to change the text, then re-run.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path("assets")

# ---- palette -------------------------------------------------------------
BG = "#02040a"
TEXT = "#3db8ff"
GLOW = "#00e5ff"
DIM = "#2a86c4"
FONT = "ui-monospace, 'SFMono-Regular', 'DejaVu Sans Mono', Menlo, Consolas, 'Liberation Mono', monospace"

FONT_SIZE = 18
CHAR_W = FONT_SIZE * 0.6  # monospace advance estimate
TYPE_SPEED = 0.055        # seconds per typed character

# kind: "sys" = dim line shown instantly, "cmd" = prompt + typed command,
#       "out" = output shown instantly, "end" = final prompt with blinking cursor
PROMPT = "guest@guigalmesh:~$ "
LINES = [
    ("sys", "GUIGALMESH BIOS v2.6 :: phosphor CRT-9000 :: memory 640K OK"),
    ("cmd", "whoami"),
    ("out", "Guilherme · Information Systems student @ UFSM"),
    ("cmd", "cat interests.txt"),
    ("out", "[C] [low-level] [cybersecurity] [networking] [python]"),
    ("cmd", "status --career"),
    ("out", "▶ OPEN TO WORK — looking for my first opportunity in tech"),
    ("end", ""),
]

SECTIONS = {
    "about": ("./about.sh", "01"),
    "stack": ("ls ~/stack", "02"),
    "stats": ("./stats --live", "03"),
    "thm": ("cat thm_rank.log", "04"),
    "contact": ("cat contact.txt", "05"),
}


def defs_common(uid: str) -> str:
    return f"""
    <filter id="glow-{uid}" x="-20%" y="-50%" width="140%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="b1"/>
      <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b2"/>
      <feMerge><feMergeNode in="b2"/><feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="scan-{uid}" width="4" height="3" patternUnits="userSpaceOnUse">
      <rect width="4" height="1" fill="#000" fill-opacity="0.45"/>
    </pattern>"""


def header() -> str:
    W, H = 900, 400
    sx, sy, sw, sh = 40, 30, 820, 300
    tx, ty, lh = 72, 76, 30

    body = []
    clips = []
    t = 0.4
    for i, (kind, text) in enumerate(LINES):
        y = ty + i * lh
        if kind == "sys":
            body.append(
                f'<text x="{tx}" y="{y}" fill="{DIM}" opacity="0">{escape(text)}'
                f'<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/></text>'
            )
            t += 0.7
        elif kind == "out":
            body.append(
                f'<text x="{tx}" y="{y}" fill="{TEXT}" opacity="0">{escape(text)}'
                f'<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/></text>'
            )
            t += 0.45
        elif kind == "cmd":
            n = len(text)
            p = len(PROMPT)
            widths = [(p + k) * CHAR_W for k in range(n + 1)] + [W]
            dur = (n + 1) * TYPE_SPEED
            cid = f"c{i}"
            clips.append(
                f'<clipPath id="{cid}"><rect x="{tx - 2}" y="{y - 22}" height="30" width="0">'
                f'<animate attributeName="width" values="{";".join(f"{w:.1f}" for w in widths)}" '
                f'calcMode="discrete" begin="{t:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>'
            )
            body.append(
                f'<text x="{tx}" y="{y}" clip-path="url(#{cid})">'
                f'<tspan fill="{DIM}">{escape(PROMPT)}</tspan><tspan fill="{GLOW}">{escape(text)}</tspan></text>'
            )
            t += dur + 0.3
        elif kind == "end":
            cx = tx + len(PROMPT) * CHAR_W
            body.append(
                f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
                f'<text x="{tx}" y="{y}" fill="{DIM}">{escape(PROMPT)}</text>'
                f'<rect x="{cx + 2:.1f}" y="{y - 16}" width="11" height="20" fill="{GLOW}">'
                f'<animate attributeName="opacity" values="1;0" dur="1.05s" calcMode="discrete" repeatCount="indefinite"/>'
                f'</rect></g>'
            )

    vents = "".join(
        f'<rect x="{620 + k * 14}" y="356" width="8" height="18" rx="2" fill="#0a0d12"/>' for k in range(12)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="CRT monitor booting: whoami — Guilherme, Information Systems student at UFSM; interests: C, low-level, cybersecurity, networking, Python; status: open to work">
  <defs>{defs_common("h")}
    <linearGradient id="bezel" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#232a35"/><stop offset="0.5" stop-color="#151a22"/><stop offset="1" stop-color="#0c0f14"/>
    </linearGradient>
    <radialGradient id="screen" cx="50%" cy="45%" r="70%">
      <stop offset="0" stop-color="#06182e"/><stop offset="0.6" stop-color="#030b18"/><stop offset="1" stop-color="{BG}"/>
    </radialGradient>
    <radialGradient id="vignette" cx="50%" cy="50%" r="72%">
      <stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.85"/>
    </radialGradient>
    <linearGradient id="roll" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{GLOW}" stop-opacity="0"/><stop offset="0.5" stop-color="{GLOW}" stop-opacity="0.07"/><stop offset="1" stop-color="{GLOW}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0.07"/><stop offset="0.35" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="screenclip"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="26"/></clipPath>
    {"".join(clips)}
  </defs>
  <style>
    .flicker {{ animation: flicker 7s infinite; }}
    @keyframes flicker {{ 0%, 88%, 92%, 100% {{ opacity: 1 }} 89% {{ opacity: .82 }} 90% {{ opacity: .97 }} 91% {{ opacity: .88 }} }}
    .roll {{ animation: roll 6s linear infinite; }}
    @keyframes roll {{ from {{ transform: translateY(-120px) }} to {{ transform: translateY({sh + 40}px) }} }}
    .led {{ animation: led 3s ease-in-out infinite; }}
    @keyframes led {{ 50% {{ opacity: .55 }} }}
    @media (prefers-reduced-motion: reduce) {{ .flicker, .roll, .led {{ animation: none }} }}
  </style>

  <rect width="{W}" height="{H}" rx="30" fill="url(#bezel)"/>
  <rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="28" fill="none" stroke="#2c3542" stroke-width="2"/>
  <rect x="{sx - 10}" y="{sy - 10}" width="{sw + 20}" height="{sh + 20}" rx="32" fill="#05070b"/>

  <g clip-path="url(#screenclip)">
    <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#screen)"/>
    <g class="flicker" font-family="{FONT}" font-size="{FONT_SIZE}" filter="url(#glow-h)" xml:space="preserve">
      {chr(10).join("      " + b for b in body)}
    </g>
    <rect class="roll" x="{sx}" y="{sy}" width="{sw}" height="80" fill="url(#roll)"/>
    <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#scan-h)"/>
    <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#vignette)"/>
    <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#shine)"/>
  </g>

  <text x="60" y="371" font-family="{FONT}" font-size="13" letter-spacing="4" fill="#5b6778">GUIGALMESH · CRT-9000</text>
  {vents}
  <circle class="led" cx="820" cy="365" r="6" fill="{GLOW}" filter="url(#glow-h)"/>
  <circle cx="850" cy="365" r="9" fill="#0a0d12" stroke="#2c3542"/>
</svg>
"""


def section(cmd: str, num: str) -> str:
    W, H = 900, 56
    label = f"[ {num} ]"
    text_end = 28 + (len(PROMPT) + len(cmd)) * 20 * 0.6
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(cmd)}">
  <defs>{defs_common("s")}
    <linearGradient id="line" x1="0" x2="1">
      <stop offset="0" stop-color="{GLOW}" stop-opacity="0.9"/><stop offset="1" stop-color="{GLOW}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    .cur {{ animation: blink 1.05s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0 }} }}
    @media (prefers-reduced-motion: reduce) {{ .cur {{ animation: none }} }}
  </style>
  <rect width="{W}" height="{H}" rx="10" fill="{BG}"/>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="9" fill="none" stroke="{DIM}" stroke-opacity="0.45"/>
  <g font-family="{FONT}" font-size="20" filter="url(#glow-s)" xml:space="preserve">
    <text x="28" y="35"><tspan fill="{DIM}">{escape(PROMPT)}</tspan><tspan fill="{GLOW}">{escape(cmd)}</tspan></text>
    <rect class="cur" x="{text_end + 4:.1f}" y="19" width="11" height="20" fill="{GLOW}"/>
    <rect x="{text_end + 34:.1f}" y="27" width="{W - text_end - 150:.1f}" height="2" fill="url(#line)"/>
    <text x="{W - 28}" y="35" text-anchor="end" fill="{DIM}" font-size="16">{label}</text>
  </g>
  <rect width="{W}" height="{H}" rx="10" fill="url(#scan-s)"/>
</svg>
"""


def main() -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / "crt-header.svg").write_text(header(), encoding="utf-8")
    for name, (cmd, num) in SECTIONS.items():
        (OUT / f"section-{name}.svg").write_text(section(cmd, num), encoding="utf-8")
    print("assets written to", OUT.resolve())


if __name__ == "__main__":
    main()
