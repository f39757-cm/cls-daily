"""
Write the final markdown report and run log.
"""

import os
import json
from datetime import datetime


def write_report(markdown_content: str, date_str: str, output_dir: str) -> str:
    """
    Write the markdown report to the output directory.
    Returns the full file path.
    """
    filename = f"CLS_早报_{date_str}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return filepath


def append_run_log(
    output_dir: str,
    date_str: str,
    item_count: int,
    status: str,
    output_path: str,
    error_msg: str = "",
):
    """
    Append a JSON line to run_log.jsonl for tracking.
    """
    log_path = os.path.join(output_dir, "run_log.jsonl")
    entry = {
        "date": date_str,
        "timestamp": datetime.now().isoformat(),
        "item_count": item_count,
        "status": status,
        "output_path": output_path,
        "error_msg": error_msg,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
