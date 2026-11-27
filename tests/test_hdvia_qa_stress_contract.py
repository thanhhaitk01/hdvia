from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_world_hdvia_stress_topics_are_defined():
    topics={
        "DESTINATION":"Hội An có gì nổi bật?",
        "HISTORY":"Lịch sử Hội An là gì?",
        "CULTURE":"Văn hóa Hội An có gì đặc sắc?",
        "FOOD":"Hội An có món gì đặc sản?",
        "GUIDE_SCRIPT":"Thuyết minh Hội An cho khách thế nào?",
        "WEATHER":"Thời tiết Hội An thế nào?",
        "ROUTE":"Từ Hội An đi Huế mất bao lâu?",
        "RISK":"Hội An có rủi ro gì cần lưu ý?",
        "PLAN_B":"Nếu mưa ở Hội An thì Plan B thế nào?",
        "TRANSPORT":"Giao thông ở Hội An thế nào?",
        "PEOPLE":"Người dân Hội An có đặc điểm gì?",
        "ECONOMY":"Kinh tế Hội An nổi bật ở đâu?",
    }
    assert len(topics)==12
    assert all(isinstance(q,str) and q for q in topics.values())

def test_image_contract_exists_for_curated_places():
    from media_defaults import media_for_slug
    from destination_catalog import DESTINATIONS
    curated={"ha-noi","ha-long","hue","da-nang","hoi-an","my-son","nha-trang","da-lat"}
    slugs={d["slug"] for d in DESTINATIONS}
    assert curated.issubset(slugs)
    for slug in curated:
        m=media_for_slug(slug)
        assert m["image_url"].startswith("https://commons.wikimedia.org/wiki/Special:Redirect/file/")
        assert m["source_url"].startswith("https://commons.wikimedia.org/wiki/File:")
        assert m["license"] and m["artist"]
