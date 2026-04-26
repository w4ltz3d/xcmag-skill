#!/usr/bin/env python3
"""
xcmag-digest: Step 5 — assemble final HTML digest from translated articles.

Reads /tmp/articles_meta.json for article list + metadata.
Reads /tmp/translated_{id}.html for each article's translated content.
Outputs the complete HTML to ~/.qclaw/workspace/xcmag-issue{NNN}-full.html

Usage: python3 assemble_html.py
"""

import json, os, re
from datetime import datetime

OUTPUT_DIR = os.path.expanduser("~/.qclaw/workspace")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CSS = """  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;background:#f4f6f9;color:#222;line-height:1.85}
  .header{background:linear-gradient(135deg,#1a2e4a 0%,#2a5298 100%);color:white;padding:52px 20px;text-align:center}
  .header h1{font-size:2em;margin-bottom:8px;letter-spacing:0.04em}
  .header p{opacity:0.85;font-size:1.05em}
  .header .badge{display:inline-block;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);border-radius:30px;padding:5px 20px;font-size:0.9em;margin-top:12px}
  .container{max-width:860px;margin:0 auto;padding:24px 16px 56px}
  .intro{background:white;border-radius:10px;padding:20px 24px;margin-bottom:28px;box-shadow:0 2px 8px rgba(0,0,0,0.07)}
  .intro p{color:#555;font-size:0.95em}
  .intro strong{color:#2a5298}
  .count-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
  .count-chip{display:inline-block;background:#f0f4ff;border:1px solid #c3d4f7;border-radius:8px;padding:3px 12px;font-size:0.8em;color:#1a3a6e}
  .article{background:white;border-radius:10px;margin-bottom:32px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden}
  .article-header{padding:22px 28px 16px;border-bottom:1px solid #eee}
  .article-badge{display:inline-block;font-size:0.7em;padding:2px 10px;border-radius:20px;margin-bottom:8px;color:white}
  .badge-adv{background:#2a5298}.badge-comp{background:#e67e22}.badge-news{background:#27ae60}
  .badge-tech{background:#8e44ad}.badge-profile{background:#c0392b}.badge-tech2{background:#16a085}
  .badge-event{background:#f39c12}.badge-health{background:#2980b9}.badge-safety{background:#7f8c8d}
  .badge-weather{background:#1abc9c}.badge-travel{background:#2980b9}
  .article h2{font-size:1.25em;color:#1a2e4a;margin:0 0 6px 0;line-height:1.4}
  .article h2 small{display:block;font-size:0.63em;color:#999;font-weight:normal;margin-top:4px}
  .article-meta{font-size:0.77em;color:#bbb;margin-top:8px}
  .article-meta a{color:#2a5298;text-decoration:none}
  .article-body{padding:20px 28px 26px}
  .issue-note{background:#f0f4ff;border-left:4px solid #2a5298;padding:10px 16px;margin-bottom:16px;font-size:0.87em;color:#1a3a6e;border-radius:0 6px 6px 0}
  .article-body p{margin-bottom:13px;text-align:justify;color:#333}
  .article-body h3{color:#1a2e4a;font-size:1em;margin:20px 0 7px;padding-bottom:4px;border-bottom:2px solid #e8f0fe}
  .article-body blockquote{border-left:4px solid #2a5298;padding:9px 15px;margin:14px 0;background:#f5f8ff;border-radius:0 6px 6px 0;color:#555;font-style:italic}
  .article-body ul,.article-body ol{padding-left:22px;margin-bottom:13px;color:#333}
  .article-body li{margin-bottom:5px}
  .article-body hr{border:none;border-top:1px solid #eee;margin:20px 0}
  .article-body em{color:#666}
  .article-body strong{color:#1a2e4a}
  .article-body figure{margin:16px 0;text-align:center}
  .article-body figure img{max-width:100%;height:auto;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,0.1)}
  .article-body img{max-width:100%;height:auto}
  .article-body figure figcaption{font-size:0.78em;color:#888;margin-top:5px}
  .article-body .wp-block-image{margin:16px 0;text-align:center}
  .article-body .wp-block-image img{max-width:100%;height:auto;border-radius:6px}
  .article-body .wp-block-image figcaption{font-size:0.78em;color:#888;margin-top:5px}
  .article-body .wp-block-teapot-container{margin:0}
  .article-body .wp-block-teapot-container .container{max-width:100%}
  .article-body .wp-block-media-text{margin:16px 0}
  .article-body .wp-block-media-text img{max-width:100%;height:auto;display:block;border-radius:6px}
  .footer{text-align:center;padding:28px 20px;color:#ccc;font-size:0.8em;border-top:1px solid #eee;margin-top:16px}
  .footer p{margin:3px 0}"""

SECTIONS = {
    "FEATURES": "🗺️ 专题故事 — FEATURES",
    "IN THE CORE": "📰 人物·新闻·洞察 — IN THE CORE",
    "FLYING IQ": "💡 飞行智慧 — FLYING IQ",
    "DESIGN INSIGHT": "📷 装备评测与设计洞察 — DESIGN INSIGHT",
}

