"""
AI analysis via DeepSeek API with streaming for reliability.
"""

import json
import requests
from config import DEEPSEEK_API_KEY, ANALYSIS_MAX_TOKENS, ANALYSIS_TIMEOUT_SECONDS


def _call_deepseek_stream(prompt: str, max_tokens: int = ANALYSIS_MAX_TOKENS) -> str:
    """DeepSeek OpenAI-compatible Chat Completions API with streaming."""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "stream": True,
    }

    full_text = []
    session = requests.Session()
    session.trust_env = False
    try:
        resp = session.post(url, headers=headers, json=body, timeout=ANALYSIS_TIMEOUT_SECONDS, stream=True)
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta:
                        full_text.append(delta["content"])
                except json.JSONDecodeError:
                    pass
    finally:
        session.close()

    return "".join(full_text)


def analyze_via_deepseek(prompt: str) -> str:
    """
    Send the prompt to DeepSeek API via streaming and return the analysis.
    Auto-adjusts max_tokens if needed.
    """
    # First try with default max_tokens
    try:
        result = _call_deepseek_stream(prompt)
        if result:
            return result
    except Exception as e:
        print(f"[WARN] First attempt failed: {e}")

    # Retry with smaller max_tokens
    try:
        print("[INFO] Retrying with reduced max_tokens...")
        result = _call_deepseek_stream(prompt, max_tokens=8192)
        if result:
            return result
    except Exception as e2:
        print(f"[WARN] Retry also failed: {e2}")

    raise RuntimeError("All DeepSeek API attempts failed")


def analyze_fallback(prompt: str) -> str:
    """Generate a basic data-only report when AI analysis fails."""
    return f"""# 财联社电报早报 - 数据汇总

> ⚠️ AI分析暂不可用，以下为原始数据汇总

分析提示词已保存至 outputs/ 目录，请手动分析。

---
{prompt[-8000:]}
"""
