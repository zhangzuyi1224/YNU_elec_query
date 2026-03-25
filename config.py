"""配置与常量。"""

from __future__ import annotations

from pathlib import Path

BASE_URL = "https://ecard.ynu.edu.cn"
LOGIN_PAGE_URL = f"{BASE_URL}/epay/person/index"
LOGIN_FORM_ACTION_FALLBACK = "/epay/j_spring_security_check"
ELECTRIC_QUERY_URL = f"{BASE_URL}/epay/electric/load4electricbill"
ELECTRIC_API_BASE = f"{BASE_URL}/epay/electric"
ELECTRIC_AREA_API = f"{ELECTRIC_API_BASE}/queryelectricarea"
ELECTRIC_DISTRICT_API = f"{ELECTRIC_API_BASE}/queryelectricdistricts"
ELECTRIC_BUILDING_API = f"{ELECTRIC_API_BASE}/queryelectricbuis"
ELECTRIC_FLOOR_API = f"{ELECTRIC_API_BASE}/queryelectricfloors"
ELECTRIC_ROOM_API = f"{ELECTRIC_API_BASE}/queryelectricrooms"
ELECTRIC_BILL_API = f"{ELECTRIC_API_BASE}/queryelectricbill"

# 抓取页面可确认的默认字段名
FIELD_USERNAME = "j_username"
FIELD_PASSWORD = "j_password"
FIELD_CAPTCHA = "imageCodeName"
FIELD_CSRF = "_csrf"
FIELD_ELCSYS_ID = "elcsysid"

APP_CONFIG_FILE = Path("query_config.json")
LOG_FILE = Path("query.log")

REQUEST_TIMEOUT = 15
LOGIN_MAX_ATTEMPTS = 5
NETWORK_RETRY_TOTAL = 3

# 通过页面源码可确认的验证码路径前缀
CAPTCHA_SRC_HINT = "/epay/codeimage"

DEBUG_LOG_HTTP = True
