"""
Normalize AI-generated markdown to consistent structure before HTML conversion.
Handles the 3 known AI output variants:
  - Variant A: Missing H1, core judgment as bold text, H3 sections
  - Variant B: Bold H3 headers (### **...**), missing H1
  - Variant C: Mostly correct, but emotion section uses H3/H4 subsections
"""

import re


def normalize(md_text: str, date_str: str = "", weekday_str: str = "", trading_note: str = "") -> str:
    """Normalize markdown to consistent format. Returns normalized text."""
    text = md_text.strip()

    # ── 1. Strip fluff preamble ──
    text = _strip_preamble(text)

    # ── 2. Ensure H1 title ──
    text = _ensure_h1(text, date_str, weekday_str, trading_note)

    # ── 3. Normalize "核心判断" to ## 核心判断 ──
    text = _normalize_core_judgment(text)

    # ── 4. Normalize section headers: ### 一、 → ## 一、 (handle bold variants too) ──
    text = _normalize_section_headers(text)

    # ── 5. Strip 三、市场情绪与策略 section if AI still outputs it ──
    text = _strip_emotion_section(text)

    # ── 6. Clean up stray horizontal rules before H2s ──
    text = _cleanup_hr(text)

    # ── 7. Validate telegraph table (flag missing table) ──
    text = _validate_telegraph_table(text)

    return text


def _strip_preamble(text: str) -> str:
    """Remove AI fluff preamble like '好的，作为顶级A股策略分析师...'"""
    # Look for the first meaningful heading or core judgment
    markers = [
        r'^#\s+每日早报',
        r'^#\s+CLS',
        r'^\*\*核心判断',
        r'^##\s+核心判断',
        r'^###\s+\*\*核心判断',
        r'^###\s+核心判断',
        r'^核心判断',
    ]
    earliest = len(text)
    for marker in markers:
        m = re.search(marker, text, re.MULTILINE)
        if m and m.start() < earliest:
            earliest = m.start()

    if earliest > 0 and earliest < len(text):
        # Also check for a --- separator just before the marker
        pre = text[:earliest].rstrip()
        if pre.endswith('---'):
            earliest = earliest - 4
            if earliest < 0:
                earliest = 0
        text = text[earliest:].strip()

    return text


def _ensure_h1(text: str, date_str: str, weekday_str: str, trading_note: str) -> str:
    """Ensure there's exactly one H1 title at the top."""
    h1 = f"# 每日早报深度分析：{date_str}（{weekday_str}）{trading_note}"

    # Check if H1 already exists
    existing_h1 = re.match(r'^#\s+.*', text)
    if existing_h1:
        # Replace existing H1
        text = re.sub(r'^#\s+.*(\n|$)', h1 + '\n', text, count=1)
    else:
        # Prepend H1
        text = h1 + '\n\n' + text

    return text


def _normalize_core_judgment(text: str) -> str:
    """Normalize core judgment to ## 核心判断 format, stripping duplicate labels."""
    patterns = [
        # ### **核心判断（写在报告最前面）** → ## 核心判断
        (r'^###\s+\*\*核心判断[（(][^)）]*[)）]\*\*\s*$', '## 核心判断'),
        # ### **核心判断** → ## 核心判断
        (r'^###\s+\*\*核心判断\*\*\s*$', '## 核心判断'),
        # ### 核心判断（...） → ## 核心判断
        (r'^###\s+核心判断[（(][^)）]*[)）]\s*$', '## 核心判断'),
        # ### 核心判断 → ## 核心判断
        (r'^###\s+核心判断\s*$', '## 核心判断'),
        # 核心判断\n--- → ## 核心判断
        (r'^核心判断\s*$', '## 核心判断'),
    ]

    for pattern, replacement in patterns:
        text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
        if count > 0:
            return text

    # Bold-text variant: **核心判断：** content or **核心判断:** content
    # Convert to ## 核心判断 + content, but only if ## 核心判断 doesn't already exist nearby
    if '## 核心判断' not in text[:500]:
        text = re.sub(
            r'^\*\*核心判断[：:]\*\*\s*',
            '## 核心判断\n\n',
            text,
            flags=re.MULTILINE
        )

    return text


def _normalize_section_headers(text: str) -> str:
    """Normalize ### 一、... and ### **一、...** to ## 一、..."""
    section_map = {
        '一、重要性排序总览': '## 一、重要性排序总览',
        '二、TOP 15 重要新闻深度分析': '## 二、TOP 15 重要新闻深度分析',
        '三、全量电报列表': '## 三、全量电报列表（精简）',
        '三、全量电报列表（精简）': '## 三、全量电报列表（精简）',
    }

    for key, replacement in section_map.items():
        # Match ### **key** or ### key
        escaped = re.escape(key)
        # Pattern with bold: ### **一、重要性排序总览**
        text = re.sub(
            r'^###\s+\*\*' + escaped + r'\*\*\s*$',
            replacement,
            text,
            flags=re.MULTILINE
        )
        # Pattern without bold: ### 一、重要性排序总览
        text = re.sub(
            r'^###\s+' + escaped + r'\s*$',
            replacement,
            text,
            flags=re.MULTILINE
        )

    return text


def _strip_emotion_section(text: str) -> str:
    """Remove the entire 三、市场情绪与策略 section if AI outputs it."""
    # Match ## 三、市场情绪与策略 ... up to the next ## section
    pattern = r'\n*##\s+三、市场情绪与策略.*?(?=\n##\s+(?:三、全量电报列表|四、全量电报列表))'
    text = re.sub(pattern, '', text, flags=re.MULTILINE | re.DOTALL)
    return text


