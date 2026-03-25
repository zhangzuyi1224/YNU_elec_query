"""电费查询模块。"""

from __future__ import annotations

import logging
import re
from typing import Any

import requests

from config import (
    ELECTRIC_AREA_API,
    ELECTRIC_BILL_API,
    ELECTRIC_BUILDING_API,
    ELECTRIC_DISTRICT_API,
    ELECTRIC_FLOOR_API,
    ELECTRIC_QUERY_URL,
    ELECTRIC_ROOM_API,
    FIELD_ELCSYS_ID,
    REQUEST_TIMEOUT,
)
from exceptions import ParseError, QueryError
from models import DormQueryTarget, ElectricResult


def _extract_csrf_token(html: str) -> str:
    m = re.search(r'<meta\s+name="_csrf"\s+content="([^"]+)"', html)
    if not m:
        raise ParseError("未在页面中找到 CSRF token")
    return m.group(1)


def _pick_by_name(items: list[dict[str, Any]], key: str, keyword: str) -> dict[str, Any]:
    hit = next((item for item in items if keyword in str(item.get(key, ""))), None)
    if hit is None:
        raise QueryError(f"未找到匹配项: {key} 包含 '{keyword}'")
    return hit


def _post_json(session: requests.Session, url: str, data: dict[str, str], headers: dict[str, str]) -> dict[str, Any]:
    resp = session.post(url, data=data, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    ctype = (resp.headers.get("Content-Type") or "").lower()
    body = resp.text.strip()
    if "application/json" not in ctype and not body.startswith("{"):
        raise ParseError(f"接口未返回 JSON: {url}")
    return resp.json()


def query_electric(session: requests.Session, target: DormQueryTarget) -> ElectricResult:
    try:
        # 第一步：打开页面拿 CSRF，并传入已知 CACHE room id 以保持与页面流程一致。
        page_resp = session.get(
            ELECTRIC_QUERY_URL,
            params={FIELD_ELCSYS_ID: target.elcsys_id},
            timeout=REQUEST_TIMEOUT,
        )
        page_resp.raise_for_status()
        page_text = page_resp.text or ""
        if "j_username" in page_text and "/epay/person/index" in page_text:
            raise QueryError("会话可能未登录或已失效")

        csrf = _extract_csrf_token(page_text)
        ajax_headers = {
            "X-CSRF-TOKEN": csrf,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }

        # 第二步：按校区->区域->楼栋->楼层->房间逐级定位 B202 的 roomNo。
        area_data = _post_json(session, ELECTRIC_AREA_API, {"sysid": target.elcsys_id}, ajax_headers)
        area = _pick_by_name(area_data.get("areas", []), "areaName", target.campus_name)
        area_id = str(area.get("areaId"))

        district_data = _post_json(
            session,
            ELECTRIC_DISTRICT_API,
            {"sysid": target.elcsys_id, "area": area_id},
            ajax_headers,
        )
        district = _pick_by_name(district_data.get("districts", []), "districtName", target.district_keyword)
        district_id = str(district.get("districtId"))

        build_data = _post_json(
            session,
            ELECTRIC_BUILDING_API,
            {"sysid": target.elcsys_id, "area": area_id, "district": district_id},
            ajax_headers,
        )
        build = _pick_by_name(build_data.get("buils", []), "buiName", target.building_keyword)
        build_id = str(build.get("buiId"))

        floor_data = _post_json(
            session,
            ELECTRIC_FLOOR_API,
            {"sysid": target.elcsys_id, "area": area_id, "district": district_id, "build": build_id},
            ajax_headers,
        )
        floor = _pick_by_name(floor_data.get("floors", []), "floorName", target.floor_name)
        floor_id = str(floor.get("floorId"))

        room_data = _post_json(
            session,
            ELECTRIC_ROOM_API,
            {
                "sysid": target.elcsys_id,
                "area": area_id,
                "district": district_id,
                "build": build_id,
                "floor": floor_id,
            },
            ajax_headers,
        )
        room = _pick_by_name(room_data.get("rooms", []), "roomName", target.room_name)
        room_no = str(room.get("roomId"))

        # 第三步：调用真实电量接口，读取 restElecDegree。
        bill_data = _post_json(
            session,
            ELECTRIC_BILL_API,
            {
                "sysid": target.elcsys_id,
                "roomNo": room_no,
                "elcarea": area_id,
                "elcbuis": build_id,
            },
            ajax_headers,
        )

        retcode = bill_data.get("retcode")
        if str(retcode) != "0":
            raise QueryError(f"电费接口返回失败: retcode={retcode}, retmsg={bill_data.get('retmsg')}")

        value = bill_data.get("restElecDegree")
        if value in (None, ""):
            raise ParseError("电费接口返回成功但缺少 restElecDegree")

        return ElectricResult(
            campus=target.campus_name,
            building=target.display_building,
            sub_building=target.display_sub_building,
            floor=target.floor_name,
            room=target.room_name,
            room_id=room_no,
            value=str(value),
            unit="度",
            update_time=None,
            raw={
                "queryPath": {
                    "area": area,
                    "district": district,
                    "build": build,
                    "floor": floor,
                    "room": room,
                },
                "bill": bill_data,
            },
        )

    except (requests.RequestException, ValueError, ParseError, QueryError) as exc:
        logging.debug("electric query failed", exc_info=True)
        raise QueryError(f"电费查询失败: {exc}") from exc


def result_to_json_dict(result: ElectricResult) -> dict[str, Any]:
    return {
        "campus": result.campus,
        "building": result.building,
        "subBuilding": result.sub_building,
        "floor": result.floor,
        "room": result.room,
        "roomId": result.room_id,
        "value": result.value,
        "unit": result.unit,
        "updateTime": result.update_time,
        "raw": result.raw,
    }


def result_to_pretty_text(result: ElectricResult) -> str:
    lines = [
        f"房间：{result.campus} {result.building} {result.sub_building} {result.floor} {result.room}",
        f"剩余电量/金额：{result.value if result.value is not None else '未解析到'}"
        + (f"（单位：{result.unit}）" if result.unit else ""),
        f"数据时间：{result.update_time if result.update_time else '未知'}",
    ]
    return "\n".join(lines)
