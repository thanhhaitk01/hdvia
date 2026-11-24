"""HDVIA 8-domain linked data core.

Additive to the legacy warehouse.  All eight domains use stable IDs and explicit
foreign-key-like references so Journey -> Destination -> Administrative ->
Knowledge/Experience/Weather/Risk/Market/Lineage can be resolved as one context.
"""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

BASE=os.path.dirname(__file__)
ROOT=os.path.join(BASE,"data","warehouse")
SCHEMA=os.path.join(ROOT,"schema_v2.json")
SEED=os.path.join(ROOT,"seed_v2.json")
COLLECTIONS=("administrative","destinations","knowledge","experiences","weather_risk","journeys","market","lineage")

ID_FIELDS={
    "administrative":"admin_id","destinations":"destination_id","knowledge":"knowledge_id",
    "experiences":"experience_id","weather_risk":"risk_id","journeys":"journey_id",
    "market":"market_id","lineage":"lineage_id",
}

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
def load(path, default):
    try:
        with open(path,"r",encoding="utf-8") as f: return json.load(f)
    except (FileNotFoundError,json.JSONDecodeError): return default

def schema(): return load(SCHEMA,{"collections":{}})
def seed(): return load(SEED,{k:[] for k in COLLECTIONS})

def validate(kind: str, payload: Dict[str,Any]) -> Dict[str,Any]:
    if kind not in COLLECTIONS: raise ValueError("Kho dữ liệu không hợp lệ")
    meta=schema()["collections"][kind]
    data={str(k):v for k,v in payload.items() if str(k) not in {"csrf_token","kind"}}
    # Backward-compatible IDs: old callers may omit IDs; the linked core assigns
    # deterministic IDs from the natural key before validation.
    id_field=ID_FIELDS[kind]
    if not data.get(id_field):
        natural=(data.get("slug") or data.get("title") or data.get("name") or data.get("record_ref") or data.get("location_code") or "record")
        import re
        slug=re.sub(r"[^a-z0-9]+","-",str(natural).lower()).strip("-") or "record"
        prefix={"administrative":"adm","destinations":"dst","knowledge":"kn","experiences":"exp","weather_risk":"risk","journeys":"jny","market":"mkt","lineage":"lin"}[kind]
        data[id_field]=f"{prefix}:{slug}"
    if kind in {"destinations","knowledge","experiences","weather_risk","market"} and not data.get("admin_id") and data.get("province_code"):
        data["admin_id"]=f"adm:{data['province_code']}"
    missing=[k for k in meta["required"] if data.get(k) is None or (isinstance(data.get(k),str) and not data.get(k).strip())]
    if missing: raise ValueError("Thiếu trường bắt buộc: "+", ".join(missing))
    data.setdefault("status","ACTIVE")
    data["updated_at"]=now()
    return data

def lineage_for(kind, record_id, *, source, source_type="manual", confidence="UNASSESSED", version="1.0.0", license=""):
    return validate("lineage", {"lineage_id":f"lin:{kind}:{record_id}","record_ref":f"{kind}:{record_id}","source":source,"source_type":source_type,"collected_at":now(),"confidence":confidence,"version":version,"license":license,"status":"ACTIVE"})

def index_records(records: Iterable[Dict[str,Any]], kind: str):
    field=ID_FIELDS[kind]
    return {str(r.get(field)):r for r in records if r.get(field)}