def _cleanup_hr(text: str) -> str:
    """Remove stray horizontal rules and broken fragments before H2 headings."""
    text = re.sub(r'\n---\n+(\n*)(##\s+)', r'\n\n\2', text)
    # Remove stray -- or --- fragments on their own line
    text = re.sub(r'^\s*--?\s*$', '', text, flags=re.MULTILINE)
    return text


def _normalize_risk_warning_format(text: str) -> str:
    """Ensure risk warning is inline - **风险提示**: format, not a ### subsection."""
    # Convert "### 风险提示（...）" to "- **风险提示**: "
    text = re.sub(
        r'^###\s+风险提示[（(][^)）]*[)）]\s*$',
        '- **风险提示**: ',
        text,
        flags=re.MULTILINE
    )
    # Convert "### 风险提示" to "- **风险提示**: "
    text = re.sub(
        r'^###\s+风险提示\s*$',
        '- **风险提示**: ',
        text,
        flags=re.MULTILINE
    )
    return text


def _normalize_risk_items(text: str) -> str:
    """Ensure risk items after - **风险提示**: are consistently formatted with
    2-space indent and numbered list, so md2html renders them as .risk-item."""
    # Find the - **风险提示**: line and collect until next ## or ---
    marker = re.search(r'^- \*\*风险提示\*\*:', text, re.MULTILINE)
    if not marker:
        return text

    start = marker.end()
    rest = text[start:]

    # Find the end of the risk items block
    end_match = re.search(r'^(##\s+|--)', rest, re.MULTILINE)
    block_end = end_match.start() if end_match else len(rest)
    block = rest[:block_end]
    after = rest[block_end:]

    # First, try to split inline risk items that are all on one line:
    # "  1. **name1**：desc1  2. **name2**：desc2  3. **name3**：desc3"
    # Detect if the block is essentially a single line with multiple numbered items
    lines = block.split('\n')
    non_empty = [l for l in lines if l.strip()]
    if non_empty and len(non_empty) <= 2:
        # Possibly inline format — split by numbered item pattern
        combined = ' '.join(l.strip() for l in non_empty if l.strip())
        # Split at "N. **" boundaries
        parts = re.split(r'(?<!\d)(?=\d+\.\s+\*\*)', combined)
        if len(parts) > 1:
            lines = [p.strip() for p in parts if p.strip()]
        else:
            lines = non_empty

    # Normalize: ensure each risk item is "  1. **name**：desc" (2-space indent)
    normalized_lines = []
    counter = 1
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if normalized_lines:
                normalized_lines.append('')
            continue

        # Match "N. **name**：desc" or "N. **name**: desc" or "- **name**：desc"
        m = re.match(r'^(\d+|[-\*])\.?\s+\*\*(.+?)\*\*[：:]\s*(.*)', stripped)
        if m:
            name = m.group(2).strip()
            desc = m.group(3).strip()
            # Also strip any trailing inline items from desc (they were split above)
            desc = re.sub(r'\s+\d+\.\s+\*\*.*', '', desc).strip()
            normalized_lines.append(f'  {counter}. **{name}**：{desc}')
            counter += 1
        elif normalized_lines:
            # Continuation line of previous item
            normalized_lines.append(f'    {stripped}')

    if normalized_lines:
        new_block = '\n' + '\n'.join(normalized_lines)
        text = text[:start] + new_block + after

    return text



def _fix_table_column_count(text: str, table_start: int) -> str:
    """Merge extra columns into the last content column when rows have more cells than header."""
    lines = text[table_start:].split('\n')
    if not lines:
        return text

    # Determine expected column count from separator row
    expected_cols = 4  # default for 4-column format
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and '---' in stripped:
            parts = [p for p in stripped.split('|') if p.strip()]
            expected_cols = len(parts)
            break

    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith('|'):
            fixed_lines.append(line)
            continue

        parts = [p for p in stripped.split('|')]
        inner = [p.strip() for p in parts[1:-1]] if len(parts) > 1 else []

        # Header and separator rows: keep as-is
        if '---' in stripped or any(k in stripped for k in ['序号', '内容']):
            fixed_lines.append(line)
        elif len(inner) > expected_cols:
            # Merge extra columns into the last one
            extra = inner[expected_cols - 1:]
            merged_content = ' '.join(extra)
            new_inner = inner[:expected_cols - 1] + [merged_content]
            new_line = '| ' + ' | '.join(new_inner) + ' |'
            fixed_lines.append(new_line)
        else:
            fixed_lines.append(line)

    return text[:table_start] + '\n'.join(fixed_lines)

def _validate_telegraph_table(text: str) -> str:
    """Detect if the telegraph table section is a placeholder instead of a real table."""
    # Find the ## 三、全量电报列表 section
    section_match = re.search(r'^##\s+三、全量电报列表[^\n]*\n+', text, re.MULTILINE)
    if not section_match:
        return text

    sec_start = section_match.end()
    rest = text[sec_start:]

    # Check if there's a table (lines starting with |)
    has_table = bool(re.search(r'^\|', rest, re.MULTILINE))

    if not has_table:
        # No table found - the AI wrote placeholder text. Insert a warning.
        warning = (
            '| 序号 | 时间 | Lv | 分享 | 评论 | 内容摘要40字 |\n'
            '|------|------|----|------|------|-------------|\n'
            '| - | - | - | - | - | **AI未生成表格，请检查prompt或重新运行** |\n'
        )
        text = text[:sec_start] + warning + text[sec_start:]
        return text

    # Fix rows with extra columns (AI sometimes uses | inside content like "龙虎榜|desc")
    text = _fix_table_column_count(text, sec_start)
    return text
