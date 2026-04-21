---
name: xcmag-digest
description: 抓取 xcmag.com 文章、翻译为中文并生成 HTML 月刊摘要的完整工作流。当用户要求"整理 xcmag.com 文章"、"生成 XCMag 月刊"、"翻译 xcmag 文章为中文"、"抓取 xcmag" 时触发。支持：(1) 获取某时间段内所有文章；(2) 识别最新期刊号并过滤；(3) 翻译为中文；(4) 生成格式化 HTML。
---

# XCMag 文章月刊摘要

## 工作流概览

```
1. 确认期刊号 → 2. 获取文章列表 → 3. 逐篇抓取内容 → 4. 翻译为中文 → 5. 生成 HTML
```

## Step 1：确认最新期刊号

访问期刊列表页（WordPress 渲染，需用 xbrowser）：
- `https://xcmag.com/issues/`

找到最新的 `cross-country-issue-XXX` 页面 URL，提取期刊号（如 `265`）。

**备选方法**：WordPress REST API 按标签搜索：
```
GET https://xcmag.com/wp-json/wp/v2/posts?per_page=100&page=1&after=2026-03-01T00:00:00
```
在返回文章中搜索含 `"Cross Country Issue NNN"` 的文章末尾标记。

## Step 2：获取期刊文章列表

两种方法（优先方法一）：

**方法一（最准确）**：直接访问期刊目录页
```
GET https://xcmag.com/issues/cross-country-issue-{NNN}-{month-year}/
```
用 xbrowser 打开，提取页面上所有文章链接。

**方法二（API）**：用 `xcNNN` 标签过滤
```json
GET https://xcmag.com/wp-json/wp/v2/posts?tags=3244&per_page=100
  // tag 3244 = xc265，对应期刊号 265
```
期刊标签 ID 会随期刊号变化，需先查期刊页确认当前标签 ID。

**方法三（直接搜索关键词）**：在文章内容中搜索
```
GET https://xcmag.com/wp-json/wp/v2/posts?search=Cross+Country+Issue+{NNN}
```

## Step 3：逐篇抓取完整内容

对每篇文章，用 `web_fetch` 按 ID 抓取：
```
GET https://xcmag.com/wp-json/wp/v2/posts/{ID}?maxChars=25000
```

**关键判断**：文章是否属于该期刊——搜索内容中是否含：
```
"This article was first published in Cross Country Issue {NNN}"
```
不含此标记的文章（通常是独立的 Gear News）不纳入期刊摘要。

**并行抓取**：最多同时发起 5 个请求，超过需排队。

## Step 4：翻译为中文

对每篇文章的 HTML 内容：
- 使用 `write` 工具将原文写入 `/tmp/_tw_article_{id}.txt`
- 用 `qclaw-text-file` skill 的 `write_file.py` 脚本写入最终目标文件（处理 UTF-8 编码）

翻译要点：
- 人名保留英文原文
- 地名、赛事名、专业术语首次出现时附英文原文
- 保留 `<figure>` 和 `<figcaption>` 中的英文原文图片说明
- "This article was first published in Cross Country Issue NNN" 翻译为"本文章首发于《Cross Country Issue NNN》"

## Step 5：生成 HTML

使用 `qclaw-text-file` skill 的 `write_file.py` 脚本，写入 `~/.qclaw/workspace/xcmag-issue{NNN}-digest.html`。

