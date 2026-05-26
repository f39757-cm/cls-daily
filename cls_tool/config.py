"""
CLS Daily Summary Tool - Configuration
Supports both local development and GitHub Actions environments.
"""

import os

# ---- Paths ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# ---- CLS API ----
CLS_API_BASE = "https://www.cls.cn/v1/roll/get_roll_list"
CLS_DEFAULT_RN = 50
CLS_MAX_PAGES = 20
CLS_APP = "CailianpressWeb"
CLS_OS = "web"
CLS_SV = "8.4.6"

# ---- Time Window ----
TIME_START_HOUR = 15
TIME_START_MINUTE = 0
TIME_END_HOUR = 8
TIME_END_MINUTE = 45

# Weekend / Monday special windows
SUNDAY_EVENING_HOUR = 21
SUNDAY_EVENING_MINUTE = 0
MONDAY_START_HOUR = 21
MONDAY_START_MINUTE = 0

# ---- DeepSeek API (Anthropic-compatible endpoint) ----
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/anthropic"
DEEPSEEK_MODEL = "deepseek-v4-pro"

# ---- AI Analysis ----
ANALYSIS_MAX_TOKENS = 32768
ANALYSIS_TIMEOUT_SECONDS = 900

# ---- Report ----
REPORT_FILENAME_TEMPLATE = "CLS_早报_{date}.md"

# ---- GitHub Pages Deployment ----
SITE_REPO_PATH = os.environ.get("SITE_REPO_PATH", r"C:\Users\29732\Desktop\cls-site")
AUTO_DEPLOY = os.environ.get("CI", "").lower() not in ("true", "1")

# ---- Feature Toggles for Market Analyzers ----
FEATURE_ZT = True
FEATURE_SECTOR = True
FEATURE_LHB = True
FEATURE_FUND_FLOW = True
FEATURE_A50 = True
FEATURE_THEME_CONTINUITY = True
FEATURE_SENTIMENT = True
FEATURE_LINKAGE = True
FEATURE_LEADER_SIGNALS = True
FEATURE_EVENT_CALENDAR = True
FEATURE_THS_MOMENTUM = True

# ---- Prompt Budget ----
PROMPT_TOP_N = 60