def get_section(category, badge):
    """Assign article to a section based on category."""
    if badge == 'badge-weather' or (category == 'Paragliding Techniques'):
        return 'FLYING IQ'
    if badge in ('badge-profile',):
        return 'IN THE CORE'
    if badge == 'badge-tech2':
        return 'DESIGN INSIGHT'
    if badge == 'badge-safety':
        return 'DESIGN INSIGHT'
    return 'FEATURES'

def make_article_card(title_cn, title_en, badge, badge_text, url, content, date="2026-04-20"):
    """Build an article card HTML block."""
    return f'''<div class="article">
  <div class="article-header">
    <span class="article-badge {badge}">{badge_text}</span>
    <h2>{title_cn}<small>{title_en}</small></h2>
    <div class="article-meta">🕘 {date} | <a href="{url}" target="_blank">查看原文 ↗</a></div>
  </div>
  <div class="article-body">
    <p class="issue-note">📖 本篇首发于《Cross Country Issue {issue_num}》（{month}合刊）</p>
{content}
  </div>
</div>'''

# Load metadata
with open('/tmp/articles_meta.json') as f:
    meta = json.load(f)

issue_num = meta['issue']
articles = meta['articles']
month = "2026年5-6月"  # TODO: derive from issue date

# Count by category for intro
from collections import Counter
cat_counts = Counter(a['category'] for a in articles)
cat_labels = {
    'Adventure and Inspiration': ('🗺️ 冒险故事', len([a for a in articles if a['category'] == 'Adventure and Inspiration'])),
    'Pilots and Profiles': ('👤 人物访谈', len([a for a in articles if a['category'] == 'Pilots and Profiles'])),
    'Paragliding Techniques': ('💡 技术教程', len([a for a in articles if a['category'] == 'Paragliding Techniques'])),
    'Technology Reviews': ('📷 装备评测', len([a for a in articles if a['category'] == 'Technology Reviews'])),
    'Weather': ('🌦️ 气象知识', len([a for a in articles if a['category'] == 'Weather'])),
    'Safety/Harnesses': ('🛡️ 安全标准', len([a for a in articles if a['category'] == 'Safety/Harnesses'])),
}
cat_chips = ' '.join(f'<span class="count-chip">{lbl} {cnt}篇</span>' for lbl, cnt in cat_labels.values() if cnt > 0)

# Build HTML
html_parts = [
    '<!DOCTYPE html>',
    '<html lang="zh-CN">',
    '<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">',
    f'<title>XCMag · Cross Country Issue {issue_num} 完整收录（中文翻译版）</title>',
    f'<style>{CSS}</style>',
    '</head><body>',
    f'<div class="header">',
    f'  <h1>XCMag · Cross Country Issue {issue_num}</h1>',
    f'  <p>xcmag.com 原版首发 &nbsp;|&nbsp; AI 中文翻译</p>',
    f'  <div class="badge">完整收录 &nbsp;·&nbsp; {month}合刊 &nbsp;·&nbsp; 共{len(articles)}篇文章</div>',
    f'</div>',
    f'<div class="container">',
    f'<div class="intro">',
    f'  <p>xcmag.com 最新一期杂志 <strong>Cross Country Issue {issue_num}</strong>（{month}合刊），共收录 <strong>{len(articles)}篇</strong> 文章，全部翻译为中文。</p>',
    f'  <div class="count-row">{cat_chips}</div>',
    f'</div>',
]

current_section = None
for a in articles:
    sec = get_section(a['category'], a.get('badge', 'badge-adv'))
    if sec != current_section:
        html_parts.append(
            f'<div style="background:white;border-radius:10px;padding:16px 24px;'
            f'margin:28px 0 20px;box-shadow:0 2px 8px rgba(0,0,0,.07)">'
            f'<h3 style="color:#2a5298;margin:0;font-size:1.05em">{SECTIONS[sec]}</h3></div>'
        )
        current_section = sec

    # Read translated content
    tpath = f'/tmp/translated_{a["id"]}.html'
    if os.path.exists(tpath):
        with open(tpath, 'r', encoding='utf-8') as f:
            content = f.read()
        # HTML size optimization: strip srcset/sizes (save 30-40%)
        content = re.sub(r' srcset="[^"]*"', '', content)
        content = re.sub(r' sizes="auto[^"]*"', '', content)
    else:
        content = f'<p>⚠️ 翻译文件缺失: {tpath}</p>'

    html_parts.append(make_article_card(
        a['title'], a['title'],  # will override below
        a.get('badge', 'badge-adv'),
        a.get('badge_text', '📰 文章'),
        a['url'], content
    ))

html_parts.append(
    f'<div class="footer">'
    f'  <p>📋 数据来源：xcmag.com | 整理时间：{datetime.now().strftime("%Y年%m月%d日")} | 🤖 AI 翻译</p>'
    f'  <p>全部{len(articles)}篇均首发于《Cross Country Issue {issue_num}》。</p>'
    f'</div></div></body></html>'
)

html = '\n'.join(html_parts)

# Write output
outpath = os.path.join(OUTPUT_DIR, f'xcmag-issue{issue_num}-full.html')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(html)
with open('/tmp/xcmag-issue{issue_num}-full.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Written: {outpath}")
print(f"  {len(html.encode('utf-8'))} bytes, {html.count(chr(10))} lines, {len(articles)} articles")
