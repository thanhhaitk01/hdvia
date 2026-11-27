"""Curated representative media fallback for core HDVIA destinations.

These are remote Wikimedia Commons files whose file pages were reviewed for
place relevance and reuse metadata. The app still falls back to the live
VerifiedImageResolver for destinations not in this seed set.
"""
from __future__ import annotations
from urllib.parse import quote


def commons_file_url(filename: str) -> str:
    return "https://commons.wikimedia.org/wiki/Special:Redirect/file/" + quote(filename, safe="")


REPRESENTATIVE_MEDIA = {
    "ha-noi": {"filename": "Hanoi, Vietnam, Hoan Kiem Lake.jpg", "license": "CC BY 4.0", "artist": "Vyacheslav Argenberg", "source_url": "https://commons.wikimedia.org/wiki/File:Hanoi,_Vietnam,_Hoan_Kiem_Lake.jpg"},
    "ha-long": {"filename": "Ha Long Bay, Vietnam.jpg", "license": "CC BY 4.0", "artist": "Vyacheslav Argenberg", "source_url": "https://commons.wikimedia.org/wiki/File:Ha_Long_Bay,_Vietnam.jpg"},
    "hue": {"filename": "Hue - Vietnam.jpg", "license": "CC BY-SA 2.0", "artist": "Michael Tyler", "source_url": "https://commons.wikimedia.org/wiki/File:Hue_-_Vietnam.jpg"},
    "da-nang": {"filename": "Da Nang, Vietnam.jpg", "license": "CC0", "artist": "Quangpraha", "source_url": "https://commons.wikimedia.org/wiki/File:Da_Nang,_Vietnam.jpg"},
    "hoi-an": {"filename": "Chùa Cầu, Hội An.jpg", "license": "CC BY-SA 3.0", "artist": "François Guerraz", "source_url": "https://commons.wikimedia.org/wiki/File:Ch%C3%B9a_C%E1%BA%A7u,_H%E1%BB%99i_An.jpg"},
    "my-son": {"filename": "My Son Sanctuary Vietnam 01.jpg", "license": "CC BY 3.0", "artist": "Philip Nalangan", "source_url": "https://commons.wikimedia.org/wiki/File:My_Son_Sanctuary_Vietnam_01.jpg"},
    "nha-trang": {"filename": "Nha Trang Beach, Vietnam.jpg", "license": "CC BY-SA 3.0", "artist": "Ken Eckert", "source_url": "https://commons.wikimedia.org/wiki/File:Nha_Trang_Beach,_Vietnam.jpg"},
    "da-lat": {"filename": "Dalat, Vietnam.jpg", "license": "CC BY 2.0", "artist": "preetamrai", "source_url": "https://commons.wikimedia.org/wiki/File:Dalat,_Vietnam.jpg"},
}


def media_for_slug(slug: str) -> dict:
    item = REPRESENTATIVE_MEDIA.get(slug)
    if not item:
        return {}
    return {**item, "image_url": commons_file_url(item["filename"]), "status": "VERIFIED_SOURCE"}
