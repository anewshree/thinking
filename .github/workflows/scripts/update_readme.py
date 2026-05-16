"""
update_readme.py
Scans the repo for markdown articles, builds a table, updates README.md.
Runs automatically via GitHub Actions on every push.
"""

import os
import re
import subprocess
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

README_PATH  = "README.md"
START_MARKER = "<!-- ARTICLES_START -->"
END_MARKER   = "<!-- ARTICLES_END -->"

SKIP_DIRS  = {".git", ".github", "scripts", "assets", "images", "node_modules"}
SKIP_FILES = {"README.md", "LICENSE.md", "CONTRIBUTING.md", "CHANGELOG.md"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_title(filepath):
    """Pull the first # heading from a markdown file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# "):
                    return line[2:].strip()
    except Exception as e:
        print(f"  ⚠️  Could not read {filepath}: {e}")

    # Fallback: prettify filename
    name = os.path.splitext(os.path.basename(filepath))[0]
    return name.replace("-", " ").replace("_", " ").title()


def get_date(filepath):
    """Get the first commit date for a file via git log."""
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%ai", "--", filepath],
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        if lines:
            date_str = lines[-1].split(" ")[0]  # YYYY-MM-DD
            return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception as e:
        print(f"  ⚠️  Could not get date for {filepath}: {e}")

    return datetime.now()


def get_folder(filepath):
    """Return the top-level folder name e.g. /strategy"""
    parts = filepath.replace("\\", "/").strip("/").split("/")
    return f"/{parts[0]}" if len(parts) > 1 else "/root"


def clean_path(raw):
    """Normalise a path like ./strategy/file.md → strategy/file.md"""
    return raw.replace("\\", "/").lstrip("./").lstrip("/")


# ── Scanner ───────────────────────────────────────────────────────────────────

def find_articles():
    articles = []

    for root, dirs, files in os.walk("."):
        # Skip unwanted directories
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith(".")
        ]

        for filename in files:
            if not filename.endswith(".md"):
                continue
            if filename in SKIP_FILES:
                continue

            raw_path = os.path.join(root, filename)
            path     = clean_path(raw_path)

            title  = get_title(raw_path)
            date   = get_date(raw_path)
            folder = get_folder(path)

            print(f"  📄 Found: {path} | {title} | {date.strftime('%b %Y')}")

            articles.append({
                "title":  title,
                "date":   date,
                "folder": folder,
                "path":   path,
            })

    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


# ── Table builder ─────────────────────────────────────────────────────────────

def build_table(articles):
    if not articles:
        return "_No articles yet. Watch this space._\n"

    rows = [
        "| Article | Folder | Published |",
        "|---------|--------|-----------|",
    ]

    for a in articles:
        date_str   = a["date"].strftime("%b %Y")
        title_link = f"[{a['title']}]({a['path']})"
        rows.append(f"| {title_link} | `{a['folder']}` | {date_str} |")

    count   = len(articles)
    label   = "article" if count == 1 else "articles"
    updated = datetime.now().strftime("%d %b %Y")
    rows.append("")
    rows.append(f"_Last updated: {updated} · {count} {label}_")

    return "\n".join(rows)


# ── README updater ────────────────────────────────────────────────────────────

def update_readme(articles):
    # Read existing README
    if os.path.exists(README_PATH):
        with open(README_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        print("  ⚠️  README.md not found — creating a basic one.")
        content = "# thinking\n\n"

    table     = build_table(articles)
    new_block = f"{START_MARKER}\n{table}\n{END_MARKER}"

    if START_MARKER in content and END_MARKER in content:
        pattern = re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER)
        content = re.sub(pattern, new_block, content, flags=re.DOTALL)
        print("  ✅ Updated existing article section in README.")
    else:
        content += f"\n\n---\n\n## 📝 Articles\n\n{new_block}\n"
        print("  ✅ Added new article section to README.")

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n🔍 Scanning repo for articles...")
    articles = find_articles()
    print(f"\n📊 Total found: {len(articles)} article(s)")
    print("\n📝 Updating README...")
    update_readme(articles)
    print("\n✅ Done.\n")


if __name__ == "__main__":
    main()
