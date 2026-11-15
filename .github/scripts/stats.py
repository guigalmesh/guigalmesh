#!/usr/bin/env python3
"""Collects the GitHub numbers shown on the stats card (used by cga_assets.py).

Uses GITHUB_TOKEN if set (higher API rate limit); works without it too.
"""
import json
import os
import re
import urllib.request
from collections import Counter

USER = "guigalmesh"
SKIP_REPOS = {USER}  # the profile repo itself


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
