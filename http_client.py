"""HTTP 会话初始化。"""

from __future__ import annotations

import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import NETWORK_RETRY_TOTAL


def build_session() -> requests.Session:
    session = requests.Session()

    retries = Retry(
        total=NETWORK_RETRY_TOTAL,
        read=NETWORK_RETRY_TOTAL,
        connect=NETWORK_RETRY_TOTAL,
        status=NETWORK_RETRY_TOTAL,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]),
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )

    logging.debug("HTTP session initialized")
    return session
