"""HDVIA 1.30.1 route/time decision layer."""
from __future__ import annotations
from typing import Any, Dict, List

def evaluate_route_time(object_type:str, operational:Dict[str,Any]|None=None, weather:Dict[str,Any]|None=None, guest_profile:Dict[str,Any]|None=None)->Dict[str,Any]:
    o=operational or {}; w=weather or {}; g=guest_profile or {}
    reasons=[]; actions=[]; plan_b=[]
    remaining=o.get("time_remaining_minutes"); travel=o.get("travel_minutes"); visit=o.get("visit_minutes"); buffer=o.get("buffer_minutes",15)
    if all(isinstance(x,(int,float)) for x in (remaining,travel,visit)):
        total=travel+visit+buffer
        if total>remaining:
            reasons.append("Không đủ quỹ thời gian theo dữ liệu hành trình.")
            actions.append("Rút ngắn thời gian tại điểm hoặc bỏ điểm ít ưu tiên.")
            plan_b.append("Chuyển sang điểm gần hơn hoặc hoạt động ngắn hơn.")
        else:
            reasons.append(f"Quỹ thời gian dự kiến còn đủ: cần khoảng {int(total)} phút, còn {int(remaining)} phút.")
    if isinstance(travel,(int,float)) and travel>=45 and (g.get("elderly") or g.get("children") or g.get("mobility_limit")):
        actions.append("Kiểm tra điểm nghỉ và khả năng tiếp cận trước đoạn di chuyển dài.")
    if (w.get("max_rain_probability") or 0)>=70:
        actions.append("Tính thời gian trú mưa vào kế hoạch thay vì chỉ tính thời gian tham quan.")
        plan_b.append("Đổi thứ tự sang điểm trong nhà/ít phụ thuộc thời tiết nếu có dữ liệu phù hợp.")
    return {"status":"ROUTE_DECISION_READY","object_type":object_type,"assessment":{"reasons":reasons,"estimated_total_minutes":(travel+visit+buffer if all(isinstance(x,(int,float)) for x in (travel,visit)) else None)},"actions":list(dict.fromkeys(actions)),"plan_b":list(dict.fromkeys(plan_b))}
