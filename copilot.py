"""HDVIA AI Copilot: context-grounded orchestration over the linked Data Core."""
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timezone

class CopilotEngine:
    VERSION = "2.0.0-context-grounded"

    def compose(self, *, user: Dict[str, Any], journey: Dict[str, Any] | None,
                question: str = "", data_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        q=(question or "").strip()
        context=journey or {}
        graph=data_context or context.get("data_context") or {}
        linked_counts={k:len(v) for k,v in graph.items() if isinstance(v,list)}
        destinations=[x for x in graph.get("destinations",[]) if isinstance(x,dict)]
        knowledge=[x for x in graph.get("knowledge",[]) if isinstance(x,dict)]
        experiences=[x for x in graph.get("experiences",[]) if isinstance(x,dict)]
        market=[x for x in graph.get("market",[]) if isinstance(x,dict)]
        weather=[x for x in graph.get("weather_risk",[]) if isinstance(x,dict)]
        risks=[]
        for item in weather:
            level=str(item.get("risk_level") or "UNKNOWN").upper()
            if level in ("HIGH","MEDIUM"):
                risks.append(f"{item.get('destination_id','điểm đến')}: {level}")
        names=[d.get("name") for d in destinations if d.get("name")]
        topics=[k.get("title") for k in knowledge[:5] if k.get("title")]
        tips=[e.get("content") for e in experiences[:3] if e.get("content")]
        insights=[m.get("insight") for m in market[:3] if m.get("insight")]

        answer_parts=[]
        if names:
            answer_parts.append("Ngữ cảnh dữ liệu đã liên kết: " + ", ".join(names) + ".")
        if q:
            answer_parts.append(f"Yêu cầu của HDV: {q}.")
        if topics:
            answer_parts.append("Tri thức đang có: " + "; ".join(topics) + ".")
        if risks:
            answer_parts.append("Có tín hiệu cần chú ý: " + ", ".join(risks) + ".")
        elif weather:
            answer_parts.append("Đã nhận context thời tiết/rủi ro của các điểm đã liên kết.")
        if insights:
            answer_parts.append("Góc nhìn thị trường: " + " | ".join(insights) + ".")
        if not answer_parts:
            answer_parts.append("Chưa có đủ context dữ liệu liên kết để trả lời chuyên sâu.")

        recommendations=[]
        if risks:
            recommendations += ["Ưu tiên các điểm có rủi ro MEDIUM/HIGH.","Chuẩn bị Plan B trước khi khởi hành và cập nhật dự báo gần giờ tour."]
        if tips:
            recommendations.append("Đối chiếu kinh nghiệm HDV đã được kiểm duyệt trước khi chốt phương án vận hành.")
        if not recommendations:
            recommendations.append("Tiếp tục kiểm tra thời tiết, thời gian di chuyển và nhu cầu khách trước mỗi chặng.")

        return {
            "ok":True,
            "engine":"HDVIA AI Copilot",
            "version":self.VERSION,
            "answer":" ".join(answer_parts),
            "context":{
                "journey_loaded":bool(context),"risk_count":len(risks),"user_role":user.get("role"),
                "data_core_linked":bool(graph),"data_core_counts":linked_counts,
                "destinations":names,"knowledge_topics":topics,"experience_count":len(experiences),"market_count":len(market),
            },
            "risk_summary":risks,
            "recommendations":recommendations,
            "next_actions":["Xem cảnh báo thời tiết","Kiểm tra Plan B","Đối chiếu tri thức và kinh nghiệm HDV"] if graph else ["Nhập hành trình để bắt đầu"],
            "generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        }
