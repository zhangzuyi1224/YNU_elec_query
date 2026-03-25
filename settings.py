"""读取统一配置文件。"""

from __future__ import annotations

import json
from pathlib import Path

from exceptions import CredentialFormatError
from models import AppConfig, Credentials, DormQueryTarget


def _must_text(obj: dict, key: str, hint: str) -> str:
    value = str(obj.get(key, "")).strip()
    if not value:
        raise CredentialFormatError(f"配置项缺失或为空: {hint}")
    return value


def load_app_config(path: Path) -> AppConfig:
    if not path.exists():
        raise CredentialFormatError(f"配置文件不存在: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CredentialFormatError(f"配置文件不是合法 JSON: {exc}") from exc

    account = data.get("account") or {}
    query = data.get("query") or {}

    credentials = Credentials(
        username=_must_text(account, "name", "account.name"),
        password=_must_text(account, "password", "account.password"),
    )

    target = DormQueryTarget(
        elcsys_id=_must_text(query, "elcsysId", "query.elcsysId"),
        campus_name=_must_text(query, "campusName", "query.campusName"),
        district_keyword=_must_text(query, "districtKeyword", "query.districtKeyword"),
        building_keyword=_must_text(query, "buildingKeyword", "query.buildingKeyword"),
        floor_name=_must_text(query, "floorName", "query.floorName"),
        room_name=_must_text(query, "roomName", "query.roomName"),
        display_building=_must_text(query, "displayBuilding", "query.displayBuilding"),
        display_sub_building=_must_text(query, "displaySubBuilding", "query.displaySubBuilding"),
    )

    return AppConfig(
        credentials=credentials,
        target=target,
    )
