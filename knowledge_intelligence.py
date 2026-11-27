"""HDVIA Knowledge Intelligence: four-layer destination cards + safe acquisition loop."""
from __future__ import annotations
import hashlib, json, os, re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List
from knowledge_expansion import KnowledgeExpansionEngine
from knowledge_graph import build as build_knowledge_graph
from knowledge_quality import assess as assess_knowledge_quality
from knowledge_self_healing import KnowledgeSelfHealingEngine, reference_lines

BASE=os.path.dirname(__file__)
KB_FILE=os.path.join(BASE,"data","knowledge_base.json")

LAYERS=("geography","culture_history","tourism","nature_operations")
STATES=("EXTERNAL","CANDIDATE","VALIDATED","PUBLISHED")

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
def norm(s): return re.sub(r"\s+"," ",str(s or "").strip().lower())
def tokens(s): return set(re.findall(r"[\wÀ-ỹĐđ]+",norm(s),flags=re.UNICODE))

def _load_kb():
    try:
        with open(KB_FILE,encoding="utf-8") as f: return json.load(f)
    except Exception: return {"entries":[]}

def _layer_for(item: Dict[str,Any]) -> str:
    c=norm(item.get("category")); k=norm(" ".join(item.get("keywords") or []))
    if any(x in c or x in k for x in ("địa lý","geograph","địa hình","vị trí")): return "geography"
    if any(x in c or x in k for x in ("văn hóa","lịch sử","di sản","tôn giáo","kiến trúc","cung đình")): return "culture_history"
    if any(x in c or x in k for x in ("ẩm thực","du lịch","tour","tham quan","trải nghiệm")): return "tourism"
    if any(x in c or x in k for x in ("thời tiết","rủi ro","thiên nhiên","biển","điều hành","kinh nghiệm")): return "nature_operations"
    return "tourism"

def destination_card(name: str, *, live: Dict[str,Any]|None=None, guide_experiences: Iterable[Dict[str,Any]]|None=None, tourist_profile: str="general") -> Dict[str,Any]:
    q=tokens(name); entries=[]
    for item in _load_kb().get("entries",[]):
        hay=tokens(" ".join([item.get("title",""),item.get("destination",""),item.get("category",""),item.get("summary",""),item.get("content","")])+" "+" ".join(item.get("keywords") or []))
        score=len(q & hay) + (3 if norm(item.get("destination"))==norm(name) else 0)
        if score: entries.append((score,item))
    entries.sort(key=lambda x:(-x[0],x[1].get("id","")))
    layers={k:[] for k in LAYERS}
    sources=[]
    for _,item in entries[:16]:
        layer=_layer_for(item); layers[layer].append({"title":item.get("title"),"summary":item.get("summary"),"content":item.get("content"),"source":item.get("source","HDVIA curated KB")})
        sources.append(item.get("source","HDVIA curated KB"))
    live=live or {}

    # Self-healing enrichment for Journey cards: if curated coverage is sparse,
    # acquire bounded reference evidence and inject it into the existing layers.
    # This does not modify the UI/module structure and never marks external data
    # as VERIFIED/PUBLISHED automatically.
    self_healing = None
    auto_heal = os.environ.get("HDVIA_AUTO_KNOWLEDGE_ENRICH", "1").strip().lower() in {"1", "true", "yes", "on"}
    if auto_heal:
        try:
            self_healing = KnowledgeSelfHealingEngine().ensure(name, profile=tourist_profile)
            if self_healing.get("ok"):
                profile = self_healing.get("profile") or {}
                blocks = profile.get("knowledge_blocks") or []
                for block in blocks[:6]:
                    domain = str(block.get("domain") or "tourism")
                    layer = "culture_history" if domain in {"history", "culture", "people"} else "tourism" if domain in {"food", "tourism", "economy"} else "nature_operations" if domain in {"nature"} else "geography"
                    text = str(block.get("extract") or "").strip()
                    if text:
                        layers[layer].append({"title": block.get("title") or name, "summary": text[:1000], "source": block.get("source") or "HDVIA Smart Knowledge Acquisition", "status": "REFERENCE"})
                img = profile.get("representative_image")
                if img and not live.get("representative_image"):
                    live["representative_image"] = img
                if profile.get("sources"):
                    live.setdefault("sources", []).extend(profile.get("sources") or [])
        except Exception:
            self_healing = None

    if live.get("coordinates"):
        layers["geography"].append({"title":"Tọa độ live","summary":str(live["coordinates"]),"source":"Live geocoding"})
        sources += live.get("sources",[])
    if live.get("osm",{}).get("results"):
        layers["geography"].append({"title":"OpenStreetMap","summary":live["osm"]["results"][0].get("display_name") or live["osm"]["results"][0].get("name"),"source":"OpenStreetMap"})
    if live.get("wikipedia",{}).get("results"):
        r=live["wikipedia"]["results"][0]; layers["culture_history"].append({"title":r.get("title") or r.get("name"),"summary":r.get("summary") or r.get("snippet") or r.get("description"),"source":"Wikipedia"})
    if live.get("wikidata",{}).get("results"):
        r=live["wikidata"]["results"][0]; layers["culture_history"].append({"title":r.get("label") or r.get("name"),"summary":r.get("description"),"source":"Wikidata"})
    aq=live.get("air_quality",{}).get("summary",{})
    if aq: layers["nature_operations"].append({"title":"Chất lượng không khí","summary":f"{aq.get('metric')}: {aq.get('value')}","source":"Open-Meteo Air Quality"})
    marine=live.get("marine",{}).get("summary",{})
    if marine: layers["nature_operations"].append({"title":"Điều kiện biển","summary":f"Sóng {marine.get('wave_height','—')} m", "source":"Open-Meteo Marine"})
    for x in guide_experiences or []:
        layers["tourism"].append({"title":x.get("title","Kinh nghiệm HDV"),"summary":x.get("content") or x.get("summary",""),"source":"HDV contribution"})
    counts={k:len(v) for k,v in layers.items()}
    populated=sum(1 for v in layers.values() if v)
    confidence="HIGH" if populated>=3 and len(sources)>=2 else "MEDIUM" if populated>=2 else "LOW"
    expansion=KnowledgeExpansionEngine().inspect(name, tourist_profile=tourist_profile)
    graph=build_knowledge_graph(name, live=live)
    quality=assess_knowledge_quality({"source":"; ".join(list(dict.fromkeys([s for s in sources if s]))),"source_type":"mixed","updated_at":now()}, corroborating_sources=sources)
    quality["layer_coverage"]={k:(len(v)>0) for k,v in layers.items()}
    quality["verified_rule"]="External references remain unverified unless validated through the knowledge pipeline."
    return {"name":name,"schema_version":"1.3.0-self-healing","layers":layers,"layer_counts":counts,"confidence":confidence,"sources":list(dict.fromkeys([s for s in sources if s])),"knowledge_expansion":expansion,"knowledge_graph":graph,"knowledge_quality":quality,"tourist_profile":tourist_profile,"self_healing": self_healing, "updated_at":now()}

