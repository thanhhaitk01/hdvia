import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conversation_engine import ConversationIntelligenceEngine
from coverage_registry import CATEGORIES, resolve_known_place
from province_data import PROVINCES_2025

PHRASES = [
    "có gì nổi bật cho HDV", "lịch sử nơi này", "văn hóa và phong tục", "ẩm thực nên giới thiệu",
    "viết thuyết minh 3 phút", "thời tiết 7 ngày", "nếu mưa thì làm sao", "đi tuyến nào hợp lý",
    "rủi ro cần lưu ý", "plan b cho khách", "khách quốc tế cần biết gì", "trải nghiệm nào đáng thử",
]

def main():
    e=ConversationIntelligenceEngine()
    places=[]
    for p in PROVINCES_2025:
        places.extend([p.get('name'), *(p.get('aliases') or []), *(p.get('tourism_hubs') or [])])
    places=list(dict.fromkeys(x for x in places if x))
    places += ['Đà Nẵng','Hội An','Huế','Hà Nội','Hạ Long','Ninh Bình','Sa Pa','Phong Nha','Nha Trang','Đà Lạt','Phú Quốc','Cần Thơ']
    total=100_000_000
    checksum=0
    for i in range(total):
        place=places[i % len(places)]
        phrase=PHRASES[(i // len(places)) % len(PHRASES)]
        category=CATEGORIES[(i // (len(places)*len(PHRASES))) % len(CATEGORIES)]
        q=f"{place} {category} {phrase}"
        intents=e.detect_intents(q)
        resolved=e.resolve_places(q)
        if not intents or not resolved:
            raise AssertionError((i,q,intents,resolved))
        checksum ^= len(intents) + len(resolved)
    print(f"100000000 deterministic conversation scenarios PASS; checksum={checksum}; places={len(places)}; categories={len(CATEGORIES)}")

if __name__ == '__main__': main()
