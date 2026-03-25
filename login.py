"""登录流程实现。"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import (
    CAPTCHA_SRC_HINT,
    FIELD_CAPTCHA,
    FIELD_PASSWORD,
    FIELD_USERNAME,
    LOGIN_FORM_ACTION_FALLBACK,
    LOGIN_MAX_ATTEMPTS,
    LOGIN_PAGE_URL,
    REQUEST_TIMEOUT,
)
from exceptions import AccountAuthError, CaptchaError, LoginError, ParseError
from models import Credentials
from ocr import OcrEngine


def _extract_login_form(html: str, base_url: str) -> tuple[str, dict[str, str], str]:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", id="loginFr") or soup.find("form", attrs={"name": "loginFr"}) or soup.find("form")
    if form is None:
        raise ParseError("未找到登录表单 form")

    action = form.get("action") or LOGIN_FORM_ACTION_FALLBACK
    action_url = urljoin(base_url, action)

    hidden_fields: dict[str, str] = {}
    for node in form.find_all("input", attrs={"type": "hidden"}):
        name = (node.get("name") or "").strip()
        value = (node.get("value") or "").strip()
        if name:
            hidden_fields[name] = value

    captcha_img = form.find("img", class_="login_x7_form_vcode")
    if captcha_img is None:
        all_imgs = form.find_all("img")
        captcha_img = next((img for img in all_imgs if CAPTCHA_SRC_HINT in (img.get("src") or "")), None)

    if captcha_img is None or not captcha_img.get("src"):
        raise ParseError("未找到验证码图片地址")

    captcha_url = urljoin(base_url, str(captcha_img.get("src")))
    return action_url, hidden_fields, captcha_url


def _is_captcha_error(text: str) -> bool:
    hints = ["验证码", "校验码", "imageCode", "code error", "verification"]
    return any(h in text for h in hints)


def _is_account_error(text: str) -> bool:
    hints = ["用户名或密码错误", "账号或密码错误", "密码错误", "user", "password", "用户名"]
    return any(h in text for h in hints)


def _looks_logged_in(resp: requests.Response) -> bool:
    final_url = resp.url or ""
    page = resp.text or ""

    if "/epay/person/index" in final_url and "login" in page.lower() and "j_username" in page:
        return False

    success_keywords = ["退出", "个人信息", "一卡通服务平台", "electric", "load4electricbill"]
    if any(k in page for k in success_keywords):
        return True

    if "/epay/person/index" not in final_url:
        return True

    return False


def login(session: requests.Session, creds: Credentials, ocr_engine: OcrEngine) -> dict[str, Any]:
    last_error: Exception | None = None

    for attempt in range(1, LOGIN_MAX_ATTEMPTS + 1):
        logging.info("登录尝试 %s/%s", attempt, LOGIN_MAX_ATTEMPTS)

        try:
            page = session.get(LOGIN_PAGE_URL, timeout=REQUEST_TIMEOUT)
            page.raise_for_status()
            action_url, hidden_fields, captcha_url = _extract_login_form(page.text, LOGIN_PAGE_URL)

            cap_resp = session.get(captcha_url, timeout=REQUEST_TIMEOUT)
            cap_resp.raise_for_status()
            captcha_text = ocr_engine.solve_captcha(cap_resp.content)
            logging.debug("OCR captcha result: %s", captcha_text)

            if len(captcha_text) < 3:
                raise CaptchaError("OCR 识别到的验证码长度异常")

            payload: dict[str, Any] = {}
            payload.update(hidden_fields)
            payload[FIELD_USERNAME] = creds.username
            payload[FIELD_PASSWORD] = creds.password
            payload[FIELD_CAPTCHA] = captcha_text

            post_resp = session.post(action_url, data=payload, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            post_resp.raise_for_status()

            if _looks_logged_in(post_resp):
                logging.info("登录成功")
                return {
                    "login_action_url": action_url,
                    "captcha_url": captcha_url,
                    "hidden_fields": hidden_fields,
                }

            body = post_resp.text or ""
            if _is_account_error(body):
                raise AccountAuthError("账号或密码错误，请检查 password.txt")
            if _is_captcha_error(body):
                raise CaptchaError("验证码错误，准备重试")

            raise LoginError("登录失败，未能识别失败原因（可能页面结构变化）")

        except AccountAuthError:
            raise
        except CaptchaError as exc:
            last_error = exc
            continue
        except requests.RequestException as exc:
            last_error = LoginError(f"登录网络异常: {exc}")
            continue
        except Exception as exc:
            last_error = exc
            continue

    if last_error is None:
        raise LoginError("登录失败：未知原因")
    if isinstance(last_error, Exception):
        raise LoginError(f"登录失败：{last_error}") from last_error
    raise LoginError("登录失败")