def normalize_candidate(payload: Dict[str,Any], source: str, source_type: str="external") -> Dict[str,Any]:
    text=re.sub(r"\s+"," ",str(payload.get("content") or payload.get("summary") or "")).strip()[:12000]
    title=re.sub(r"\s+"," ",str(payload.get("title") or payload.get("name") or "External knowledge")).strip()[:240]
    digest=hashlib.sha256((norm(source)+"\n"+title+"\n"+text).encode()).hexdigest()[:16]
    return {"candidate_id":f"kc:{digest}","title":title,"content":text,"source":source,"source_type":source_type,"status":"CANDIDATE","confidence":"UNASSESSED","collected_at":now(),"destination":payload.get("destination") or payload.get("place") or "","topic":payload.get("topic") or "external"}

def dedupe_candidates(items: Iterable[Dict[str,Any]]) -> List[Dict[str,Any]]:
    out=[]; seen=set()
    for item in items:
        key=hashlib.sha256((norm(item.get("title"))+"\n"+norm(item.get("content"))).encode()).hexdigest()[:20]
        if key in seen: continue
        seen.add(key); out.append(item)
    return out

def score_source(source: str, source_type: str="") -> float:
    s=norm(source); t=norm(source_type)
    if "gov.vn" in s or "unesco" in s: return 0.95
    if "wikidata" in s or "wikipedia" in s: return 0.80
    if "openstreetmap" in s or "nominatim" in s: return 0.75
    if t=="manual": return 0.90
    return 0.50

def validate_candidate(item: Dict[str,Any]) -> Dict[str,Any]:
    out=dict(item); issues=[]
    if len(str(out.get("content") or ""))<40: issues.append("CONTENT_TOO_SHORT")
    if not out.get("source"): issues.append("MISSING_SOURCE")
    out["source_score"]=round(score_source(out.get("source",""),out.get("source_type","")),2)
    out["status"]="VALIDATED" if not issues else "REJECTED"
    out["confidence"]="HIGH" if out["source_score"]>=0.9 else "MEDIUM" if out["source_score"]>=0.7 else "LOW"
    out["issues"]=issues; out["validated_at"]=now()
    return out

class KnowledgeAcquisitionLoop:
    VERSION="1.0.0"
    def ingest(self,payload:Dict[str,Any],source:str,source_type:str="external")->Dict[str,Any]: return normalize_candidate(payload,source,source_type)
    def process(self,items:Iterable[Dict[str,Any]])->List[Dict[str,Any]]: return [validate_candidate(x) for x in dedupe_candidates(items)]
