"""Bounded scheduled self-healing sync for HDVIA destination knowledge references."""
from __future__ import annotations
import argparse, json, os
from datetime import datetime, timezone
from pathlib import Path
from destination_catalog import DESTINATIONS
from open_data_agent import DEFAULT_TARGETS
from smart_knowledge_acquisition import SmartKnowledgeAcquirer

OUT=Path(__file__).resolve().parent / "data" / "warehouse" / "smart_knowledge_cache.json"
STATE=Path(__file__).resolve().parent / "data" / "acquisition" / "smart_sync_state.json"

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def targets():
    out=[]; seen=set()
    for item in list(DESTINATIONS) + [{"name":x} for x in DEFAULT_TARGETS]:
        name=str(item.get("name") or "").strip()
        key=" ".join(name.lower().split())
        if name and key not in seen:
            seen.add(key); out.append(name)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=int(os.getenv("HDVIA_SMART_SYNC_BATCH","12")))
    args=ap.parse_args()
    all_targets=targets(); limit=max(1,min(args.limit,len(all_targets)))
    state={}
    if STATE.exists():
        try: state=json.loads(STATE.read_text(encoding="utf-8"))
        except Exception: state={}
    cursor=int(state.get("cursor",0)) % len(all_targets)
    batch=[all_targets[(cursor+i)%len(all_targets)] for i in range(limit)]
    existing={}
    if OUT.exists():
        try: existing=json.loads(OUT.read_text(encoding="utf-8"))
        except Exception: existing={}
    profiles=existing.get("profiles",{}) if isinstance(existing,dict) else {}
    acq=SmartKnowledgeAcquirer()
    stats={"requested":len(batch),"ok":0,"errors":0,"cursor":cursor,"next_cursor":(cursor+len(batch))%len(all_targets),"targets":batch}
    for name in batch:
        try:
            result=acq.acquire(name, domains=["history","culture","food","tourism"])
            if result.get("ok"):
                key=" ".join(name.lower().split())
                profiles[key]=result["profile"]; stats["ok"]+=1
            else: stats["errors"]+=1
        except Exception: stats["errors"]+=1
    payload={"version":"2.0.0","updated_at":now(),"profiles":profiles,"last_run":stats,"publication_policy":"REFERENCE_ONLY","target_count":len(all_targets)}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    STATE.parent.mkdir(parents=True,exist_ok=True); STATE.write_text(json.dumps({"version":"1.0.0","cursor":stats["next_cursor"],"updated_at":now(),"target_count":len(all_targets)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(stats,ensure_ascii=False))

if __name__=="__main__": main()
