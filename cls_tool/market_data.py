"""
Fetch market index data via akshare.
Monkey-patches requests to bypass Windows system proxy.
"""

import os

# Clear proxy env vars
for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(k, None)

# Monkey-patch requests before akshare's internal import
import requests

_orig_get = requests.get

def _patched_get(url, **kwargs):
    with requests.Session() as s:
        s.trust_env = False
        return s.get(url, **kwargs)

requests.get = _patched_get

import akshare as ak


INDEX_MAP = {
    "sh": ("sh000001", "上证指数"),
    "sz": ("sz399001", "深证成指"),
    "cyb": ("sz399006", "创业板指"),
    "kc": ("sh000688", "科创50"),
}


def get_index_data() -> dict:
    """Fetch latest major index data via akshare. Returns dict with formatted strings."""
    result = {}
    for key, (symbol, _name) in INDEX_MAP.items():
        try:
            df = ak.stock_zh_index_daily(symbol=symbol)
            if not df.empty:
                last = df.iloc[-1]
                close = last["close"]
                if len(df) >= 2:
                    prev = df.iloc[-2]["close"]
                    pct = (close - prev) / prev * 100
                    sign = "+" if pct >= 0 else ""
                    result[key] = f"{close:.2f} ({sign}{pct:.2f}%)"
                else:
                    result[key] = f"{close:.2f}"
            else:
                result[key] = "N/A"
        except Exception as e:
            print(f"[WARN] 获取{_name}数据失败: {e}")
            result[key] = "N/A"
    return result
