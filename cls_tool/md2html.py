"""
Convert CLS morning report markdown to a beautifully formatted HTML page
that can be opened directly in any browser.
"""

import re
import sys
import os


CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif;
    background: #f4f5f7;
    color: #1a1a2e;
    line-height: 1.6;
}
.container { max-width: 1200px; margin: 0 auto; padding: 30px 24px; }

/* Header */
.header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: #fff; padding: 30px 36px; border-radius: 8px; margin-bottom: 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
}
.header h1 { font-size: 26px; font-weight: 700; margin-bottom: 8px; letter-spacing: 1px; }
.header .meta { font-size: 13px; opacity: 0.85; margin-top: 10px; }
.header .meta span { margin-right: 20px; }
.header .verdict {
    margin-top: 18px; padding: 14px 18px; background: rgba(255,255,255,0.1);
    border-left: 3px solid #e94560; border-radius: 0 6px 6px 0;
    font-size: 14px; line-height: 1.7;
}

/* Core verdict banner */
.verdict-banner {
    background: #fff5f5; padding: 16px 20px; border-radius: 8px;
    border-left: 4px solid #e94560; margin: 12px 0 20px;
    font-size: 18px; line-height: 1.8; color: #e94560;
    box-shadow: 0 1px 6px rgba(233,69,96,0.1);
}

