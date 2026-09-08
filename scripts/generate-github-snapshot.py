#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import date
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "AmirSadeghiH"
DISPLAY_NAME = "Amir Sadeghi"
OUT = Path("assets/github-snapshot.svg")


def github_graphql(query: str, variables: dict) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "AmirSadeghiH-profile",
        },
        method="POST",
    )
    with urlopen(req, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def build_svg(data: dict) -> str:
    user = data["user"]
    calendar = user["contributionsCollection"]["contributionCalendar"]
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    follower_count = user["followers"]["totalCount"]
    repo_count = user["repositories"]["totalCount"]
    stars = sum(r["stargazerCount"] for r in user["repositories"]["nodes"])
    year = date.today().year

    cells = []
    for wi, week in enumerate(weeks[-53:]):
        for di, day in enumerate(week["contributionDays"]):
            level = day["contributionLevel"]
            palette = {
                "NONE": "#182235",
                "FIRST_QUARTILE": "#164e63",
                "SECOND_QUARTILE": "#0e7490",
                "THIRD_QUARTILE": "#0891b2",
                "FOURTH_QUARTILE": "#38bdf8",
            }
            x = 310 + wi * 9.2
            y = 151 + di * 9.2
            cells.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="6.8" height="6.8" rx="1.7" fill="{palette.get(level, "#182235")}"/>'
            )

    contribution_text = f"{total:,} contributions in {year}"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="270" viewBox="0 0 900 270" role="img" aria-labelledby="title desc">
<title id="title">{escape(DISPLAY_NAME)} GitHub activity</title>
<desc id="desc">{escape(contribution_text)}, {repo_count} public repositories, {stars} stars and {follower_count} followers.</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="900" y2="270" gradientUnits="userSpaceOnUse"><stop stop-color="#0b1120"/><stop offset="1" stop-color="#111827"/></linearGradient>
  <radialGradient id="glow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(720 120) scale(270 150)"><stop stop-color="#38bdf8" stop-opacity=".08"/><stop offset="1" stop-color="#38bdf8" stop-opacity="0"/></radialGradient>
  <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" stroke="#94a3b8" stroke-opacity=".045"/></pattern>
  <style>.ui{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}}.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace}}</style>
</defs>
<rect x="8" y="8" width="884" height="254" rx="22" fill="url(#bg)" stroke="#263244"/>
<rect x="8" y="8" width="884" height="254" rx="22" fill="url(#grid)"/>
<rect x="8" y="8" width="884" height="254" rx="22" fill="url(#glow)"/>
<path d="M286 30V240" stroke="#334155" opacity=".65"/>
<circle cx="45" cy="44" r="4" fill="#38bdf8"/>
<text x="59" y="49" class="mono" font-size="11" font-weight="700" letter-spacing="1.7" fill="#94a3b8">GITHUB ACTIVITY</text>
<text x="42" y="91" class="ui" font-size="28" font-weight="700" fill="#f8fafc">{escape(contribution_text)}</text>
<text x="42" y="119" class="ui" font-size="13" fill="#94a3b8">A snapshot of recent engineering activity on GitHub.</text>
<line x1="42" y1="143" x2="243" y2="143" stroke="#38bdf8" stroke-opacity=".55"/>
<g class="ui">
  <text x="42" y="175" font-size="11" fill="#64748b">PUBLIC REPOS</text><text x="42" y="201" font-size="22" font-weight="700" fill="#e2e8f0">{repo_count}</text>
  <text x="130" y="175" font-size="11" fill="#64748b">STARS</text><text x="130" y="201" font-size="22" font-weight="700" fill="#e2e8f0">{stars}</text>
  <text x="205" y="175" font-size="11" fill="#64748b">FOLLOWERS</text><text x="205" y="201" font-size="22" font-weight="700" fill="#e2e8f0">{follower_count}</text>
</g>
<text x="310" y="48" class="mono" font-size="10" font-weight="700" letter-spacing="1.5" fill="#64748b">CONTRIBUTION CALENDAR · {year}</text>
<g>{''.join(cells)}</g>
<g class="mono" font-size="9" fill="#64748b"><text x="310" y="242">Less</text><rect x="343" y="235" width="7" height="7" rx="1.5" fill="#182235"/><rect x="355" y="235" width="7" height="7" rx="1.5" fill="#164e63"/><rect x="367" y="235" width="7" height="7" rx="1.5" fill="#0e7490"/><rect x="379" y="235" width="7" height="7" rx="1.5" fill="#0891b2"/><rect x="391" y="235" width="7" height="7" rx="1.5" fill="#38bdf8"/><text x="406" y="242">More</text></g>
</svg>'''
    return svg


def main() -> None:
    year = date.today().year
    query = '''
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        followers { totalCount }
        repositories(privacy: PUBLIC, first: 100, ownerAffiliations: OWNER) {
          totalCount
          nodes { stargazerCount }
        }
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { contributionCount contributionLevel date } }
          }
        }
      }
    }
    '''
    data = github_graphql(query, {
        "login": USERNAME,
        "from": f"{year}-01-01T00:00:00Z",
        "to": f"{year}-12-31T23:59:59Z",
    })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_svg(data), encoding="utf-8")
    print(f"Updated {OUT}")


if __name__ == "__main__":
    main()
