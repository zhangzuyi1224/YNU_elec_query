"""数据模型定义。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Credentials:
    username: str
    password: str


@dataclass
class DormQueryTarget:
    elcsys_id: str
    campus_name: str
    district_keyword: str
    building_keyword: str
    floor_name: str
    room_name: str
    display_building: str
    display_sub_building: str


@dataclass
class AppConfig:
    credentials: Credentials
    target: DormQueryTarget


@dataclass
class ElectricResult:
    campus: str
    building: str
    sub_building: str
    floor: str
    room: str
    room_id: str
    value: str | None
    unit: str | None
    update_time: str | None
    raw: Any
