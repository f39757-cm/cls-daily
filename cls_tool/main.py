"""
CLS Daily Summary Tool - Main Entry Point
Fetches CLS telegraph news and generates AI-powered morning briefing.
"""

import sys
import os
from datetime import datetime, timedelta

from config import (
    OUTPUT_DIR, LOG_DIR,
    TIME_START_HOUR, TIME_START_MINUTE,
    TIME_END_HOUR, TIME_END_MINUTE,
    SUNDAY_EVENING_HOUR, SUNDAY_EVENING_MINUTE,
    MONDAY_START_HOUR, MONDAY_START_MINUTE,
    AUTO_DEPLOY,
)
from cls_fetcher import fetch_rolls_in_range
from news_processor import filter_by_time, deduplicate, pre_rank
from prompt_builder import build_analysis_prompt
from ai_analyzer import analyze_via_deepseek, analyze_fallback
from report_writer import write_report, append_run_log
from market_data import get_index_data


def get_time_window(date_override: str = None) -> tuple:
    """
    Compute the time window based on day of week:
    - Mon 08:45 → Sunday 21:00 ~ Monday 08:45 (last ~12h)
    - Tue-Fri 08:45 → previous day 15:00 ~ today 08:45
    - Sun 21:00 → Friday 15:00 ~ Sunday 21:00 (weekend wrap-up)
    - Sat / Sun morning → skip (returns None)
    Returns (start_dt, end_dt, date_str) or (None, None, None) to skip.
    """
    if date_override:
        today = datetime.strptime(date_override, "%Y%m%d")
        # Force weekday behavior based on overridden date
        weekday = today.weekday()
        now = today.replace(hour=datetime.now().hour, minute=datetime.now().minute)
    else:
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        weekday = today.weekday()

    # Saturday: should not run, skip
    if weekday == 5:
        return None, None, None

    # Sunday
    if weekday == 6:
        if now.hour >= SUNDAY_EVENING_HOUR:
            # Sunday evening run: Friday 15:00 → now
            friday = today - timedelta(days=2)
            start_dt = friday.replace(hour=TIME_START_HOUR, minute=TIME_START_MINUTE)
            end_dt = now
            return start_dt, end_dt, today.strftime("%Y%m%d")
        else:
            # Sunday morning: skip
            return None, None, None

    # Monday
    if weekday == 0:
        yesterday = today - timedelta(days=1)
        start_dt = yesterday.replace(hour=MONDAY_START_HOUR, minute=MONDAY_START_MINUTE)
        end_dt = today.replace(hour=TIME_END_HOUR, minute=TIME_END_MINUTE)
        return start_dt, end_dt, today.strftime("%Y%m%d")

    # Tuesday through Friday
    yesterday = today - timedelta(days=1)
    start_dt = yesterday.replace(hour=TIME_START_HOUR, minute=TIME_START_MINUTE)
    end_dt = today.replace(hour=TIME_END_HOUR, minute=TIME_END_MINUTE)
    date_str = today.strftime("%Y%m%d")
    return start_dt, end_dt, date_str


