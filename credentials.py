"""读取并校验账号凭据。"""

from __future__ import annotations

from pathlib import Path

from exceptions import CredentialFormatError
from models import Credentials


def read_credentials(path: Path) -> Credentials:
    if not path.exists():
        raise CredentialFormatError(f"凭据文件不存在: {path}")

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 2:
        raise CredentialFormatError("凭据文件格式错误：需要两行，分别是 name:xxx 与 password:xxx")

    first, second = lines[0], lines[1]
    if not first.startswith("name:"):
        raise CredentialFormatError("第一行格式错误，必须以 name: 开头")
    if not second.startswith("password:"):
        raise CredentialFormatError("第二行格式错误，必须以 password: 开头")

    username = first.split(":", 1)[1].strip()
    password = second.split(":", 1)[1].strip()
    if not username:
        raise CredentialFormatError("账号不能为空，请检查 name: 后内容")
    if not password:
        raise CredentialFormatError("密码不能为空，请检查 password: 后内容")

    return Credentials(username=username, password=password)
