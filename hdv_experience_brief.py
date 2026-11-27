"""HDVIA 1.30.1 HDV Brief: turn evidence into usable guide preparation."""
from __future__ import annotations
from typing import Any, Dict, List

def build_hdv_brief(name: str, object_info: Dict[str, Any], profile: Dict[str, Any] | None = None,
                    story_graph: Dict[str, Any] | None = None) -> Dict[str, Any]:
    p = profile or {}
    types = object_info.get("types") or [object_info.get("primary_type", "UNKNOWN")]
    primary = object_info.get("primary_type", "UNKNOWN")
    sources = list(dict.fromkeys(str(x) for x in (p.get("sources") or []) if x))
    verified = [str(x) for x in (p.get("verified_facts") or []) if x]
    gaps = [str(x) for x in (p.get("knowledge_gaps") or []) if x]
    highlights = [str(x) for x in (p.get("highlights") or []) if x][:5]
    if not highlights:
        highlights = verified[:5]
    tell = [
        f"Giới thiệu ngắn: {name} là đối tượng thuộc nhóm {primary.replace('_', ' ').lower()}.",
        "Ưu tiên kể 1 câu chuyện có nguồn, sau đó cho khách một chi tiết cụ thể để quan sát hoặc trải nghiệm.",
    ]
    if story_graph and story_graph.get("narrative_order"):
        tell.append("Mạch kể gợi ý: " + " → ".join(story_graph["narrative_order"][:6]) + ".")
    avoid = [
        "Không biến thông tin chưa kiểm chứng thành sự thật chắc chắn.",
        "Không dùng ngày sự kiện cũ như ngày hiện tại nếu chưa xác minh thời gian.",
    ]
    guest_questions = [
        {"question": "Điểm này có gì đáng xem?", "answer": "Chọn 2–3 giá trị nổi bật nhất đã được kiểm chứng."},
        {"question": "Điều gì đặc biệt ở nơi này?", "answer": "Trả lời bằng câu chuyện, chi tiết quan sát được và bối cảnh địa phương."},
    ]
    return {
        "object_name": name, "object_types": types, "why_guests_care": highlights[:3] or ["Giá trị cần xác định từ nguồn đáng tin cậy."],
        "highlights": highlights, "story_to_tell": tell, "do_not_say_without_verification": avoid,
        "suggested_explanation_minutes": 5 if primary in {"FOOD", "ATTRACTION", "EVENT"} else 8,
        "likely_guest_questions": guest_questions, "sources": sources, "verified_facts": verified,
        "knowledge_gaps": gaps, "experience_level": "HDV_GIAU_KINH_NGHIEM",
    }
