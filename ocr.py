"""验证码 OCR 模块。"""

from __future__ import annotations

import io
import re
from typing import Final

from PIL import Image, ImageOps

_ALLOWED: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9]")


class OcrEngine:
    def __init__(self) -> None:
        self._backend = None
        self._init_backend()

    def _init_backend(self) -> None:
        # 优先尝试 ddddocr（对验证码适配较好）
        try:
            import ddddocr  # type: ignore

            self._backend = ("ddddocr", ddddocr.DdddOcr(show_ad=False))
            return
        except Exception:
            pass

        # 回退到 pytesseract
        try:
            import pytesseract  # type: ignore

            self._backend = ("tesseract", pytesseract)
            return
        except Exception as exc:
            raise RuntimeError(
                "未找到可用 OCR 后端，请安装 ddddocr 或 pytesseract。"
            ) from exc

    def solve_captcha(self, image_bytes: bytes) -> str:
        if not image_bytes:
            return ""

        preprocessed = self._preprocess(image_bytes)
        kind, engine = self._backend

        if kind == "ddddocr":
            text = engine.classification(preprocessed)
        else:
            img = Image.open(io.BytesIO(preprocessed))
            text = engine.image_to_string(
                img,
                config="--oem 1 --psm 7 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
            )

        return self._clean(text)

    def _preprocess(self, image_bytes: bytes) -> bytes:
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        # 自适应对比度后做简单二值化，提升字符边界。
        img = ImageOps.autocontrast(img)
        img = img.point(lambda p: 255 if p > 140 else 0)

        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()

    def _clean(self, text: str) -> str:
        text = text.strip().replace(" ", "")
        text = _ALLOWED.sub("", text)
        return text
