"""程序主入口：自动登录并查询电费。"""

from __future__ import annotations

import json
import logging
import sys
import traceback

from config import (
    APP_CONFIG_FILE,
    DEBUG_LOG_HTTP,
    LOG_FILE,
)
from electric_query import query_electric, result_to_json_dict, result_to_pretty_text
from exceptions import AccountAuthError, CaptchaError, CredentialFormatError, LoginError, QueryError
from http_client import build_session
from login import login
from ocr import OcrEngine
from settings import load_app_config


def setup_logging() -> None:
    level = logging.DEBUG if DEBUG_LOG_HTTP else logging.INFO
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def main() -> int:
    setup_logging()

    try:
        app_cfg = load_app_config(APP_CONFIG_FILE)
        logging.info("已读取配置文件: %s", APP_CONFIG_FILE)
        logging.info("已读取凭据，账号: ***%s", app_cfg.credentials.username[8:])

        session = build_session()
        ocr_engine = OcrEngine()

        login_meta = login(session, app_cfg.credentials, ocr_engine)
        logging.debug("login_meta keys: %s", list(login_meta.keys()))

        result = query_electric(session, app_cfg.target)
        json_payload = result_to_json_dict(result)
        logging.info("QUERY_RESULT %s", json.dumps(json_payload, ensure_ascii=False))
        print(result_to_pretty_text(result))
        return 0

    except CredentialFormatError as exc:
        print(f"凭据读取失败: {exc}", file=sys.stderr)
        return 2
    except AccountAuthError as exc:
        print(f"登录失败（账号密码问题）: {exc}", file=sys.stderr)
        return 3
    except CaptchaError as exc:
        print(f"登录失败（验证码问题）: {exc}", file=sys.stderr)
        return 4
    except LoginError as exc:
        print(f"登录失败: {exc}", file=sys.stderr)
        return 5
    except QueryError as exc:
        print(f"电费查询失败: {exc}", file=sys.stderr)
        return 6
    except Exception as exc:
        print(f"未处理异常: {exc}", file=sys.stderr)
        logging.debug("Unhandled exception details:\n%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
