"""HDVIA 1.30.1 guide decision engine: situation -> assessment -> action."""
from __future__ import annotations
from typing import Any, Dict, List

def assess_and_act(object_type: str, weather: Dict[str, Any] | None = None,
                   crowd: str | None = None, guest_profile: Dict[str, Any] | None = None,
                   operational: Dict[str, Any] | None = None) -> Dict[str, Any]:
    w = weather or {}; g = guest_profile or {}; o = operational or {}
    risks: List[str] = []; actions: List[str] = []; plan_b: List[str] = []
    rain = w.get("max_rain_probability"); wind = w.get("max_wind_kmh"); temp = w.get("max_temperature_c")
    if isinstance(rain, (int, float)) and rain >= 70:
        risks.append("mưa cao"); actions.append("Giảm phụ thuộc vào hoạt động ngoài trời và kiểm tra phương án che mưa.")
        plan_b.append("Chuyển sang điểm/hoạt động trong nhà phù hợp hoặc rút ngắn thời gian ngoài trời.")
    if isinstance(wind, (int, float)) and wind >= 30:
        risks.append("gió mạnh"); actions.append("Kiểm tra điều kiện an toàn thực tế trước hoạt động trên nước/cao điểm.")
        plan_b.append("Hoãn hoạt động nhạy cảm với gió và thay bằng nội dung tham quan an toàn hơn.")
    if isinstance(temp, (int, float)) and temp >= 35:
        risks.append("nắng nóng"); actions.append("Tăng điểm nghỉ, nước uống và tránh đứng ngoài trời quá lâu.")
    if crowd in {"HIGH", "VERY_HIGH"}:
        risks.append("đông khách"); actions.append("Quy định điểm tập kết và thời gian quay lại trước khi tách nhóm.")
        plan_b.append("Đổi khung giờ hoặc thứ tự điểm tham quan để giảm thời gian chờ.")
    if g.get("elderly") or g.get("children") or g.get("mobility_limit"):
        risks.append("nhóm có nhu cầu hỗ trợ"); actions.append("Ưu tiên quãng đi bộ hợp lý, chỗ nghỉ và điểm tiếp cận thuận tiện.")
    if o.get("ticket_required"):
        actions.append("Kiểm tra vé/quy định vào cửa trước khi đoàn di chuyển.")
    if not actions:
        actions.append("Kiểm tra điều kiện thực tế trước khi đưa đoàn vào điểm.")
    return {"status": "ACTIONABLE", "assessment": {"object_type": object_type, "risks": risks, "signals": w},
            "actions": list(dict.fromkeys(actions)), "plan_b": list(dict.fromkeys(plan_b)),
            "decision": "Ưu tiên an toàn và trải nghiệm khách; nếu điều kiện thay đổi, chuyển sang phương án B đã chuẩn bị.",
            "guest_profile": g}
