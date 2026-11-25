"""HDVIA Knowledge Expansion Engine.

Adds a controlled expansion layer on top of the existing 7-layer Journey Data
Fusion foundation. It does not auto-publish arbitrary web content: external and
HDV contributions remain candidates until provenance/validation rules pass.
"""
from __future__ import annotations
import json, os, re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

BASE=os.path.dirname(__file__)
KB_FILE=os.path.join(BASE,"data","knowledge_base.json")
PROFILE_FILE=os.path.join(BASE,"data","tourist_profiles.json")

KNOWLEDGE_DOMAINS=("geography","history","culture","people","food","tourism","nature","operations","guide_experience")
PROFILE_WEIGHTS={
    "general": {"history":1.0,"culture":1.0,"food":1.0,"tourism":1.0,"guide_experience":1.0},
    "india": {"history":1.1,"culture":1.2,"food":1.1,"tourism":1.0,"guide_experience":1.0},
    "korea": {"tourism":1.2,"food":1.0,"culture":1.0,"nature":1.1,"guide_experience":1.0},
    "europe": {"history":1.2,"culture":1.2,"architecture":1.1,"nature":1.0,"guide_experience":1.0},
}

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
def norm(s): return " ".join(re.findall(r"[\wÀ-ỹĐđ]+",str(s or "").lower(),flags=re.UNICODE))

def _load(path, default):
    try:
        with open(path,encoding="utf-8") as f: return json.load(f)
    except Exception: return default

def coverage(name: str) -> Dict[str,Any]:
    q=norm(name); entries=_load(KB_FILE,{"entries":[]}).get("entries",[])
    counts={d:0 for d in KNOWLEDGE_DOMAINS}
    matched=[]
    for item in entries:
        hay=norm(" ".join([item.get("title",""),item.get("destination",""),item.get("category",""),item.get("summary",""),item.get("content","")]))
        if q and q in hay:
            matched.append(item)
            cat=norm(item.get("category"))
            mapping={"địa lý":"geography","địa hình":"geography","lịch sử":"history","văn hóa":"culture","con người":"people","ẩm thực":"food","du lịch":"tourism","thiên nhiên":"nature","điều hành":"operations","kinh nghiệm":"guide_experience"}
            assigned=next((v for k,v in mapping.items() if k in cat),"tourism")
            counts[assigned]+=1
    populated=sum(1 for v in counts.values() if v)
    gaps=[k for k,v in counts.items() if not v]
    score=round((populated/len(counts))*100,1)
    return {"destination":name,"score":score,"counts":counts,"gaps":gaps,"matched_entries":len(matched),"updated_at":now()}

def knowledge_gaps(name: str, *, profile: str="general") -> List[Dict[str,Any]]:
    c=coverage(name); gaps=[]
    weights=PROFILE_WEIGHTS.get(norm(profile),PROFILE_WEIGHTS["general"])
    for domain in c["gaps"]:
        priority=weights.get(domain,1.0)
        gaps.append({"domain":domain,"priority":priority,"reason":f"Chưa có dữ liệu đủ trong kho curated cho {name}.","action":"COLLECT_AND_VALIDATE"})
    gaps.sort(key=lambda x:(-x["priority"],x["domain"]))
    return gaps

def profile_answer(entries: Iterable[Dict[str,Any]], profile: str="general", limit:int=5) -> List[Dict[str,Any]]:
    weights=PROFILE_WEIGHTS.get(norm(profile),PROFILE_WEIGHTS["general"])
    scored=[]
    for item in entries:
        domain=norm(item.get("domain") or item.get("category") or "tourism")
        score=weights.get(domain,1.0)
        scored.append((score,item))
    scored.sort(key=lambda x:(-x[0],x[1].get("id",x[1].get("title",""))))
    return [x[1] for x in scored[:limit]]

def graph_for_destination(name: str) -> Dict[str,Any]:
    q=norm(name); entries=_load(KB_FILE,{"entries":[]}).get("entries",[])
    nodes={"destination":[],"topic":[],"place":[],"experience":[]}; edges=[]
    nodes["destination"].append({"id":f"dest:{q}","label":name})
    seen=set()
    for item in entries:
        hay=norm(" ".join([item.get("destination",""),item.get("title",""),item.get("keywords",[]).__str__()]))
        if q not in hay: continue
        tid=f"topic:{item.get('id')}"
        if tid not in seen:
            seen.add(tid); nodes["topic"].append({"id":tid,"label":item.get("title"),"domain":item.get("category")})
            edges.append({"from":f"dest:{q}","to":tid,"type":"HAS_KNOWLEDGE"})
        for kw in (item.get("keywords") or [])[:8]:
            pid=f"place:{norm(kw)}"
            if len(norm(kw))<3: continue
            if not any(x["id"]==pid for x in nodes["place"]): nodes["place"].append({"id":pid,"label":kw})
            edges.append({"from":tid,"to":pid,"type":"MENTIONS"})
    return {"destination":name,"nodes":nodes,"edges":edges,"node_count":sum(map(len,nodes.values())),"edge_count":len(edges),"version":"1.0.0"}

class KnowledgeExpansionEngine:
    VERSION="1.0.0"
    def inspect(self,name: str, *, tourist_profile: str="general") -> Dict[str,Any]:
        return {"version":self.VERSION,"coverage":coverage(name),"gaps":knowledge_gaps(name,profile=tourist_profile),"graph":graph_for_destination(name)}
    def rank(self, entries: Iterable[Dict[str,Any]], tourist_profile: str="general", limit:int=5) -> List[Dict[str,Any]]:
        return profile_answer(entries,tourist_profile,limit)
    def contribution(self, *, destination:str,title:str,content:str,source:str="HDV contribution") -> Dict[str,Any]:
        if not destination.strip() or not title.strip() or not content.strip(): raise ValueError("destination/title/content required")
        return {"status":"CANDIDATE","destination":destination.strip(),"title":title.strip(),"content":content.strip()[:12000],"source":source,"source_type":"guide","provenance_required":True,"created_at":now()}