/* Verdict section (## 核心判断) */
.verdict-section {
    background: #fff; border-radius: 8px; padding: 24px 28px;
    margin: 16px 0 24px; box-shadow: 0 2px 16px rgba(0,0,0,0.06);
    border-top: 4px solid #e94560;
}
.verdict-section .section-title {
    border-bottom: none; margin-top: 0; margin-bottom: 14px;
    color: #e94560; font-size: 22px;
}
.verdict-content p { font-size: 15px; line-height: 1.8; margin: 6px 0; }
.verdict-content strong { color: #0f3460; }
.verdict-content ul, .verdict-content ol { margin: 8px 0 8px 20px; font-size: 15px; line-height: 1.7; }
.verdict-content li { margin-bottom: 4px; }

/* Section titles */
.section-title {
    font-size: 20px; font-weight: 700; color: #0f3460;
    border-bottom: 3px solid #e94560; padding-bottom: 8px;
    margin: 28px 0 16px;
}

/* Ranking table */
.rank-table {
    width: 100%; border-collapse: collapse; margin: 16px 0 24px;
    background: #fff; border-radius: 8px; overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06); font-size: 14px;
}
.rank-table thead th {
    background: #0f3460; color: #fff; padding: 10px 10px;
    font-weight: 600; text-align: center; font-size: 13px;
}
.rank-table thead th.th-important {
    color: #ff6b6b; font-size: 15px; font-weight: 800;
}
.rank-table tbody td {
    padding: 8px 10px; border-bottom: 1px solid #eee;
    text-align: center; vertical-align: middle;
}
.rank-table tbody tr:hover { background: #f8f9ff; }
.rank-table .rank-num { font-weight: 700; color: #e94560; font-size: 16px; }
.rank-table .title-col { text-align: left; font-weight: 500; }
.rank-table .impact-col { text-align: left; font-size: 14px; color: #444; max-width: 400px; }
.rank-table .stars { color: #f5a623; white-space: nowrap; font-size: 14px; letter-spacing: 1px; }

/* Analysis card */
.analysis-card {
    background: #fff; border-radius: 8px; padding: 22px 28px;
    margin: 16px 0; box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    border-top: 4px solid #e94560;
}
.analysis-card .card-title {
    font-size: 17px; font-weight: 700; color: #1a1a2e; margin-bottom: 12px;
}
.analysis-card .card-level {
    display: inline-block; padding: 3px 10px; border-radius: 3px;
    font-size: 16px; font-weight: 800; color: #e94560;
    background: #fff5f5; border: 1px solid #e94560;
    margin-right: 4px;
}
.analysis-card .card-meta {
    display: flex; align-items: center; gap: 16px; margin-bottom: 10px;
    font-size: 13px; color: #777;
    line-height: 1.4;
}
.analysis-card .card-meta-inline {
    display: inline-block; margin-right: 18px; margin-bottom: 8px;
    font-size: 13px; color: #777; line-height: 1.4;
}
.analysis-card .card-meta .stars { color: #f5a623; font-size: 16px; }
.analysis-card .logic {
    background: #fff8f0; padding: 12px 16px; border-radius: 6px;
    font-size: 14px; color: #8b4513; margin-bottom: 14px;
    border-left: 3px solid #f5a623;
}
.analysis-card h4 {
    font-size: 15px; font-weight: 700; color: #0f3460;
    margin: 10px 0 4px; padding-bottom: 2px; border-bottom: 1px dashed #ddd;
    line-height: 1.4;
}
.analysis-card h4.perspective-domestic {
    color: #c0392b; border-bottom-color: #e94560; font-size: 17px;
}
.analysis-card h4.perspective-intl {
    color: #0e8c6a; border-bottom-color: #0e8c6a; font-size: 17px;
}
/* When a perspective h4 is immediately followed by another h4, make it inline */
.analysis-card h4.perspective-domestic + h4,
.analysis-card h4.perspective-intl + h4 {
    margin-top: 0; padding-top: 0; border-top: none;
}
.analysis-card h4.perspective-domestic + h4::before {
    content: '\25B8  ';
    color: #c0392b;
}
.analysis-card h4.perspective-intl + h4::before {
    content: '\25B8  ';
    color: #0e8c6a;
}
.analysis-card ul { margin: 4px 0 8px 18px; font-size: 14px; line-height: 1.5; }
.analysis-card ul li { margin-bottom: 2px; }
.bull { color: #e94560; font-weight: 600; }
.bear { color: #2ecc71; font-weight: 600; }

/* Sector tags */
.tag { display: inline-block; padding: 2px 8px; border-radius: 3px;
    font-size: 11px; font-weight: 600; margin-right: 4px; }
.tag-a { background: #ffe0e0; color: #c0392b; }
.tag-b { background: #fff3cd; color: #856404; }
.tag-c { background: #e8e8e8; color: #555; }

/* Emotion section */
.emotion-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 12px; margin: 16px 0;
}
.emotion-item {
    background: #fff; padding: 18px 20px; border-radius: 8px;
    box-shadow: 0 1px 8px rgba(0,0,0,0.04);
}
.emotion-item .label { font-size: 11px; color: #999; text-transform: uppercase; }
.emotion-item .value { font-size: 16px; font-weight: 700; color: #0f3460; margin-top: 4px; }

/* Risk list */
.risk-list { list-style: none; }
.risk-list li {
    padding: 10px 14px; margin: 6px 0; background: #fff5f5;
    border-left: 3px solid #e94560; border-radius: 0 6px 6px 0;
    font-size: 13px;
}
.risk-list li::before { content: '⚠ '; }

.risk-item {
    padding: 6px 12px; margin: 3px 0; background: #fff5f5;
    border-left: 3px solid #e94560; border-radius: 0 6px 6px 0;
    font-size: 13px; line-height: 1.5;
}
.risk-heading {
    font-size: 15px; font-weight: 800; color: #e94560;
    margin: 10px 0 4px;
}

/* Full telegram table */
.telegram-table {
    width: 100%; border-collapse: collapse; font-size: 12px;
    background: #fff; border-radius: 6px; overflow: hidden;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}
.telegram-table thead th {
    background: #16213e; color: #fff; padding: 10px 8px;
    font-weight: 500; font-size: 12px;
}
.telegram-table thead th:first-child { width: 42px; }
.telegram-table thead th:nth-child(2) { width: 48px; }
.telegram-table thead th:nth-child(3) { width: 38px; }
.telegram-table thead th:nth-child(4) { width: 48px; }
.telegram-table thead th:nth-child(5) { width: 48px; }
.telegram-table thead th:last-child { width: auto; }
.telegram-table tbody td {
    padding: 5px 8px; border-bottom: 1px solid #f0f0f0;
    vertical-align: middle;
}
.telegram-table tbody td:first-child,
.telegram-table tbody td:nth-child(2),
.telegram-table tbody td:nth-child(3),
.telegram-table tbody td:nth-child(4),
.telegram-table tbody td:nth-child(5) {
    text-align: center;
}
.telegram-table tbody td:last-child {
    text-align: left; white-space: normal; word-break: break-all;
}
.telegram-table tbody tr:nth-child(even) { background: #fafafa; }
.telegram-table .lv-S { background: #c0392b; color: #fff; padding: 1px 5px; border-radius: 2px; font-size: 10px; }
.telegram-table .lv-A { background: #e74c3c; color: #fff; padding: 1px 5px; border-radius: 2px; font-size: 10px; }
.telegram-table .lv-B { background: #f39c12; color: #fff; padding: 1px 5px; border-radius: 2px; font-size: 10px; }
.telegram-table .lv-C { background: #bbb; color: #fff; padding: 1px 5px; border-radius: 2px; font-size: 10px; }

.footer {
    text-align: center; margin-top: 40px; padding: 20px;
    color: #999; font-size: 12px; border-top: 1px solid #eee;
}
"""


def md_to_html(md_path: str, html_path: str = None):
    with open(md_path, 'r', encoding='utf-8') as f:
        md = f.read()

    if html_path is None:
        html_path = md_path.replace('.md', '.html')

    body = _convert_md_body(md, _extract_date(md))

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CLS 早报</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="container">
{body}
<div class="footer">Generated by CLS Daily Summary Tool &copy; {_extract_date(md)}</div>
</div>
</body>
</html>"""

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return html_path


def _extract_date(md: str) -> str:
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', md)
    if m:
        return f'{m.group(1)}年{m.group(2)}月{m.group(3)}日'
    return ''


def _convert_md_body(md: str, date_str: str = '') -> str:
    """Convert markdown to HTML with custom styling."""
    lines = md.split('\n')
    out = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Empty line
        if not line:
            out.append('')
            i += 1
            continue

        # Horizontal rule
        if line.strip() == '---':
            out.append('<hr style="border:none;border-top:1px solid #ddd;margin:24px 0">')
            i += 1
            continue

        # H1 - report title
        m = re.match(r'^#\s+(.+)', line)
        if m:
            out.append(f'<div class="header"><h1>{_fmt_text(m.group(1))}</h1></div>')
            i += 1
            continue

        # Analysis card items (### N. [...] ...) — must be checked before H3
        m = re.match(r'^###\s+(\d+)\.\s+\[(.+?)\]\s+(.+)', line)
        if m:
            num, level, title = m.groups()
            level_clean = level.rstrip('级')
            # Start collecting this card
            card_lines = []
            i += 1
            while i < len(lines) and not (re.match(r'^###\s+(\d+)\.\s+\[(.+?)\]\s+', lines[i].rstrip()) or (lines[i].rstrip().startswith('### ') and not re.match(r'^###\s+\d+', lines[i].rstrip())) or lines[i].rstrip().startswith('## ')):
                card_lines.append(lines[i].rstrip())
                i += 1

            out.append('<div class="analysis-card">')
            out.append(f'<div class="card-title">{num}. <span class="card-level">{level_clean}级</span> {_fmt_text(title)}</div>')

            body_text = '\n'.join(card_lines)
            out.append(_parse_card_body(body_text, date_str))
            out.append('</div>')
            continue

        # H3 in bold - section header (must have ** wrapping)
        m = re.match(r'^###\s+\*\*(.+?)\*\*\s*$', line)
        if m:
            title = m.group(1).strip()
            if '核心判断' in title or '核心观点' in title:
                out.append(f'<div class="header"><div class="verdict"><strong>核心判断：</strong>{_fmt_text(title)}</div></div>')
            else:
                out.append(f'<h2 class="section-title">{_fmt_text(title)}</h2>')
            i += 1
            continue

        # H3 without bold (e.g. ### 一、重要性排序总览)
        m = re.match(r'^###\s+(.+)', line)
        if m:
            title = m.group(1).strip()
            out.append(f'<h2 class="section-title">{_fmt_text(title)}</h2>')
            i += 1
            continue

        # H2
        m = re.match(r'^##\s+(.+)', line)
        if m:
            title = m.group(1).strip()
            if '核心判断' in title or '核心观点' in title:
                # Render core judgment as a prominent verdict section
                out.append(f'<div class="verdict-section">')
                out.append(f'<h2 class="section-title" style="margin-top:0">{_fmt_text(title)}</h2>')
                out.append(f'<div class="verdict-content">')
                i += 1
                verdict_lines = []
                while i < len(lines):
                    nxt = lines[i].rstrip()
                    if re.match(r'^##\s+', nxt) or re.match(r'^#\s+', nxt):
                        break
                    if nxt == '---':
                        i += 1
                        continue
                    verdict_lines.append(nxt)
                    i += 1
                # Render collected verdict content
                verdict_text = '\n'.join(verdict_lines)
                out.append(_render_verdict_content(verdict_text))
                out.append('</div></div>')
            else:
                out.append(f'<h2 class="section-title">{_fmt_text(title)}</h2>')
                i += 1
            continue

        # Tables
        if line.startswith('|') and not line.startswith('|---'):
            table_lines = []
            while i < len(lines) and lines[i].rstrip().startswith('|'):
                table_lines.append(lines[i].rstrip())
                i += 1

            # Skip header separator (|---|)
            data_lines = []
            for tl in table_lines:
                if not re.match(r'^\|[\s\-|]+\|$', tl):
                    data_lines.append(tl)

            if len(data_lines) >= 2:
                # Determine if it's a ranking table or telegram table
                is_rank_table = any('重要度' in data_lines[0] or '等级' in data_lines[0] for _ in [1])
                if is_rank_table and '核心影响' in data_lines[0]:
                    tbl_class = 'rank-table'
                elif '摘要' in data_lines[0] or '内容' in data_lines[0]:
                    tbl_class = 'telegram-table'
                else:
                    tbl_class = 'rank-table'

                out.append(f'<table class="{tbl_class}">')

                # Header
                cells = [c.strip() for c in data_lines[0].split('|') if c.strip()]
                out.append('<thead><tr>')
                for c in cells:
                    cls = 'th-important' if '核心影响' in c else ''
                    out.append(f'<th class="{cls}">{_fmt_text(c)}</th>')
                out.append('</tr></thead>')

                # Body
                out.append('<tbody>')
                is_telegram = tbl_class == 'telegram-table'
                for dl in data_lines[1:]:
                    cells = [c.strip() for c in dl.split('|') if c.strip()]
                    if not cells:
                        continue
                    out.append('<tr>')
                    for ci, c in enumerate(cells):
                        c_clean = _fmt_text(c)
                        if ci == 0:
                            c = f'<span class="rank-num">{c_clean}</span>'
                        elif ci == 4 and '★' in c:
                            c = f'<span class="stars">{c_clean}</span>'
                        elif 'S' in c and len(c) <= 2:
                            c = f'<span class="tag tag-a">{c_clean}</span>'
                        elif 'A' in c and len(c) <= 2:
                            c = f'<span class="tag tag-b">{c_clean}</span>'
                        elif 'B' in c and len(c) <= 2:
                            c = f'<span class="tag tag-b">{c_clean}</span>'
                        elif 'C' in c and len(c) <= 2:
                            c = f'<span class="tag tag-c">{c_clean}</span>'
                        else:
                            c = c_clean
                        if is_telegram:
                            cls = 'content-col' if ci == 5 else ''
                        else:
                            cls = 'title-col' if ci == 3 else ('impact-col' if ci == 5 else '')
                        out.append(f'<td class="{cls}">{c}</td>')
                    out.append('</tr>')
                out.append('</tbody></table>')
            continue

        # Emotion section items (skip risk lines which have their own handler)
        m = re.match(r'^-\s+\*\*(.+?)\*\*:\s*(.+)', line)
        if m:
            label, value = m.groups()
            if '风险提示' not in label:
                out.append(f'<div class="emotion-item"><span class="label">{label}</span><div class="value">{_fmt_text(value)}</div></div>')
                i += 1
                continue

        # Indented numbered risk items:   1. **xxx**: ... or 1. **xxx**：... (before bold handler)
        m = re.match(r'^(\s+)(\d+)\.\s+\*\*(.+?)\*\*[：:]\s*(.+)', line)
        if m:
            indent, num, label, value = m.groups()
            out.append(f'<p class="risk-item"><strong>{num}. {label}：</strong>{_fmt_text(value)}</p>')
            i += 1
            continue

        # List items (must be before bold handler to catch - **risk提示** etc.)
        if line.strip().startswith('- '):
            text = _fmt_text(line.strip()[2:])
            if '风险提示' in text:
                out.append(f'<h4 class="risk-heading">{text}</h4>')
            else:
                out.append(f'<li style="font-size:13px;margin:2px 0">{text}</li>')
            i += 1
            continue

        # Regular bold text
        if '**' in line:
            line = _fmt_text(line)
            if '核心判断' in line:
                line = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#c0392b;font-size:22px;">\1</strong>', line)
                out.append(f'<div class="verdict-banner">{line}</div>')
            else:
                line = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#0f3460;">\1</strong>', line)
                out.append(f'<p style="margin:4px 0;font-size:13px">{line}</p>')
            i += 1
            continue

        # Regular text
        text = _fmt_text(line)
        if text:
            out.append(f'<p style="margin:4px 0;font-size:13px">{text}</p>')
        i += 1

    return '\n'.join(out)


def _parse_card_body(text: str, date_str: str) -> str:
    """Parse the body of an analysis card into styled HTML."""
    raw = []
    stars_val = None
    time_val = None

    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # - **重要程度**: ★★★★★
        m = re.match(r'^-\s+\*\*重要程度\*\*:\s*(.+)', line)
        if m:
            stars_val = _fmt_text(m.group(1))
            continue

        # - **时间**: ...
        m = re.match(r'^-\s+\*\*时间\*\*:\s*(.+)', line)
        if m:
            time_val = m.group(1)
            continue

        # - **核心逻辑**: ...
        m = re.match(r'^-\s+\*\*核心逻辑\*\*:\s*(.+)', line)
        if m:
            raw.append(f'<div class="logic">{_fmt_text(m.group(1))}</div>')
            continue

        # - **国内视角**: or - **国际视角**:
        m = re.match(r'^-\s+\*\*(国内视角|国际视角)\*\*:\s*(.+)', line)
        if m:
            label = m.group(1)
            content = _fmt_text(m.group(2))
            cls = 'perspective-domestic' if '国内' in label else 'perspective-intl'
            raw.append(f'<h4 class="{cls}">{label}</h4>')
            raw.append(f'<p style="font-size:14px;margin:2px 0 6px 16px;line-height:1.5">{content}</p>')
            continue

        # - **国内视角**: or - **国际视角**: (empty, content follows on subsequent lines)
        m = re.match(r'^-\s+\*\*(国内视角|国际视角)\*\*:\s*$', line)
        if m:
            label = m.group(1)
            cls = 'perspective-domestic' if '国内' in label else 'perspective-intl'
            raw.append(f'<h4 class="{cls}">{label}</h4>')
            continue

        # - **XXX**: ...
        m = re.match(r'^-\s+\*\*(.+?)\*\*:\s*(.+)', line)
        if m:
            label, value = m.groups()
            raw.append(f'<h4>{label}</h4><p style="font-size:14px;margin:2px 0 6px 16px;line-height:1.5">{_fmt_text(value)}</p>')
            continue

        # Sub-list items:   - xxx
        if line.startswith('  - ') or line.startswith('  * '):
            text = _fmt_text(line.strip().lstrip('-* '))
            raw.append(f'<li style="font-size:13px;margin:1px 0 1px 20px;line-height:1.5">{text}</li>')
            continue

        # Numbered items:   1. **xxx**: ...
        m = re.match(r'^\s+(\d+)\.\s+\*\*(.+?)\*\*:\s*(.+)', line)
        if m:
            num, label, value = m.groups()
            raw.append(f'<p style="font-size:14px;margin:3px 0 3px 16px;line-height:1.5"><strong>{num}. {label}：</strong>{_fmt_text(value)}</p>')
            continue

        # Default paragraph
        if line and len(line) > 1:
            raw.append(f'<p style="font-size:14px;margin:2px 0;line-height:1.5">{_fmt_text(line)}</p>')

    # Build meta line: stars first, then time with year-month-day
    meta_parts = []
    if stars_val:
        meta_parts.append(f'<span class="stars">{stars_val}</span>')
    if time_val:
        # time_val is like "21:23", prepend date
        full_time = f'{date_str} {time_val}' if date_str else time_val
        meta_parts.append(f'<span>⏰ {full_time}</span>')
    if meta_parts:
        meta_line = '<div class="card-meta">' + ' '.join(meta_parts) + '</div>'
        raw.insert(0, meta_line)

    return '\n'.join(raw)


def _render_verdict_content(text: str) -> str:
    """Render the content inside a verdict section."""
    lines = text.split('\n')
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Bold text
        if '**' in line:
            line = _fmt_text(line)
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            out.append(f'<p>{line}</p>')
        # List items
        elif re.match(r'^[\-\*\d+\.]\s', line):
            tag = 'ol' if re.match(r'^\d+', line) else 'ul'
            items = [line]
            # Single list item per line
            text_clean = re.sub(r'^[\-\*\d+\.]\s+', '', line)
            text_fmt = _fmt_text(text_clean)
            text_fmt = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text_fmt)
            out.append(f'<li>{text_fmt}</li>')
        else:
            out.append(f'<p>{_fmt_text(line)}</p>')

    # Wrap consecutive <li> items in <ul>
    result = []
    i = 0
    while i < len(out):
        if out[i].startswith('<li>'):
            result.append('<ul>')
            while i < len(out) and out[i].startswith('<li>'):
                result.append(out[i])
                i += 1
            result.append('</ul>')
        else:
            result.append(out[i])
            i += 1
    return '\n'.join(result)


def _fmt_text(text: str) -> str:
    """Format text for HTML output."""
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code style="background:#f0f0f0;padding:1px 4px;border-radius:2px">\1</code>', text)
    return text


def main():
    if len(sys.argv) >= 2:
        md_path = sys.argv[1]
    else:
        md_path = 'outputs/CLS_早报_20260520.md'

    if len(sys.argv) >= 3:
        html_path = sys.argv[2]
    else:
        html_path = md_path.replace('.md', '.html')

    out = md_to_html(md_path, html_path)
    print(f'HTML created: {out}')
    print(f'Size: {os.path.getsize(out)} bytes')
    print('Open in browser: file:///' + os.path.abspath(out).replace('\\', '/'))


if __name__ == '__main__':
    main()
