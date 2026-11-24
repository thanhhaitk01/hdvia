"""HDVIA AI Copilot foundation.

Provider-neutral orchestration layer: combines Journey Intelligence, knowledge,
weather/risk context and deterministic recommendations. A future LLM provider can
replace `compose()` without changing the HTTP contract.
"""
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timezone

class CopilotEngine:
    VERSION = "1.0.0-foundation"

    def compose(self, *, user: Dict[str, Any], journey: Dict[str, Any] | None,
                question: str = "", data_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        q = (question or "").strip()
        context = journey or {}
        data_context = data_context or context.get("data_context") or {}
        linked_counts = {k: len(v) for k, v in data_context.items() if isinstance(v, list)}
        risks = []
        for item in (context.get("risks") or []):
            if item.get("level") in ("HIGH", "MEDIUM"):
                risks.append(f"{item.get('place')}: {item.get('level')}")
        recommendations: List[str] = []
        if risks:
            recommendations.append("Ưu tiên các điểm có rủi ro và chuẩn bị Plan B trước khi khởi hành.")
        else:
            recommendations.append("Lịch trình hiện chưa có cảnh báo lớn từ dữ liệu đã phân tích.")
        if context:
            recommendations.append("Kiểm tra lại thời gian di chuyển, buffer và nhu cầu khách trước mỗi chặng.")
        if q:
            answer = f"Tôi đã đưa yêu cầu của anh vào ngữ cảnh HDVIA. {q}"
        else:
            answer = "Tôi đã tổng hợp ngữ cảnh hành trình, thời tiết, rủi ro và Plan B để hỗ trợ HDV."
        return {
            "ok": True,
            "engine": "HDVIA AI Copilot",
            "version": self.VERSION,
            "answer": answer,
            "context": {"journey_loaded": bool(context), "risk_count": len(risks), "user_role": user.get("role"), "data_core_linked": bool(data_context), "data_core_counts": linked_counts},
            "risk_summary": risks,
            "recommendations": recommendations,
            "next_actions": ["Xem lại cảnh báo", "Kiểm tra Plan B", "Đối chiếu tri thức và kinh nghiệm HDV"] if context else ["Nhập hành trình để bắt đầu"],
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
