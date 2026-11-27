"""HDVIA Place Intelligence: point -> local commune -> live weather -> guide actions."""
from __future__ import annotations
import json, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Optional

VERSION = "1.30.1-hdv-giau-kinh-nghiem"


def _http_json(url: str, timeout: int = 8) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": os.getenv("HDVIA_API_USER_AGENT", "HDVIA-PlaceIntelligence/1.25.8")})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode(r.headers.get_content_charset() or "utf-8", errors="replace"))
    except Exception:
        return {}


def reverse_admin(lat: float, lon: float) -> Dict[str, Any]:
    """Best-effort reverse administrative context from OSM/Nominatim.

    We deliberately retain the raw address fields and a confidence marker because
    Vietnamese administrative naming can vary across providers and reorganizations.
    """
    q = urllib.parse.urlencode({"lat": lat, "lon": lon, "format": "jsonv2", "addressdetails": 1, "zoom": 18})
    data = _http_json("https://nominatim.openstreetmap.org/reverse?" + q)
    addr = data.get("address") or {}
    commune = (addr.get("village") or addr.get("town") or addr.get("municipality") or
               addr.get("suburb") or addr.get("city_district"))
    district = addr.get("county") or addr.get("district") or addr.get("city_district")
    province = addr.get("state") or addr.get("province") or addr.get("city")
    return {
        "commune": commune,
        "district": district,
        "province": province,
        "display_name": data.get("display_name"),
        "osm_type": data.get("osm_type"),
        "osm_id": data.get("osm_id"),
        "raw_address": addr,
        "source": "OpenStreetMap/Nominatim",
        "confidence": "MEDIUM" if commune else "LOW",
    }


def guide_actions(place_name: str, forecast: list, admin: Dict[str, Any], text: str = "") -> list:
    q = (place_name + " " + text).lower()
    rows = [x for x in forecast if isinstance(x, dict)]
    rain = max([x.get("rain") for x in rows if isinstance(x.get("rain"), (int, float))] or [0])
    wind = max([x.get("wind") for x in rows if isinstance(x.get("wind"), (int, float))] or [0])
    hot = max([x.get("tmax") for x in rows if isinstance(x.get("tmax"), (int, float))] or [0])
    severe = any((x.get("code") or -1) in {95, 96, 99} for x in rows)
    water = any(k in q for k in ("hồ", "ho ", "sông", "biển", "bãi", "thuyền", "cano", "tàu", "phú ninh"))
    outdoor = any(k in q for k in ("hồ", "ho ", "sông", "biển", "núi", "đồi", "vườn", "tham quan", "check-in", "ngoài trời", "phú ninh"))
    actions = []
    if outdoor:
        actions.append("Chuẩn bị trang phục gọn, đẹp và phù hợp hoạt động ngoài trời; mang giày dễ di chuyển.")
    if rain >= 45:
        actions.append("Khả năng mưa đáng lưu ý: HDV nên chuẩn bị áo mưa/ô, túi chống nước cho điện thoại và giấy tờ; nhắc khách trước khi đi.")
    if rain >= 70:
        actions.append("Mưa có xác suất cao: cần chuẩn bị Plan B trong nhà và rà lại thời gian tham quan.")
    if wind >= 30:
        actions.append("Gió mạnh: rà lại các hoạt động trên cao, ven hồ/sông/biển và phương án di chuyển; theo dõi cập nhật trước giờ khởi hành.")
    if water and wind >= 30:
        actions.append("Có hoạt động mặt nước và gió đáng chú ý: không tự ý cho khách lên thuyền/cano khi đơn vị vận hành hoặc cảnh báo an toàn không cho phép.")
    if severe:
        actions.append("Có tín hiệu dông mạnh: ưu tiên an toàn, tránh khu vực trống trải/mặt nước và sẵn sàng dừng hoạt động ngoài trời theo cảnh báo địa phương.")
    if hot >= 35:
        actions.append("Nắng nóng: chuẩn bị nước uống, mũ/nón, kem chống nắng và thời gian nghỉ phù hợp.")
    if not actions:
        actions.append("Thời tiết 7 ngày chưa cho thấy tín hiệu rủi ro lớn theo ngưỡng HDVIA; vẫn kiểm tra lại trước giờ khởi hành.")
    return actions


def build_place_intelligence(place: Dict[str, Any], weather: list, text: str = "") -> Dict[str, Any]:
    lat, lon = place.get("lat"), place.get("lon")
    admin = reverse_admin(float(lat), float(lon)) if lat is not None and lon is not None else {"confidence": "UNKNOWN"}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {
        "version": VERSION,
        "point": {"name": place.get("name"), "lat": lat, "lon": lon},
        "local_admin": admin,
        "weather_anchor": {"level": "POINT", "fallback_level": "COMMUNE" if admin.get("commune") else None,
                            "label": admin.get("commune") or place.get("name"),
                            "updated_at": now, "refresh_policy": "on_query + scheduled_watch"},
        "guide_actions": guide_actions(str(place.get("name") or ""), weather or [], admin, text),
        "disaster_watch": {
            "status": "DERIVED_WEATHER_RISK",
            "note": "Đây là cảnh báo suy luận từ dữ liệu thời tiết live; cảnh báo thiên tai chính thức cần được bổ sung từ cơ quan có thẩm quyền khi nguồn được cấu hình.",
        },
    }