def main():
    # Parse args
    date_override = None
    mode = "full"  # full | test | install-task | remove-task

    args = sys.argv[1:]
    for arg in args:
        if arg.startswith("--date="):
            date_override = arg.split("=", 1)[1]
        elif arg == "--mode=test":
            mode = "test"
        elif arg == "--install-task":
            mode = "install-task"
        elif arg == "--remove-task":
            mode = "remove-task"
        elif arg == "--deploy":
            mode = "deploy"

    # Handle deploy command (standalone, no report generation)
    if mode == "deploy":
        from deploy_site import main as deploy_main
        deploy_main(deploy=True)
        return

    # Handle scheduler commands
    if mode == "install-task":
        from scheduler_setup import install_scheduled_task
        install_scheduled_task()
        return
    elif mode == "remove-task":
        from scheduler_setup import remove_scheduled_task
        remove_scheduled_task()
        return

    # Ensure output directories exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # 1. Compute time window
    start_dt, end_dt, date_str = get_time_window(date_override)
    if start_dt is None:
        print(f"[INFO] 周末早间时段，跳过执行")
        return

    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    print(f"[INFO] 时间窗口: {start_dt} -> {end_dt}")
    print(f"[INFO] 时间戳: {start_ts} -> {end_ts}")

    # 2. Fetch CLS data
    print("[INFO] 正在抓取财联社电报数据...")
    try:
        items = fetch_rolls_in_range(start_ts, end_ts)
    except Exception as e:
        print(f"[ERROR] 数据抓取失败: {e}")
        append_run_log(OUTPUT_DIR, date_str, 0, "FETCH_ERROR", "", str(e))
        sys.exit(1)

    print(f"[INFO] 原始抓取: {len(items)} 条")

    # 3. Filter, deduplicate, pre-rank
    items = filter_by_time(items, start_ts, end_ts)
    items = deduplicate(items)
    items = pre_rank(items)

    print(f"[INFO] 去重过滤后: {len(items)} 条")

    if not items:
        print("[INFO] 该时段无财联社电报数据")
        append_run_log(OUTPUT_DIR, date_str, 0, "NO_DATA", "", "")
        return

    # Test mode: just dump raw data
    if mode == "test":
        import json
        test_path = os.path.join(OUTPUT_DIR, f"raw_data_{date_str}.json")
        with open(test_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 测试模式: 原始数据已保存至 {test_path}")
        return

    # 4. Fetch market context
    print("[INFO] 正在获取前日指数数据...")
    idx_data = get_index_data()
    print(f"[INFO] 指数: {idx_data}")

    # 5. Build analysis prompt
    print("[INFO] 正在构建分析提示词...")
    prompt = build_analysis_prompt(items, start_dt, end_dt, idx_data=idx_data)

    # 6. AI Analysis via DeepSeek
    print("[INFO] 正在调用 DeepSeek API 生成分析...")
    try:
        analysis = analyze_via_deepseek(prompt)
    except Exception as e:
        print(f"[WARN] AI分析失败，使用降级方案: {e}")
        analysis = analyze_fallback(prompt)
        # Also save the prompt for manual analysis
        prompt_path = os.path.join(OUTPUT_DIR, f"prompt_{date_str}.md")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"[INFO] 分析提示词已保存至 {prompt_path}")

    # 6.5 Normalize markdown structure for consistent rendering
    print("[INFO] 正在规范化 Markdown 结构...")
    try:
        from md_normalizer import normalize
        weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday_str = weekday_map[end_dt.weekday()]
        trading_note = "交易日" if end_dt.weekday() < 5 else "非交易日(供下一交易日参考)"
        date_display = end_dt.strftime("%Y年%m月%d日")
        analysis = normalize(analysis, date_display, weekday_str, trading_note)
    except Exception as e:
        print(f"[WARN] Markdown规范化失败: {e}")

    # 7. Write report
    output_path = write_report(analysis, date_str, OUTPUT_DIR)
    print(f"[SUCCESS] 早报已生成: {output_path}")

    # 7.5 Generate HTML version
    try:
        from md2html import md_to_html
        html_path = md_to_html(output_path)
        print(f"[SUCCESS] HTML版本: {html_path}")
    except Exception as e:
        print(f"[WARN] HTML生成失败: {e}")

    # 8. Log
    append_run_log(OUTPUT_DIR, date_str, len(items), "SUCCESS", output_path)

    # 9. Deploy to GitHub Pages (if --deploy or AUTO_DEPLOY)
    do_deploy = "--deploy" in sys.argv
    if do_deploy or AUTO_DEPLOY:
        print("[INFO] 正在部署到 GitHub Pages...")
        try:
            from deploy_site import main as deploy_main
            deploy_main(deploy=True)
        except Exception as e:
            print(f"[WARN] 部署失败: {e}")

    return output_path


if __name__ == "__main__":
    main()
