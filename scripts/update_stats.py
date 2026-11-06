#!/usr/bin/env python3
"""Sync QookiX organization stats into the GitHub profile README.

Data source: public GitHub REST API. Run without network using --demo to
regenerate the layout-only example values.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "profile" / "README.md"
ORG = os.environ.get("QK_ORG", "QookiX")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
API = "https://api.github.com"

STATS_START = "<!-- QK:STATS:START -->"
STATS_END = "<!-- QK:STATS:END -->"
LANG_START = "<!-- QK:LANG:START -->"
LANG_END = "<!-- QK:LANG:END -->"

DEMO = {
    "repos": 11,
    "stars": 1240,
    "forks": 186,
    "commits": 3480,
    "languages": [("Rust", 38), ("TypeScript", 27), ("Vue", 12), ("Kotlin", 9), ("C#", 8), ("Go", 6)],
    "weeks": [4, 9, 14, 21, 12, 6, 25, 19, 10, 16, 22, 13],
}


def api_get(path: str, params: dict | None = None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "QookiX-org-stats",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8")), resp.headers


def list_repos() -> list[dict]:
    repos: list[dict] = []
    page = 1
    while page <= 10:
        body, headers = api_get(f"/orgs/{ORG}/repos", {"per_page": 100, "type": "public", "page": page})
        if not isinstance(body, list):
            raise RuntimeError("unexpected response for organization repositories")
        repos.extend(body)
        if 'rel="next"' not in (headers.get("Link") or ""):
            break
        page += 1
    return [r for r in repos if not r.get("fork")]


def commit_count(name: str) -> int:
    try:
        body, headers = api_get(f"/repos/{ORG}/{name}/commits", {"per_page": 1})
        match = re.search(r'[?&]page=(\d+)>;\s*rel="last"', headers.get("Link") or "")
        if match:
            return int(match.group(1))
        return len(body) if isinstance(body, list) else 0
    except Exception:
        return 0


def repo_languages(name: str) -> dict[str, int]:
    try:
        body, _ = api_get(f"/repos/{ORG}/{name}/languages")
        return body if isinstance(body, dict) else {}
    except Exception:
        return {}


def recent_weeks(names: list[str]) -> list[int]:
    now = datetime.now(timezone.utc)
    since = (now - timedelta(weeks=12)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    weeks = [0] * 12
    for name in names:
        page = 1
        while page <= 3:
            try:
                body, headers = api_get(
                    f"/repos/{ORG}/{name}/commits",
                    {"since": since, "per_page": 100, "page": page},
                )
            except Exception:
                break
            if not isinstance(body, list) or not body:
                break
            for item in body:
                date = ((item.get("commit") or {}).get("author") or {}).get("date")
                if not date:
                    continue
                try:
                    when = datetime.fromisoformat(date.replace("Z", "+00:00"))
                except ValueError:
                    continue
                index = 11 - (now - when).days // 7
                if 0 <= index < 12:
                    weeks[index] += 1
            if 'rel="next"' not in (headers.get("Link") or ""):
                break
            page += 1
    return weeks


def fetch() -> dict:
    repos = list_repos()
    if not repos:
        raise RuntimeError("no public repositories found, refusing to overwrite README")
    names = [r["name"] for r in repos]
    totals: dict[str, int] = {}
    commits = 0
    for name in names:
        commits += commit_count(name)
        for lang, size in repo_languages(name).items():
            totals[lang] = totals.get(lang, 0) + size

    grand = sum(totals.values())
    ranked = sorted(((k, round(v * 100 / grand)) for k, v in totals.items()), key=lambda x: -x[1]) if grand else []
    top = [[k, v] for k, v in ranked[:6] if v > 0]
    rest = sum(v for _, v in ranked[6:])
    if rest > 0:
        top.append(["其它", rest])
    if not top:
        top = [["未标注", 100]]
    else:
        top[0][1] = max(1, top[0][1] + 100 - sum(v for _, v in top))

    return {
        "repos": len(repos),
        "stars": sum(r.get("stargazers_count", 0) for r in repos),
        "forks": sum(r.get("forks_count", 0) for r in repos),
        "commits": commits,
        "languages": [(k, int(v)) for k, v in top],
        "weeks": recent_weeks(names),
    }


def fmt(value: int) -> str:
    return f"{value / 1000:.1f}k" if value >= 10_000 else f"{value:,}"


def badge(label: str, value: str, color: str) -> str:
    left = urllib.parse.quote(label, safe="")
    right = urllib.parse.quote(value, safe="")
    return f"https://img.shields.io/badge/{left}-{right}-{color}?style=flat-square"


def sparkline(weeks: list[int]) -> str:
    bars = "▁▂▃▄▅▆▇█"
    peak = max(weeks) or 1
    return "".join(bars[min(7, int(w / peak * 7))] if w else bars[0] for w in weeks)


def render_stats(data: dict, demo: bool = False) -> str:
    items = [
        ("Stars", fmt(data["stars"]), "E9A44C"),
        ("Repos", fmt(data["repos"]), "2F81F7"),
        ("Commits", fmt(data["commits"]), "A45A2A"),
        ("Forks", fmt(data["forks"]), "5D8A66"),
    ]
    lines = ['<p align="center">']
    for label, value, color in items:
        lines.append(f'  <img src="{badge(label, value, color)}" alt="{label}: {value}" />')
    lines += [
        "</p>",
        "",
        '<p align="center"><sub>近 12 周提交活跃度</sub> &nbsp; <code>' + sparkline(data["weeks"]) + "</code></p>",
        "",
    ]
    if demo:
        lines.append('<p align="center"><sub>版式示例数据 · 推送后由 GitHub Actions 自动同步为真实数据</sub></p>')
    else:
        lines.append('<p align="center"><sub>数据由 GitHub Actions 每日自动同步 · 无需手工维护</sub></p>')
    return "\n".join(lines)


def mermaid_label(name: str) -> str:
    return name.replace('"', "'").replace("\r", " ").replace("\n", " ")


def render_languages(data: dict) -> str:
    lines = ["```mermaid", "pie showData", f"    title {ORG} 语言构成"]
    for name, percent in data["languages"]:
        lines.append(f'    "{mermaid_label(name)}" : {percent}')
    lines += ["```", "", "| 语言 | 占比 |", "| :--- | ---: |"]
    for name, percent in data["languages"]:
        lines.append(f"| {name} | {percent}% |")
    lines += ["", '<p align="center"><sub>按各仓库 languages 接口字节数聚合 · 每日自动同步</sub></p>']
    return "\n".join(lines)


def replace_block(text: str, start: str, end: str, body: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        raise RuntimeError(f"missing markers in README: {start} / {end}")
    replacement = start + "\n\n" + body + "\n\n" + end
    return pattern.sub(lambda _: replacement, text, count=1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="use example values without network")
    parser.add_argument("--check", action="store_true", help="render and print without writing")
    args = parser.parse_args()

    try:
        data = dict(DEMO) if args.demo else fetch()
    except Exception as exc:
        print(f"failed to fetch GitHub data: {exc}", file=sys.stderr)
        return 1

    stats_block = render_stats(data, demo=args.demo)
    lang_block = render_languages(data)
    if args.check:
        print(stats_block, "\n\n---\n", lang_block, sep="\n")
        return 0

    text = README.read_text(encoding="utf-8").replace("\r\n", "\n")
    text = replace_block(text, STATS_START, STATS_END, stats_block)
    text = replace_block(text, LANG_START, LANG_END, lang_block)
    with open(README, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    mode = "demo" if args.demo else "live GitHub API"
    print(f"profile/README.md updated from {mode}: {data['repos']} repos, {data['stars']} stars, {data['commits']} commits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