def resolve_context(records_by_kind: Dict[str,List[Dict[str,Any]]], *, journey_id=None, destination_id=None, admin_id=None):
    """Resolve a connected context graph. Returns only linked records, never guessed links."""
    out={k:[] for k in COLLECTIONS}
    idx={k:index_records(records_by_kind.get(k,[]),k) for k in COLLECTIONS}
    j=idx["journeys"].get(journey_id) if journey_id else None
    if j:
        out["journeys"]=[j]
        destination_ids=[str(x) for x in j.get("destination_ids",[]) ]
    else:
        destination_ids=[str(destination_id)] if destination_id else []
    destinations=[idx["destinations"][x] for x in destination_ids if x in idx["destinations"]]
    if admin_id: admin_ids=[str(admin_id)]
    else: admin_ids=sorted({str(d.get("admin_id")) for d in destinations if d.get("admin_id")})
    admins=[idx["administrative"][x] for x in admin_ids if x in idx["administrative"]]
    out["destinations"]=destinations; out["administrative"]=admins
    destset=set(destination_ids); adminset=set(admin_ids)
    out["knowledge"]=[r for r in records_by_kind.get("knowledge",[]) if str(r.get("destination_id")) in destset or str(r.get("admin_id")) in adminset]
    out["experiences"]=[r for r in records_by_kind.get("experiences",[]) if str(r.get("destination_id")) in destset or str(r.get("admin_id")) in adminset]
    out["weather_risk"]=[r for r in records_by_kind.get("weather_risk",[]) if str(r.get("destination_id")) in destset or str(r.get("admin_id")) in adminset]
    out["market"]=[r for r in records_by_kind.get("market",[]) if str(r.get("destination_id")) in destset or str(r.get("admin_id")) in adminset or str(r.get("admin_id"))=="GLOBAL"]
    refs={f"{k}:{r.get(ID_FIELDS[k])}" for k,rows in out.items() for r in rows if r.get(ID_FIELDS[k]) and k!="lineage"}
    out["lineage"]=[r for r in records_by_kind.get("lineage",[]) if str(r.get("record_ref")) in refs]
    return out

class LearningPipeline:
    """Candidate -> validated -> reviewed -> published; never auto-publishes."""
    VERSION="2.0.0-linked"
    def ingest(self, *, kind, payload, source, source_type="external"):
        record=validate(kind,payload)
        rid=record.get(ID_FIELDS[kind],"candidate")
        return {"status":"CANDIDATE","kind":kind,"record":record,"lineage":lineage_for(kind,rid,source=source,source_type=source_type,version=self.VERSION)}
    def validate(self, item):
        issues=[]
        if not item.get("lineage",{}).get("source"): issues.append("MISSING_SOURCE")
        if kind_requires_provenance(item.get("kind")) and not item.get("lineage",{}).get("source"): issues.append("MISSING_PROVENANCE")
        item["status"]="VALIDATED" if not issues else "REJECTED"; item["issues"]=issues; return item
    def review(self,item,approved=False,reviewer=""):
        item["reviewed_by"]=reviewer; item["reviewed_at"]=now(); item["status"]="PUBLISHED" if approved else "REJECTED"; return item

def kind_requires_provenance(kind): return kind in {"administrative","knowledge","experiences","weather_risk","market","lineage"}

def graph_integrity_report(records_by_kind: Dict[str,List[Dict[str,Any]]]) -> Dict[str,Any]:
    """Check that every cross-domain reference resolves to a known master record."""
    ids={k:set(str(r.get(ID_FIELDS[k])) for r in records_by_kind.get(k,[]) if r.get(ID_FIELDS[k])) for k in COLLECTIONS}
    checks=[]
    def check(condition, code, detail): checks.append({"code":code,"ok":bool(condition),"detail":detail})
    for r in records_by_kind.get("destinations",[]):
        check(str(r.get("admin_id")) in ids["administrative"],"DEST_ADMIN_LINK",r.get("destination_id"))
    for kind in ("knowledge","experiences","weather_risk","market"):
        for r in records_by_kind.get(kind,[]):
            if r.get("destination_id"):
                check(str(r.get("destination_id")) in ids["destinations"],f"{kind.upper()}_DEST_LINK",r.get(ID_FIELDS[kind]))
            if r.get("admin_id"):
                check(str(r.get("admin_id")) in ids["administrative"],f"{kind.upper()}_ADMIN_LINK",r.get(ID_FIELDS[kind]))
    for r in records_by_kind.get("journeys",[]):
        for did in r.get("destination_ids",[]) or []:
            check(str(did) in ids["destinations"],"JOURNEY_DEST_LINK",r.get("journey_id"))
    non_lineage={f"{k}:{r.get(ID_FIELDS[k])}" for k in COLLECTIONS if k!="lineage" for r in records_by_kind.get(k,[]) if r.get(ID_FIELDS[k])}
    for r in records_by_kind.get("lineage",[]):
        check(str(r.get("record_ref")) in non_lineage,"LINEAGE_RECORD_LINK",r.get("lineage_id"))
    failed=[x for x in checks if not x["ok"]]
    return {"ok":not failed,"checks":len(checks),"failed":failed,"counts":{k:len(v) for k,v in records_by_kind.items()}}
