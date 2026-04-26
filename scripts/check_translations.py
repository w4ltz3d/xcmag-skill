#!/usr/bin/env python3
"""
xcmag-digest: Translation quality checker.

Run after each batch of delegate_task translation to verify all articles
were properly translated. Detects articles that are still mostly English.

Usage: python3 check_translations.py [batch_size]
  batch_size: number of articles in the batch (default: check all)
"""

import json, os, sys

def check_file(path):
    """Check if a translated file has sufficient Chinese content."""
    if not os.path.exists(path):
        return 'MISSING', 0, 0, 999
    
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    
    zh = sum(1 for ch in c if '\u4e00' <= ch <= '\u9fff')
    en = sum(1 for ch in c if ch.isalpha() and 'a' <= ch.lower() <= 'z')
    ratio = en / max(zh, 1) if zh > 0 else 999
    
    if zh == 0 and en == 0:
        return 'EMPTY', zh, en, ratio
    if zh == 0:
        return 'NO_CHINESE', zh, en, ratio
    if ratio > 2.0:
        return f'LOW_QUALITY(ratio={ratio:.1f})', zh, en, ratio
    return 'PASS', zh, en, ratio

# Load article list
if os.path.exists('/tmp/articles_meta.json'):
    with open('/tmp/articles_meta.json') as f:
        meta = json.load(f)
    articles = meta['articles']
else:
    # Check all /tmp/translated_* files
    import glob
    files = sorted(glob.glob('/tmp/translated_*.html'))
    articles = [{'id': int(f.split('_')[1].split('.')[0])} for f in files]

batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else len(articles)

print(f"Checking {batch_size} articles...\n")

failed = []
for i, a in enumerate(articles[:batch_size]):
    path = f'/tmp/translated_{a["id"]}.html'
    status, zh, en, ratio = check_file(path)
    title = a.get('title', '')[:50]
    
    if status == 'PASS':
        print(f"  ✅ {a['id']:>6} | 中文={zh} 英文={en} 比例={ratio:.1f} | {title}")
    else:
        print(f"  ⚠️ {status}: {a['id']:>6} | 中文={zh} 英文={en} 比例={ratio:.1f} | {title}")
        failed.append(a['id'])

print(f"\n--- Summary ---")
print(f"Total checked: {batch_size}")
print(f"Passed: {batch_size - len(failed)}")
print(f"Failed: {len(failed)}")

if failed:
    print(f"\n❌ ARTICLES NEEDING RETRANSLATION: {failed}")
    print(f"Resubmit these via delegate_task:")
    for fid in failed:
        print(f"  - /tmp/article_{fid}.txt → /tmp/translated_{fid}.html")
else:
    print(f"\n✅ All articles passed quality check!")

print(f"\nQuality check complete.")
