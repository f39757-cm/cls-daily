"""
Filter, deduplicate, and pre-rank CLS news items.
Ranking based on share_num and comment_num (not reading_num).
"""

import math


def filter_by_time(items: list[dict], start_ts: int, end_ts: int) -> list[dict]:
    """Keep only items with start_ts <= ctime <= end_ts."""
    return [item for item in items if start_ts <= item.get("ctime", 0) <= end_ts]


def deduplicate(items: list[dict]) -> list[dict]:
    """Remove duplicate items by 'id' field, keeping first occurrence."""
    seen = set()
    result = []
    for item in items:
        item_id = item.get("id")
        if item_id not in seen:
            seen.add(item_id)
            result.append(item)
    return result


def compute_importance_score(item: dict) -> float:
    """
    Importance score based on share count and comment count.
    Higher weight on shares (social proof of importance).
      - level: A=3.0, B=2.0, C=1.0
      - share_num: log10 scaled, weight 0.8 (primary)
      - comment_num: log10 scaled, weight 0.5 (secondary)
      - reading_num: log10 scaled, weight 0.1 (tertiary reference)
      - has_subjects: +0.3
      - has_stocks: +0.5
      - bold: +0.3
    """
    level_map = {"A": 3.0, "B": 2.0, "C": 1.0}
    score = level_map.get(item.get("level", "C"), 1.0)

    share_num = item.get("share_num", 0)
    if share_num > 0:
        score += math.log10(share_num + 1) * 0.8

    comment_num = item.get("comment_num", 0)
    if comment_num > 0:
        score += math.log10(comment_num + 1) * 0.5

    reading_num = item.get("reading_num", 0)
    if reading_num > 0:
        score += math.log10(reading_num + 1) * 0.1

    if item.get("subjects"):
        score += 0.3
    if item.get("stock_list"):
        score += 0.5
    if item.get("bold"):
        score += 0.3

    return round(score, 2)


def pre_rank(items: list[dict]) -> list[dict]:
    """Sort items by importance score descending. Adds '_score' key."""
    for item in items:
        item["_score"] = compute_importance_score(item)
    items.sort(key=lambda x: x["_score"], reverse=True)
    return items
