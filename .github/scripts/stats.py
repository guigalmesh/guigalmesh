#!/usr/bin/env python3
"""Builds assets/stats.svg — a CRT-style GitHub stats card, no third-party service.

Run from the repo root:  python3 .github/scripts/stats.py
Uses GITHUB_TOKEN if set (higher API rate limit); works without it too.
"""
import json
import os
import re
import urllib.request
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

USER = "guigalmesh"
SKIP_REPOS = {USER}  # the profile repo itself
OUT = Path("assets/stats.svg")

BG, TEXT, GLOW, DIM = "#02040a", "#3db8ff", "#00e5ff", "#2a86c4"
RAMP = ["#00e5ff", "#3db8ff", "#7aa7ff", "#2a86c4", "#1d5f9a", "#16405f"]
FONT = "ui-monospace, 'SFMono-Regular', 'DejaVu Sans Mono', Menlo, Consolas, 'Liberation Mono', monospace"


def get(url: str, raw: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-stats"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
    return body if raw else json.loads(body)


def collect() -> dict:
    repos = get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    own = [r for r in repos if not r["fork"] and r["name"] not in SKIP_REPOS]
    langs = Counter()
    for r in own:
        langs.update(get(r["languages_url"]))
    try:
        html = re.sub(r"\s+", " ", get(f"https://github.com/users/{USER}/contributions", raw=True))
        m = re.search(r"([\d,]+) contributions? in the last year", html)
        contrib = m.group(1) if m else "—"
    except Exception:
        contrib = "—"
    return {
        "repos": len(own),
        "stars": sum(r["stargazers_count"] for r in own),
        "contrib": contrib,
        "langs": langs,
    }


def render(d: dict) -> str:
    W, H = 900, 250
    total = sum(d["langs"].values()) or 1
    top = d["langs"].most_common(5)
    other = total - sum(v for _, v in top)
    items = [(k, v) for k, v in top] + ([("Other", other)] if other > 0 else [])

    rows = [
        ("public repos", str(d["repos"])),
        ("stars earned", str(d["stars"])),
        ("contribs / last year", str(d["contrib"])),
        ("main language", top[0][0] if top else "—"),
    ]
    left = []
    for i, (k, v) in enumerate(rows):
        y = 100 + i * 34
        dots = "." * (24 - len(k))
        left.append(
            f'<text x="36" y="{y}"><tspan fill="{DIM}">&gt; {escape(k)} {dots}</tspan>'
            f'<tspan fill="{GLOW}"> {escape(v)}</tspan></text>'
        )

    bx, bw, by = 470, 394, 106
    bar, legend, x = [], [], bx
    for i, (name, v) in enumerate(items):
        w = bw * v / total
        c = RAMP[i % len(RAMP)]
        bar.append(f'<rect x="{x:.1f}" y="{by}" width="{max(w, 1):.1f}" height="12" fill="{c}"/>')
        x += w
        col, row = i % 2, i // 2
        lx, ly = bx + col * 200, 152 + row * 30
        legend.append(
            f'<rect x="{lx}" y="{ly - 11}" width="12" height="12" fill="{c}"/>'
            f'<text x="{lx + 22}" y="{ly}" fill="{TEXT}">{escape(name)} '
            f'<tspan fill="{DIM}">{100 * v / total:.1f}%</tspan></text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub stats: {d['repos']} public repos, {d['stars']} stars, {d['contrib']} contributions in the last year. Top languages: {escape(', '.join(n for n, _ in items))}">
  <defs>
    <filter id="g" x="-20%" y="-50%" width="140%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b1"/>
      <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b2"/>
      <feMerge><feMergeNode in="b2"/><feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" fill-opacity="0.45"/></pattern>
    <radialGradient id="bg" cx="50%" cy="40%" r="75%"><stop offset="0" stop-color="#06182e"/><stop offset="1" stop-color="{BG}"/></radialGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="11" fill="none" stroke="{DIM}" stroke-opacity="0.45"/>
  <g font-family="{FONT}" font-size="16" filter="url(#g)" xml:space="preserve">
    <text x="36" y="48" fill="{GLOW}" font-size="18" letter-spacing="3">SYSTEM DIAGNOSTICS</text>
    <text x="{W - 36}" y="48" fill="{DIM}" text-anchor="end">user: {USER}</text>
    <rect x="36" y="62" width="{W - 72}" height="1" fill="{DIM}" opacity="0.6"/>
    {"".join(left)}
    <text x="{bx}" y="94" fill="{DIM}">&gt; languages (bytes of code)</text>
    {"".join(bar)}
    {"".join(legend)}
  </g>
  <rect width="{W}" height="{H}" rx="12" fill="url(#scan)"/>
</svg>
"""


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(render(collect()), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
