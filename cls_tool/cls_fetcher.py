"""
CLS API fetcher with pagination and retry logic.
"""

import time
import requests
from config import (
    CLS_API_BASE, CLS_DEFAULT_RN, CLS_MAX_PAGES,
    CLS_APP, CLS_OS, CLS_SV,
)
from signer import sign_params


def _build_params(last_time: int, rn: int = CLS_DEFAULT_RN, category: str = "") -> dict:
    return {
        "refresh_type": "1",
        "rn": str(rn),
        "category": category,
        "last_time": str(last_time),
        "os": CLS_OS,
        "sv": CLS_SV,
        "app": CLS_APP,
    }


def fetch_roll_page(
    last_time: int = 0,
    rn: int = CLS_DEFAULT_RN,
    category: str = "",
    session: requests.Session = None,
) -> dict:
    """Fetch one page of CLS roll data. Returns the full JSON response."""
    params = _build_params(last_time, rn, category)
    signed_params = sign_params(params)

    close_session = False
    if session is None:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.cls.cn/",
        })
        close_session = True

    try:
        resp = session.get(CLS_API_BASE, params=signed_params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if str(data.get("errno")) != "0":
            raise RuntimeError(f"CLS API error: errno={data.get('errno')}, msg={data.get('msg', 'unknown')}")
        return data
    finally:
        if close_session:
            session.close()


def fetch_rolls_in_range(
    start_ts: int,
    end_ts: int,
    max_pages: int = CLS_MAX_PAGES,
) -> list[dict]:
    """
    Fetch all CLS roll items whose ctime falls within [start_ts, end_ts].
    Returns a flat list of roll_data items, newest first.
    """
    all_items = []
    last_time = 0  # Start from newest

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.cls.cn/",
    })
    session.trust_env = False  # Bypass Windows system proxy
    try:
        for page in range(max_pages):
            try:
                data = fetch_roll_page(last_time=last_time, session=session)
            except Exception as e:
                # Retry once after 2s delay
                print(f"[WARN] Page {page + 1} fetch failed: {e}, retrying...")
                time.sleep(2)
                try:
                    data = fetch_roll_page(last_time=last_time, session=session)
                except Exception as e2:
                    print(f"[ERROR] Page {page + 1} retry also failed: {e2}")
                    break

            roll_data = data.get("data", {}).get("roll_data", [])
            if not roll_data:
                break

            # Filter items in time range
            in_range = []
            for item in roll_data:
                ctime = item.get("ctime", 0)
                if start_ts <= ctime <= end_ts:
                    in_range.append(item)
                # Items are reverse-chronological; once we go below start_ts, we can stop
                elif ctime < start_ts:
                    # Still add items from this page that are in range
                    # then break pagination
                    all_items.extend(in_range)
                    return all_items

            all_items.extend(in_range)

            # If all items on this page are older than our range, stop
            oldest_ctime = roll_data[-1].get("ctime", 0)
            if oldest_ctime < start_ts:
                break

            # Paginate: set last_time to the oldest item's ctime
            last_time = oldest_ctime
    finally:
        session.close()

    return all_items