### HTML 模板结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>XCMag · Cross Country Issue {NNN} 完整收录</title>
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;background:#f4f6f9;color:#222;line-height:1.85}
  .header{background:linear-gradient(135deg,#1a2e4a,#2a5298);color:white;padding:52px 20px;text-align:center}
  .container{max-width:860px;margin:0 auto;padding:24px 16px 56px}
  .article{background:white;border-radius:10px;margin-bottom:32px;box-shadow:0 2px 12px rgba(0,0,0,.07);overflow:hidden}
  .article-header{padding:22px 28px 16px;border-bottom:1px solid #eee}
  .article h2{font-size:1.25em;color:#1a2e4a}
  .article h2 small{display:block;font-size:.63em;color:#999;font-weight:normal;margin-top:4px}
  .article-body{padding:20px 28px 26px}
  .issue-note{background:#f0f4ff;border-left:4px solid #2a5298;padding:10px 16px;margin-bottom:16px;font-size:.87em;color:#1a3a6e;border-radius:0 6px 6px 0}
  .article-body p{margin-bottom:13px;text-align:justify;color:#333}
  .article-body h3{color:#1a2e4a;font-size:1em;margin:20px 0 7px}
  .article-body blockquote{border-left:4px solid #2a5298;padding:9px 15px;margin:14px 0;background:#f5f8ff;border-radius:0 6px 6px 0;color:#555;font-style:italic}
  .article-body ul,.article-body ol{padding-left:22px;margin-bottom:13px}
  .article-body li{margin-bottom:5px}
  .article-body hr{border:none;border-top:1px solid #eee;margin:20px 0}
  .article-body strong{color:#1a2e4a}
  .article-body figure{margin:16px 0;text-align:center}
  .article-body figure img{max-width:100%;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.1)}
  .article-body figure figcaption{font-size:.78em;color:#888;margin-top:5px}
  .article-badge{display:inline-block;font-size:.7em;padding:2px 10px;border-radius:20px;margin-bottom:8px;color:white}
  .badge-adv{background:#2a5298}.badge-comp{background:#e67e22}.badge-news{background:#27ae60}
  .badge-tech{background:#8e44ad}.badge-interview{background:#c0392b}.badge-tech2{background:#16a085}
  .badge-event{background:#f39c12}.badge-health{background:#2980b9}.badge-safety{background:#7f8c8d}
  .badge-profile{background:#2c3e50}.badge-weather{background:#1abc9c}
  .article-meta{font-size:.77em;color:#bbb;margin-top:8px}
  .article-meta a{color:#2a5298;text-decoration:none}
  .footer{text-align:center;padding:28px 20px;color:#ccc;font-size:.8em;border-top:1px solid #eee;margin-top:16px}
  .intro{background:white;border-radius:10px;padding:20px 24px;margin-bottom:28px;box-shadow:0 2px 8px rgba(0,0,0,.07)}
  .intro p{color:#555;font-size:.95em}
  .intro strong{color:#2a5298}
  .count-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
  .count-chip{display:inline-block;background:#f0f4ff;border:1px solid #c3d4f7;border-radius:8px;padding:3px 12px;font-size:.8em;color:#1a3a6e}
</style>
</head>
<body>
<div class="header">
  <h1>XCMag · Cross Country Issue {NNN}</h1>
  <p>xcmag.com 原版首发 | AI 中文翻译</p>
  <div class="badge">完整收录 · {Month Year}合刊 · 共{count}篇文章</div>
</div>
<div class="container">
<div class="intro">
  <p>xcmag.com 最新一期杂志 <strong>Cross Country Issue {NNN}</strong>（{Month Year}合刊），共收录 <strong>{count}篇</strong> 文章，全部翻译为中文。</p>
  <div class="count-row">{categoryChips}</div>
</div>
<!-- Articles go here -->
<div class="footer">
  <p>📋 数据来源：xcmag.com | 整理时间：{date} | 🤖 AI 翻译</p>
  <p>全部{count}篇均首发于《Cross Country Issue {NNN}》。</p>
</div>
</div>
</body>
</html>
```

### 文章卡片模板

```html
<div class="article">
  <div class="article-header">
    <span class="article-badge badge-{categoryClass}">{categoryLabel}</span>
    <h2>{中文标题}<small>{英文标题}</small></h2>
    <div class="article-meta">🕘 {date} | <a href="{url}" target="_blank">查看原文 ↗</a></div>
  </div>
  <div class="article-body">
    <p class="issue-note">📖 本篇首发于《Cross Country Issue {NNN}》（{Month Year}合刊）</p>
    {translatedContent}
    <p><em>本文章首发于《Cross Country Issue {NNN}》</em></p>
  </div>
</div>
```

## 分类标签映射

| 分类 | badge class | 中文标签 |
|------|------------|---------|
| Adventure and Inspiration | badge-adv | 🗺️ 冒险故事 |
| Competition News | badge-comp | 🏆 赛事新闻 |
| Gear News | badge-news | ⚙️ 装备新闻 |
| Technology Reviews | badge-tech / badge-tech2 | 📷 装备评测 |
| Pilots and Profiles | badge-profile | 👤 人物访谈 |
| Paragliding Techniques | badge-tech | 💡 技术教程 |
| Weather | badge-weather | 🌦️ 气象知识 |
| Safety/Harnesses | badge-safety | 🛡️ 安全标准 |
| News (general) | badge-news | 📰 新闻 |

## 写入文件（强制）

**禁止使用内置 write 工具直接写最终目标 HTML 文件**，必须使用 `qclaw-text-file` skill 的脚本：

```bash
python3 ~/Library/Application\ Support/QClaw/openclaw/config/skills/qclaw-text-file/scripts/write_file.py \
  --path "~/.qclaw/workspace/xcmag-issue{NNN}-digest.html" \
  --content-file "/tmp/_tw_xcmag_{NNN}.txt"
```

## 已知问题与解决

**问题：文章内容截断**
- 解决：`web_fetch` 加 `--maxChars 25000` 参数

**问题：Gear News 误归入期刊**
- 判断标准：内容中必须含 `"This article was first published in Cross Country Issue {NNN}"` 才算期刊文章
- 无此标记的 gear news 归入"网站新闻"不纳入摘要

**问题：某些文章 ID 查不到**
- 解决：改用 `?slug=article-slug-name` 搜索

## 输出文件规范

- 路径：`~/.qclaw/workspace/xcmag-issue{NNN}-digest.html`
- 命名规则：`xcmag-issue{NNN}-digest.html`
- 如果是全量月度摘要（不区分期刊）：`xcmag-{YYYY-MM}.html`
