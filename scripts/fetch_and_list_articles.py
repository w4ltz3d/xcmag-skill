#!/usr/bin/env python3
"""
xcmag-digest: Step 1-3 combined — discover issue, filter articles, fetch content.

Usage: Set ISSUE_DATE at the top, then run directly.
Output: /tmp/articles_meta.json with issue number + article list
        /tmp/article_{id}.txt with each article's rendered HTML

Requires: curl, python3
"""

import json, re, os, sys
from datetime import datetime

# === CONFIG: Change this each run ===
ISSUE_DATE = "2026-04-20"  # The publication date of the latest issue
# ====================================

def run_cmd(cmd, timeout=20):
    """Run a shell command and return stdout."""
    import subprocess
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {cmd[:60]}...")
        return ""

def classify(url):
    """Infer article category from URL path."""
    if '/weather/' in url: return 'Weather'
    if '/pilots-and-profiles/' in url: return 'Pilots and Profiles'
    if '/paragliding-techniques' in url: return 'Paragliding Techniques'
    if '/design-insights/' in url or '/gear-guide/' in url: return 'Technology Reviews'
    return 'Adventure and Inspiration'

CATEGORY_META = {
    'Weather': ('badge-weather', '🌦️ 气象知识'),
    'Pilots and Profiles': ('badge-profile', '👤 人物访谈'),
    'Paragliding Techniques': ('badge-tech', '💡 技术教程'),
    'Technology Reviews': ('badge-tech2', '📷 装备评测'),
    'Adventure and Inspiration': ('badge-adv', '🗺️ 冒险故事'),
}

# === Step 1-2: Fetch and filter ===
print(f"Fetching posts since {ISSUE_DATE}...")
data = run_cmd(f"curl -s 'https://xcmag.com/wp-json/wp/v2/posts?per_page=100&page=1&after={ISSUE_DATE}T00:00:00'")
if not data:
    print("ERROR: No data received from API")
    sys.exit(1)

with open('/tmp/posts.json', 'w') as f:
    f.write(data)

posts = json.loads(data)

# Find the latest issue number
issue_num = None
issue_page_id = None
for p in posts:
    full = p['content']['rendered'] + p['excerpt']['rendered']
    m = re.search(r'Issue\s*(\d+)', full)
    if m:
        n = int(m.group(1))
        if issue_num is None or n > issue_num:
            issue_num = n

# Find the issue page itself (to exclude it)
for p in posts:
    if f'Cross Country Issue {issue_num}:' in p['title']['rendered'] or f'Cross Country Issue {issue_num}:' in p['title']['rendered'].replace('&nbsp;', ' '):
        issue_page_id = p['id']
        break

if not issue_num:
    print("ERROR: Could not find issue number in posts")
    sys.exit(1)

# Filter articles
articles = []
issue_ids = set()
for p in posts:
    full = p['content']['rendered'] + p['excerpt']['rendered']
    if f'Issue {issue_num}' not in full:
        continue
    if p['id'] == issue_page_id:
        continue
    link = p['link']
    cat = classify(link)
    a = {
        'id': p['id'],
        'title': p['title']['rendered'],
        'link': link,
        'url': link,
        'slug': p['slug'],
        'category': cat,
        'badge': CATEGORY_META[cat][0],
        'badge_text': CATEGORY_META[cat][1],
    }
    articles.append(a)

print(f"\nIssue {issue_num}: {len(articles)} articles\n")

# === Step 3: Fetch content ===
for i, a in enumerate(articles, 1):
    print(f"  [{i}/{len(articles)}] Fetching {a['id']} - {a['title'][:50]}...")
    raw = run_cmd(f"curl -s 'https://xcmag.com/wp-json/wp/v2/posts/{a['id']}' > /tmp/raw_{a['id']}.json", timeout=20)
    if not raw and not os.path.exists(f'/tmp/raw_{a['id']}.json'):
        print(f"  ⚠ FAILED: {a['id']}")
        continue
    try:
        with open(f'/tmp/raw_{a['id']}.json') as f:
            data = json.loads(f.read())
        content = data.get('content', {}).get('rendered', '')
        with open(f'/tmp/article_{a["id"]}.txt', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"    OK: {len(content)} chars")
    except Exception as e:
        print(f"  ⚠ ERROR: {e}")

# Save metadata for downstream steps
meta = {'issue': issue_num, 'articles': articles, 'fetched_at': datetime.now().isoformat()}
with open('/tmp/articles_meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"\nDone. All data saved.")
print(f"  Metadata: /tmp/articles_meta.json")
print(f"  Articles: {len(articles)} files at /tmp/article_{{id}}.txt")
