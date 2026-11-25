"""Deterministic destination knowledge graph for HDVIA.

The graph is intentionally small and explainable: destination -> knowledge topic ->
mentioned place/topic. External data can enrich nodes but is never promoted to
verified status by graph construction alone.
"""
from __future__ import annotations
import json, os, re
from typing import Any, Dict

BASE=os.path.dirname(__file__)
KB=os.path.join(BASE,"data","knowledge_base.json")

def norm(s): return " ".join(re.findall(r"[\wÀ-ỹĐđ]+",str(s or "").lower(),flags=re.UNICODE))

def _load():
    try:
        with open(KB,encoding="utf-8") as f: return json.load(f).get("entries",[])
    except Exception: return []

def build(name: str, live: Dict[str,Any]|None=None) -> Dict[str,Any]:
    live=live or {}; target=norm(name)
    nodes={"destination":[],"topic":[],"place":[],"source":[]}; edges=[]; seen=set()
    did=f"destination:{target}"
    nodes["destination"].append({"id":did,"label":name,"verified":True})
    for item in _load():
        hay=norm(" ".join([item.get("title",""),item.get("destination",""),item.get("category",""),item.get("summary","")," ".join(item.get("keywords") or [])]))
        if target not in hay: continue
        tid=f"topic:{item.get('id') or norm(item.get('title'))}"
        if tid in seen: continue
        seen.add(tid)
        nodes["topic"].append({"id":tid,"label":item.get("title"),"domain":item.get("category"),"verified":True})
        edges.append({"from":did,"to":tid,"type":"HAS_KNOWLEDGE"})
        src=item.get("source") or "HDVIA curated KB"; sid=f"source:{norm(src)}"
        if sid not in {x["id"] for x in nodes["source"]}: nodes["source"].append({"id":sid,"label":src,"verified":True})
        edges.append({"from":tid,"to":sid,"type":"SUPPORTED_BY"})
        for kw in (item.get("keywords") or [])[:8]:
            pid=f"place:{norm(kw)}"
            if len(norm(kw))<3: continue
            if pid not in {x["id"] for x in nodes["place"]}: nodes["place"].append({"id":pid,"label":kw,"verified":True})
            edges.append({"from":tid,"to":pid,"type":"MENTIONS"})
    for key, label, typ in (("osm","OpenStreetMap","external"),("wikipedia","Wikipedia","external"),("wikidata","Wikidata","external")):
        rows=((live.get(key) or {}).get("results") or [])
        for row in rows[:3]:
            lbl=row.get("name") or row.get("title") or row.get("display_name")
            if not lbl: continue
            sid=f"source:{label.lower()}"; nid=f"{typ}:{key}:{norm(lbl)}"
            if nid not in {x["id"] for group in nodes.values() for x in group}: nodes["place"].append({"id":nid,"label":lbl,"verified":False,"source":label})
            edges.append({"from":did,"to":nid,"type":"EXTERNAL_REFERENCE","verified":False})
            if sid not in {x["id"] for x in nodes["source"]}: nodes["source"].append({"id":sid,"label":label,"verified":False})
            edges.append({"from":nid,"to":sid,"type":"FROM_SOURCE","verified":False})
    return {"version":"1.1.0","destination":name,"nodes":nodes,"edges":edges,"node_count":sum(len(v) for v in nodes.values()),"edge_count":len(edges)}
