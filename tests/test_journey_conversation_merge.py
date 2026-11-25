from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def _load_merge_helper():
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_merge_conversation_result")
    module = ast.Module(body=[node], type_ignores=[])
    ns = {}
    exec(compile(module, str(ROOT / "app.py"), "exec"), ns)
    return ns["_merge_conversation_result"]


def test_conversation_merge_preserves_journey_intelligence_fields():
    merge = _load_merge_helper()
    journey = {
        "days": [{"day": 1, "text": "Huế"}],
        "places": [{"name": "Huế"}],
        "weather": {"Huế": [{"date": "2026-11-25", "rain": 70}]},
        "risk_map": {"Huế": {"level": "HIGH"}},
        "risks": [{"place": "Huế", "level": "HIGH"}],
        "plan_b": [{"day": 1, "trigger": "Rủi ro tại Huế"}],
        "briefing": [{"day": 1, "title": "Ngày 1 — Huế"}],
    }
    conversation = {
        "answer": "Huế: xác suất mưa cao nhất trong 7 ngày là khoảng 70%.",
        "intent": "WEATHER",
        "days": [],
        "places": [{"name": "Huế"}],
        "weather": {},
        "risk_map": {},
        "risks": [],
        "plan_b": [],
        "predicted_questions": ["Nếu trời mưa thì nên đổi lịch thế nào?"],
    }
    merged = merge(journey, conversation)
    assert merged["days"] == journey["days"]
    assert merged["weather"] == journey["weather"]
    assert merged["risk_map"] == journey["risk_map"]
    assert merged["risks"] == journey["risks"]
    assert merged["plan_b"] == journey["plan_b"]
    assert merged["briefing"] == journey["briefing"]
    assert merged["answer"] == conversation["answer"]
    assert merged["intent"] == "WEATHER"
