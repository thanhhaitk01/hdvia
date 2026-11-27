"""HDVIA 1.30.1 source conflict detection and verification guard."""
from __future__ import annotations
from typing import Any, Dict, Iterable, List

def detect_conflicts(evidence:Iterable[Dict[str,Any]]|None)->Dict[str,Any]:
    rows=[x for x in evidence or [] if isinstance(x,dict) and str(x.get("fact") or x.get("text") or "").strip()]
    groups:Dict[str,List[Dict[str,Any]]]={}
    for r in rows:
        subject=str(r.get("subject") or r.get("claim_key") or "").strip().lower()
        if subject: groups.setdefault(subject,[]).append(r)
    conflicts=[]
    for subject,items in groups.items():
        vals={str(i.get("fact") or i.get("text") or "").strip().lower() for i in items}
        if len(vals)>1:
            conflicts.append({"subject":subject,"claims":[{"source":i.get("source") or "UNKNOWN","fact":i.get("fact") or i.get("text") or "","updated_at":i.get("updated_at"),"confidence":i.get("confidence","UNKNOWN")} for i in items]})
    return {"has_conflict":bool(conflicts),"conflicts":conflicts,"policy":"Không tự ý chọn một tuyên bố chỉ vì nguồn được xếp hạng cao; nếu mâu thuẫn ảnh hưởng quyết định, yêu cầu kiểm chứng nguồn chính thức mới nhất."}
