#!/usr/bin/env python3
"""
Build static HTML site from newsletter markdown issues.
Generates individual issue pages + index page.
"""

import markdown
import os
import json
from datetime import datetime
from pathlib import Path

ISSUES_DIR = Path("/home/aj/newsletter/issues")
BUILD_DIR = Path("/home/aj/newsletter/site")

# HTML template with inline styles (email-safe, no external deps)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Stadium Meta Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 720px; margin: 0 auto; padding: 20px; background: #0a0a0a; color: #e0e0e0; line-height: 1.6; }}
h1 {{ color: #ff6b35; font-size: 1.8em; }}
h2 {{ color: #ff6b35; border-bottom: 1px solid #333; padding-bottom: 8px; margin-top: 2em; }}
h3 {{ color: #f7c948; }}
a {{ color: #4ea8de; }}
code {{ background: #1a1a2e; padding: 2px 6px; border-radius: 4px; font-size: 0.95em; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
th, td {{ border: 1px solid #333; padding: 8px 12px; text-align: left; }}
th {{ background: #1a1a2e; color: #ff6b35; }}
tr:nth-child(even) {{ background: #111; }}
hr {{ border: none; border-top: 1px solid #333; margin: 2em 0; }}
.nav {{ margin-bottom: 2em; padding: 12px 0; border-bottom: 2px solid #ff6b35; }}
.nav a {{ color: #ff6b35; text-decoration: none; font-weight: bold; font-size: 1.1em; }}
.subscribe {{ background: #ff6b35; color: #fff; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block; margin: 1em 0; font-weight: bold; }}
footer {{ margin-top: 3em; padding-top: 1em; border-top: 1px solid #333; color: #888; font-size: 0.85em; }}
</style>
</head>
<body>
<div class="nav"><a href="index.html">🏟️ Stadium Meta Report</a></div>
{body}
<footer>
<p>Data sourced from <a href="https://stadiumbuilds.io">stadiumbuilds.io</a>. Generated {date}.</p>
</footer>
</body>
</html>"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stadium Meta Report — Weekly Overwatch Stadium Builds</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 720px; margin: 0 auto; padding: 20px; background: #0a0a0a; color: #e0e0e0; line-height: 1.6; }}
h1 {{ color: #ff6b35; font-size: 2em; }}
h2 {{ color: #ff6b35; }}
a {{ color: #4ea8de; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.issue {{ padding: 16px; margin: 12px 0; background: #111; border-radius: 8px; border-left: 4px solid #ff6b35; }}
.issue h3 {{ margin: 0; }}
.issue .date {{ color: #888; font-size: 0.9em; }}
.issue .preview {{ color: #aaa; margin-top: 8px; font-size: 0.95em; }}
.subscribe {{ background: #ff6b35; color: #fff; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block; margin: 1em 0; font-weight: bold; }}
footer {{ margin-top: 3em; padding-top: 1em; border-top: 1px solid #333; color: #888; font-size: 0.85em; }}
</style>
</head>
<body>
<h1>🏟️ Stadium Meta Report</h1>
<p>Weekly Overwatch 2 Stadium builds — top trending picks across Tank, Damage, and Support. Every build includes a forge code for instant in-game import.</p>
<p class="subscribe" style="cursor:default;">Updated every Tuesday</p>
<h2>Archive</h2>
{issues}
<footer>
<p>Powered by <a href="https://stadiumbuilds.io">stadiumbuilds.io</a> data. Generated {date}.</p>
</footer>
</body>
</html>"""


def build_issue(md_path: Path) -> str:
    """Convert a markdown issue to HTML."""
    md_content = md_path.read_text()
    # Extract title from first line
    first_line = md_content.strip().split("\n")[0]
    title = first_line.lstrip("# ").strip()

    html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])
    return HTML_TEMPLATE.format(
        title=title, body=html_body, date=datetime.now().strftime("%Y-%m-%d %H:%M")
    )


def build_index(issue_files: list[dict]) -> str:
    """Build index page listing all issues."""
    issues_html = ""
    for issue in sorted(issue_files, key=lambda x: x["date"], reverse=True):
        issues_html += f"""<div class="issue">
<h3><a href="{issue['filename']}">{issue['title']}</a></h3>
<div class="date">{issue['date']}</div>
<div class="preview">{issue['preview']}</div>
</div>\n"""
    return INDEX_TEMPLATE.format(
        issues=issues_html, date=datetime.now().strftime("%Y-%m-%d %H:%M")
    )


def main():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    md_files = sorted(ISSUES_DIR.glob("issue_*.md"))
    if not md_files:
        print("No issue files found in", ISSUES_DIR)
        return

    issue_files = []
    for md_path in md_files:
        filename = md_path.stem + ".html"
        md_content = md_path.read_text()
        lines = md_content.strip().split("\n")

        # Extract metadata
        title = lines[0].lstrip("# ").strip() if lines else "Untitled"
        # Get first paragraph as preview
        preview_lines = []
        for line in lines[1:]:
            if line.strip() and not line.startswith("#") and not line.startswith("|"):
                preview_lines.append(line.strip())
                if len(preview_lines) >= 2:
                    break
        preview = " ".join(preview_lines)[:120] + "..." if preview_lines else ""

        # Parse date from filename: issue_2026-04-17.md
        date_str = md_path.stem.replace("issue_", "")

        # Generate HTML
        html = build_issue(md_path)
        (BUILD_DIR / filename).write_text(html)
        print(f"Built: {filename}")

        issue_files.append(
            {
                "filename": filename,
                "title": title,
                "date": date_str,
                "preview": preview,
            }
        )

    # Build index
    index_html = build_index(issue_files)
    (BUILD_DIR / "index.html").write_text(index_html)
    print(f"Built: index.html ({len(issue_files)} issues)")

    # Write manifest for deploy script
    manifest = {
        "built": datetime.now().isoformat(),
        "issues": len(issue_files),
        "files": [f["filename"] for f in issue_files] + ["index.html"],
    }
    (BUILD_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("Done.")


if __name__ == "__main__":
    main()
