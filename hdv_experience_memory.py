"""HDVIA 1.30.1+ experience memory: reusable field lessons, not invented facts."""
from __future__ import annotations
from typing import Any, Dict, List

SCENARIO_RULES = [
    {"id":"HEAT_ELDERLY","when":lambda w,g,o: (w.get("max_temperature_c") or 0)>=35 and (g.get("elderly") or g.get("mobility_limit")),
     "lesson":"Đoàn có nhu cầu hỗ trợ + nắng nóng: giảm thời gian đứng ngoài trời, tăng điểm nghỉ và nước.",
     "actions":["Bố trí điểm nghỉ trước đoạn di chuyển dài.","Rút ngắn phần đứng thuyết minh ngoài trời.","Kiểm tra khả năng tiếp cận và nước uống."]},
    {"id":"RAIN_OUTDOOR","when":lambda w,g,o: (w.get("max_rain_probability") or 0)>=70,
     "lesson":"Mưa xác suất cao: không chờ mưa mới đổi phương án; chuẩn bị Plan B trước khi đoàn đến.",
     "actions":["Xác định điểm trú mưa.","Đảo thứ tự điểm nếu phù hợp.","Bảo vệ thiết bị và giấy tờ của HDV."]},
    {"id":"CROWD_TIME","when":lambda w,g,o: o.get("crowd_level") in {"HIGH","VERY_HIGH"} and o.get("time_remaining_minutes") is not None and o.get("time_remaining_minutes") < 120,
     "lesson":"Đông khách + ít thời gian: ưu tiên trải nghiệm cốt lõi thay vì cố hoàn thành toàn bộ điểm.",
     "actions":["Chốt điểm tập kết rõ ràng.","Rút gọn tuyến đi bộ.","Giữ dư thời gian cho việc quay lại xe/nhà hàng."]},
]

def build_experience_memory(object_type: str, weather: Dict[str, Any]|None=None, guest_profile: Dict[str,Any]|None=None, operational: Dict[str,Any]|None=None, prior_lessons: List[Dict[str,Any]]|None=None) -> Dict[str,Any]:
    w=weather or {}; g=guest_profile or {}; o=operational or {}
    matched=[]
    for rule in SCENARIO_RULES:
        try:
            if rule["when"](w,g,{**o,"crowd_level":o.get("crowd_level")}): matched.append(rule)
        except Exception: pass
    lessons=[{"id":r["id"],"object_type":object_type,"lesson":r["lesson"],"actions":r["actions"],"evidence_state":"RULE_BASED"} for r in matched]
    for row in prior_lessons or []:
        if isinstance(row,dict) and row.get("lesson"):
            lessons.append({"id":row.get("id","EXTERNAL_LESSON"),"object_type":row.get("object_type",object_type),"lesson":row["lesson"],"actions":list(row.get("actions") or []),"evidence_state":row.get("evidence_state","FIELD_MEMORY")})
    return {"mode":"HDV_EXPERIENCE_MEMORY","object_type":object_type,"matched_scenarios":len(matched),"lessons":lessons,"policy":"Chỉ coi bài học là kinh nghiệm áp dụng khi điều kiện tương tự; không biến kinh nghiệm thành sự thật lịch sử."}
