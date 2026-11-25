import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conversation_engine import ConversationIntelligenceEngine
from coverage_registry import CATEGORIES
from province_data import PROVINCES_2025
import argparse

PHRASES=["có gì nổi bật cho HDV","lịch sử nơi này","văn hóa và phong tục","ẩm thực nên giới thiệu","viết thuyết minh 3 phút","thời tiết 7 ngày","nếu mưa thì làm sao","đi tuyến nào hợp lý","rủi ro cần lưu ý","plan b cho khách","khách quốc tế cần biết gì","trải nghiệm nào đáng thử"]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--start',type=int); ap.add_argument('--count',type=int); ap.add_argument('--worker',type=int); a=ap.parse_args()
    e=ConversationIntelligenceEngine(); places=[]
    for p in PROVINCES_2025: places.extend([p.get('name'),*(p.get('aliases') or []),*(p.get('tourism_hubs') or [])])
    places=list(dict.fromkeys(x for x in places if x)); places += ['Đà Nẵng','Hội An','Huế','Hà Nội','Hạ Long','Ninh Bình','Sa Pa','Phong Nha','Nha Trang','Đà Lạt','Phú Quốc','Cần Thơ']
    checksum=0
    for j in range(a.count):
        i=a.start+j; place=places[i%len(places)]; phrase=PHRASES[(i//len(places))%len(PHRASES)]; cat=CATEGORIES[(i//(len(places)*len(PHRASES)))%len(CATEGORIES)]
        q=f"{place} {cat} {phrase} tình huống {i}"
        intents=e.detect_intents(q); resolved=e.resolve_places(q)
        if not intents or not resolved: raise AssertionError((i,q,intents,resolved))
        checksum=(checksum*131 + len(intents)*17 + len(resolved)) & 0xffffffff
    print(f'worker={a.worker} PASS count={a.count} checksum={checksum}', flush=True)
main()
