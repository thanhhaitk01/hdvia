from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]

def test_normalize_is_inside_safe_analyze_try():
    src=(ROOT/'app.py').read_text(encoding='utf-8')
    start=src.index('def _safe_journey_analyze')
    end=src.index('\n\n@app.route("/journey"', start)
    block=src[start:end]
    assert 'try:\n        title, itinerary = _normalize_journey_input' in block
    assert 'except Exception as exc:' in block

def test_journey_post_has_outer_exception_boundary():
    src=(ROOT/'app.py').read_text(encoding='utf-8')
    start=src.index('def journey():')
    end=src.index('\n\n@app.post("/api/v1/journey/analyze")', start)
    block=src[start:end]
    assert 'if request.method=="POST":\n        try:' in block
    assert 'traceback.print_exc()' in block

def test_engine_has_parallel_weather_fallback():
    src=(ROOT/'journey_engine/engine.py').read_text(encoding='utf-8')
    assert 'ThreadPoolExecutor' in src
    assert 'self._fallback_weather()' in src
