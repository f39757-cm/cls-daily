"""
Build the deep analysis prompt from CLS telegraph data.
Focus: 加红消息深度分析 + 国内外联动 + 市场情绪与策略.
"""

from datetime import datetime
from config import PROMPT_TOP_N


def _fmt_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%H:%M")


def _format_item_compact(item: dict, idx: int) -> str:
    """Compact single-line format to save tokens."""
    level = item.get("level", "C")
    ctime = _fmt_ts(item.get("ctime", 0))
    subjects = "|".join(s.get("subject_name", "") for s in item.get("subjects", []))
    stocks = ",".join(
        f"{s.get('name', '')}({s.get('StockID', '')})"
        for s in item.get("stock_list", [])
    )
    content = item.get("content", "")
    share_num = item.get("share_num", 0)
    comment_num = item.get("comment_num", 0)
    score = item.get("_score", 0)

    parts = [f"[{idx}] {ctime} Lv{level} s{score} 分享{share_num} 评论{comment_num}"]
    if subjects:
        parts.append(f"#{subjects}")
    if stocks:
        parts.append(f"${stocks}")
    parts.append(content[:200])
    return " ".join(parts)


def build_analysis_prompt(
    items: list[dict],
    start_dt: datetime,
    end_dt: datetime,
    idx_data: dict = None,
    market_context: dict = None,
) -> str:
    """Build analysis prompt focused on CLS news deep analysis."""

    date_str = end_dt.strftime("%Y年%m月%d日")
    weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_map[end_dt.weekday()]
    is_trading_day = end_dt.weekday() < 5

    market_ctx = ""
    if idx_data:
        market_ctx = f"上证{idx_data.get('sh','?')} 深证{idx_data.get('sz','?')} 创业板{idx_data.get('cyb','?')}"
    else:
        market_ctx = "前日指数数据待补充（请根据你掌握的知识补充前日主要指数收盘及涨跌幅）"

    trading_note = "交易日" if is_trading_day else "非交易日(供下一交易日参考)"

    # Separate 加红 (S/A level) vs regular
    red_items = [it for it in items if it.get("level") in ("S", "A")]
    regular_items = [it for it in items if it.get("level") not in ("S", "A")]

    # Take top items for full detail
    top_n = min(PROMPT_TOP_N, len(items))
    top_items = items[:top_n]
    news_lines = []
    for i, item in enumerate(top_items, 1):
        news_lines.append(_format_item_compact(item, i))
    all_news = "\n".join(news_lines)

    # Remaining items summary
    rest_items = items[top_n:]
    rest_table = ""
    if rest_items:
        rest_table = "\n## 其余电报摘要\n|#|时间|Lv|分享|评论|内容摘要|\n|---|---|---|---|---|---|\n"
        for i, item in enumerate(rest_items, top_n + 1):
            ctime = _fmt_ts(item.get("ctime", 0))
            level = item.get("level", "C")
            share_num = item.get("share_num", 0)
            comment_num = item.get("comment_num", 0)
            content = item.get("content", "")[:60].replace("\n", " ")
            rest_table += f"|{i}|{ctime}|{level}|{share_num}|{comment_num}|{content}|\n"

    prompt = f"""你是顶级A股策略分析师，擅长从全球宏观视角解读中国市场。请根据以下{len(items)}条财联社电报，生成一份高水平的每日早报深度分析。

日期: {date_str} {weekday} {trading_note}
市场: {market_ctx}
覆盖时段: {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}
加红消息(S/A级): {len(red_items)}条 | 普通消息: {len(regular_items)}条

## 分析要求

**重要：排序标准** — 消息的重要性由你独立判断，结合国内外宏观形势、政策动向、产业趋势、地缘格局等维度综合评估。TOP 15 深度分析以你对宏观形势的独立判断为主；全量电报列表排序可参考等级+分享数+评论数的综合指标。

## 核心判断

用200字以内的精炼语言，给出今日市场的核心判断。必须包含：
- **一句话定调**: 今日市场最核心的矛盾或主线是什么
- **3个关键信号**: 最重要的3条新闻分别释放了什么信号
- **策略一句话**: 今天该怎么做

### 一、重要性排序总览

从全部{len(items)}条电报中，按你的独立判断选出最重要的15条，列出排序表格：

| 排名 | 时间 | 等级 | 标题概述 | 重要度 | 核心影响 |
|------|------|------|----------|--------|----------|
| 1 | HH:MM | S/A/B | 一句话概括 | ★★★★★ | 一句话点出最关键的影响 |

### 二、TOP 15 重要新闻深度分析

对上表15条新闻逐一深度分析，优先关注加红消息(S/A级)。每条必须包含：

**格式：**
### N. [S/A/B级] 新闻标题
- **时间**: YYYY年MM月DD日 HH:MM
- **重要程度**: ★★★★★ (一星到五星)
- **核心逻辑**: 用2-3句话讲清楚为什么重要，背后的传导链条是什么

- **国内视角**（内容直接写在标题下，禁止使用子标题如"对A股影响""传导链条"等）:
  - 对A股相关板块/个股的具体影响路径
  - 政策面/资金面/基本面的联动逻辑

- **国际视角**（内容直接写在标题下，禁止使用子标题如"全球格局""联动关系"等）:
  - 该事件在全球宏观格局中的位置
  - 与美股/港股/大宗商品/汇率的联动关系
  - 外资可能如何看待和反应

- **受益方向及个股**:
  1. **方向一**: 逻辑简述 → 个股: xxx(代码), xxx(代码)
  2. **方向二**: 逻辑简述 → 个股: xxx(代码)

- **韭研公社热议**: 该方向在社区的讨论焦点和分歧点
- **券商研报视角**: 是否有卖方覆盖，主流观点和预期差在哪
- **持续性判断**: 一日游 / 3-5天事件驱动 / 中期主线 / 长期赛道

### 三、全量电报列表（精简）
**【强制】必须输出完整表格，包含全部{len(items)}条电报，禁止使用"篇幅限制略"等占位文本。**
按综合重要度排列（等级优先，分享数和评论数作为热度参考）：
| 序号 | 时间 | Lv | 分享 | 评论 | 内容摘要40字 |
|------|------|----|------|------|-------------|

---
## 电报数据

{all_news}
{rest_table}
"""
    return prompt
