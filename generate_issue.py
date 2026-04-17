#!/usr/bin/env python3
"""
Overwatch Stadium Weekly Meta Report — Newsletter Content Generator

Scrapes stadiumbuilds.io for trending builds across all heroes,
formats into a publish-ready newsletter (Markdown).

Usage:
    python3 generate_issue.py                    # Generate current issue, print to stdout
    python3 generate_issue.py -o issue_YYYY-MM-DD.md  # Save to file
    python3 generate_issue.py --json             # JSON output for programmatic use

Output is Markdown formatted for Beehiiv/Substack paste.
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Add scraper to path
SKILL_DIR = Path("/home/aj/.hermes/skills/research/overwatch-stadium-research/scripts")
sys.path.insert(0, str(SKILL_DIR))

from scrape import fetch_hero_data, get_heroes

ANON_KEY_PATH = SKILL_DIR / ".anon_key"

# Role ordering and emojis for newsletter
ROLES = ["Tank", "Damage", "Support"]
ROLE_DISPLAY = {
    "Tank": "🛡️ Tank",
    "Damage": "⚔️ Damage",
    "Support": "💚 Support",
}


def load_anon_key():
    with open(ANON_KEY_PATH) as f:
        return f.read().strip()


def scrape_all_heroes(anon_key, builds_per_hero=5):
    """Scrape trending builds for every hero. Returns dict keyed by hero slug."""
    heroes = get_heroes(anon_key)
    all_data = {}

    for slug, info in heroes.items():
        try:
            data = fetch_hero_data(slug, sort="trending", limit=builds_per_hero)
            builds = data.get("builds", [])
            abilities = data.get("abilities", [])
            all_data[slug] = {
                "name": info["name"],
                "role": info["role"],
                "builds": builds,
                "abilities": abilities,
            }
        except Exception as e:
            print(f"  ⚠ {slug}: {e}", file=sys.stderr)
            all_data[slug] = {
                "name": info["name"],
                "role": info["role"],
                "builds": [],
                "abilities": [],
            }

    return all_data


def pick_top_builds(all_data, per_role=3):
    """Select top builds per role by hotness score, then views."""
    by_role = defaultdict(list)

    for slug, hero in all_data.items():
        for build in hero["builds"]:
            by_role[hero["role"]].append(
                {
                    **build,
                    "hero": hero["name"],
                    "hero_slug": slug,
                }
            )

    top = {}
    for role in ROLES:
        builds = by_role.get(role, [])
        # Sort by hotness (trending), then views as tiebreaker
        builds.sort(key=lambda b: (b.get("hotness", 0), b.get("views", 0)), reverse=True)
        top[role] = builds[:per_role]

    return top


def format_issue(all_data, top_builds, issue_date=None):
    """Format the newsletter as Markdown."""
    if issue_date is None:
        issue_date = datetime.now()

    week_str = issue_date.strftime("%B %d, %Y")
    issue_num = issue_date.isocalendar()[1]  # ISO week number

    lines = []
    lines.append(f"# 🏟️ Overwatch Stadium Meta Report")
    lines.append(f"**Week of {week_str}** · Issue #{issue_num}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "Your weekly roundup of the best Stadium builds, sorted by what's trending right now. "
        "Every build includes a forge code — copy it and import in-game to try it immediately."
    )
    lines.append("")

    # Top builds per role
    for role in ROLES:
        builds = top_builds.get(role, [])
        if not builds:
            continue

        lines.append(f"## {ROLE_DISPLAY[role]}")
        lines.append("")

        for i, b in enumerate(builds, 1):
            code_str = f" · Forge: `{b['code']}`" if b.get("code") else ""
            tag_str = f" [{b['tag']}]" if b.get("tag") else ""
            stats_str = f" — {b['stats']}" if b.get("stats") else ""

            lines.append(f"### {i}. {b['title']}")
            lines.append(f"**{b['hero']}**{tag_str} · {b.get('views', 0):,} views · {b.get('likes', 0)} likes{code_str}{stats_str}")
            lines.append("")
            lines.append(f"🔗 [{b['title'][:50]}]({b['url']})")
            lines.append("")

    # Forge code quick-reference table
    lines.append("## 📋 Quick Import Table")
    lines.append("")
    lines.append("| Hero | Build | Forge Code | Views | Tag |")
    lines.append("|------|-------|------------|-------|-----|")

    for role in ROLES:
        for b in top_builds.get(role, []):
            code = b.get("code") or "—"
            title = b["title"][:40]
            lines.append(f"| {b['hero']} | {title} | `{code}` | {b.get('views', 0):,} | {b.get('tag', '—')} |")

    lines.append("")

    # Meta snapshot
    lines.append("## 📊 Meta Snapshot")
    lines.append("")

    # Count builds per hero to show what's popular
    hero_build_counts = {}
    for slug, hero in all_data.items():
        if hero["builds"]:
            total_views = sum(b.get("views", 0) for b in hero["builds"])
            hero_build_counts[hero["name"]] = {
                "builds": len(hero["builds"]),
                "total_views": total_views,
                "role": hero["role"],
            }

    # Top 5 by total views
    top_heroes = sorted(hero_build_counts.items(), key=lambda x: x[1]["total_views"], reverse=True)[:5]
    lines.append("**Most viewed heroes this week:**")
    lines.append("")
    for name, stats in top_heroes:
        lines.append(f"- **{name}** ({stats['role']}) — {stats['total_views']:,} total views across {stats['builds']} builds")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "*Data sourced from [stadiumbuilds.io](https://stadiumbuilds.io). "
        "Builds ranked by trending score (hotness) which weights recency.*"
    )
    lines.append("")
    lines.append(
        "*Import forge codes in Overwatch 2 → Stadium → Import Build to try them instantly.*"
    )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate Overwatch Stadium newsletter issue")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--json", action="store_true", help="JSON output instead of Markdown")
    parser.add_argument("--builds-per-hero", type=int, default=5, help="Builds to scrape per hero")
    parser.add_argument("--top-per-role", type=int, default=3, help="Top builds per role in newsletter")
    args = parser.parse_args()

    anon_key = load_anon_key()

    print("Scraping all heroes...", file=sys.stderr)
    all_data = scrape_all_heroes(anon_key, builds_per_hero=args.builds_per_hero)

    total_builds = sum(len(h["builds"]) for h in all_data.values())
    print(f"Collected {total_builds} builds across {len(all_data)} heroes", file=sys.stderr)

    top_builds = pick_top_builds(all_data, per_role=args.top_per_role)

    if args.json:
        output = json.dumps(
            {"date": datetime.now().isoformat(), "top_builds": top_builds, "all_heroes": all_data},
            indent=2,
            default=str,
        )
    else:
        output = format_issue(all_data, top_builds)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
