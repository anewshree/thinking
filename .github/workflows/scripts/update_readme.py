"""
update_readme.py — scans repo for markdown articles, updates README.md
"""

import os
import re
import subprocess
import sys
from datetime import datetime

README_PATH  = "README.md"
START_MARKER = "<!-- ARTICLES_START -->"
END_MARKER   = "<!-- ARTICLES_END -->"

SKIP_DIRS  = {".git", ".github", "scripts", "assets", "images"}
SKIP_FILES = {"README.md", "LICENSE.md", "CONTRIBUTING.md", "CHANGELOG.md"}


def get_title(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip().startswith("# "):
                    return line.strip()[2:].strip()
    except Exception as e:
        print(f"  Could not read {filepath}: {e}")
    name = os.path.splitext(os.path.basename(filepath))[0]
    return name.replace("-", " ").replace("_", " ").title()


def get_date(filepath):
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%as", "--", filepath],
            capture_output=True, text=True, timeout=15
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        if lines:
            return datetime.strptime(lines[-1], "%Y-%m-%d")
    except Exception as e:
        print(f"  Could not get date for {filepath}: {e}")
    return datetime.now()


def main():
    print("Scanning repo for articles...")
    articles = []

    for root, dirs, files in os.walk("."):
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith(".")
        ]
        for filename in files:
            if not filename.endswith(".md"):
                continue
            if filename in SKIP_FILES:
                continue

            raw  = os.path.join(root, filename)
            path = raw.replace("\\", "/").lstrip("./").lstrip("/")

            title  = get_title(raw)
            date   = get_date(raw)
            parts  = path.split("/")
            folder = f"/{parts[0]}" if len(parts) > 1 else "/root"

            print(f"  + {title} | {folder} | {date.strftime('%b %Y')}")
            articles.append({
                "title":  title,
                "date":   date,
                "folder": folder,
                "path":   path,
            })

    articles.sort(key=lambda a: a["date"], reverse=True)
    print(f"Found {len(articles)} article(s).")

    # Build table
    if articles:
        rows = [
            "| Article | Folder | Published |",
            "|---------|--------|-----------|",
        ]
        for a in articles:
            rows.append(
                f"| [{a['title']}]({a['path']}) "
                f"| `{a['folder']}` "
                f"| {a['date'].strftime('%b %Y')} |"
            )
        updated = datetime.now().strftime("%d %b %Y")
        rows.append(f"\n_Last updated: {updated} · {len(articles)} article(s)_")
        table = "\n".join(rows)
    else:
        table = "_No articles yet. Watch this space._"

    new_block = f"{START_MARKER}\n{table}\n{END_MARKER}"

    # Read README
    if os.path.exists(README_PATH):
        with open(README_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        print("README.md not found — creating one.")
        content = "# thinking\n\n"

    # Splice in new block
    if START_MARKER in content and END_MARKER in content:
        pattern = re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER)
        content = re.sub(pattern, new_block, content, flags=re.DOTALL)
        print("Updated existing article section.")
    else:
        content += f"\n\n## 📝 Articles\n\n{new_block}\n"
        print("Added new article section.")

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
