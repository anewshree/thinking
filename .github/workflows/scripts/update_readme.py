"""
update_readme.py
Scans the repo for markdown articles, builds a table, and updates README.md.
Runs automatically via GitHub Actions on every push.
"""

import os
import re
import subprocess
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

README_PATH   = 'README.md'
START_MARKER  = '<!-- ARTICLES_START -->'
END_MARKER    = '<!-- ARTICLES_END -->'

# Folders to skip entirely
SKIP_DIRS  = {'.git', '.github', 'scripts', 'assets', 'images', 'node_modules'}

# Files to skip even if they're .md
SKIP_FILES = {'README.md', 'LICENSE.md', 'CONTRIBUTING.md', 'CHANGELOG.md'}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_title(filepath):
    """Pull the first # heading from a markdown file as its title."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# '):
                    return line[2:].strip()
    except Exception:
        pass
    # Fallback: prettify the filename
    name = os.path.splitext(os.path.basename(filepath))[0]
    return name.replace('-', ' ').replace('_', ' ').title()


def get_date(filepath):
    """Get the date the file was first committed to the repo."""
    try:
        result = subprocess.run(
            ['git', 'log', '--follow', '--format=%ai', '--', filepath],
            capture_output=True, text=True
        )
        lines = [l for l in result.stdout.strip().split('\n') if l]
        if lines:
            # Last line = oldest commit = when it was first published
            date_str = lines[-1].split(' ')[0]
            return datetime.strptime(date_str, '%Y-%m-%d')
    except Exception:
        pass
    return datetime.now()


def get_folder(filepath):
    """Return the top-level folder for display (e.g. /strategy)."""
    parts = filepath.replace('\\', '/').strip('/').split('/')
    if len(parts) > 1:
        return f'/{parts[0]}'
    return '/root'


def find_articles():
    """Walk the repo and collect all markdown articles."""
    articles = []

    for root, dirs, files in os.walk('.'):
        # Prune skip dirs in-place so os.walk doesn't descend into them
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith('.')
        ]

        for filename in sorted(files):
            if not filename.endswith('.md'):
                continue
            if filename in SKIP_FILES:
                continue

            # Clean up the path (remove leading ./ or .\)
            raw_path = os.path.join(root, filename)
            clean_path = raw_path.lstrip('./').lstrip('.\\')

            articles.append({
                'title':    get_title(raw_path),
                'date':     get_date(raw_path),
                'folder':   get_folder(clean_path),
                'path':     clean_path,
            })

    # Newest first
    articles.sort(key=lambda a: a['date'], reverse=True)
    return articles


def build_table(articles):
    """Render articles as a clean markdown table."""
    if not articles:
        return '_No articles yet. Watch this space._\n'

    rows = [
        '| Article | Folder | Published |',
        '|---------|--------|-----------|',
    ]

    for a in articles:
        date_str   = a['date'].strftime('%b %Y')
        title_link = f"[{a['title']}]({a['path']})"
        rows.append(f"| {title_link} | `{a['folder']}` | {date_str} |")

    count     = len(articles)
    label     = 'article' if count == 1 else 'articles'
    updated   = datetime.now().strftime('%d %b %Y')
    rows.append('')
    rows.append(f'_Last updated: {updated} · {count} {label}_')

    return '\n'.join(rows)


def update_readme(articles):
    """Splice the new article table into README between the markers."""
    if os.path.exists(README_PATH):
        with open(README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = '# thinking\n\n'

    table       = build_table(articles)
    new_block   = f'{START_MARKER}\n{table}\n{END_MARKER}'

    if START_MARKER in content and END_MARKER in content:
        # Replace existing block
        pattern = re.escape(START_MARKER) + r'.*?' + re.escape(END_MARKER)
        content = re.sub(pattern, new_block, content, flags=re.DOTALL)
    else:
        # Append a new section if markers aren't there yet
        content += f'\n\n---\n\n## 📝 Articles\n\n{new_block}\n'

    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(content)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    articles = find_articles()
    update_readme(articles)
    print(f'✅ README updated — {len(articles)} article(s) found.')
