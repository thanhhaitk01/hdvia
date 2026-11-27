"""Controlled Khám Phá Di Sản discovery importer for HDVIA 1.24.

Stores only page metadata and compact excerpts/candidate summaries. It does not
copy full articles into the HDVIA warehouse. Publication remains review-gated.
"""
from __future__ import annotations
import json, re, urllib.request
from html import unescape
from pathlib import Path
from datetime import datetime, timezone

BASE=Path(__file__).resolve().parent
OUT=BASE/"data"/"acquisition"/"khamphadisan_candidates.json"
UA="HDVIA/1.24 (+source-attribution; controlled discovery)"

def _text(html):
    html=re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>"," ",html,flags=re.I)
    html=re.sub(r"<[^>]+>"," ",html)
    return re.sub(r"\s+"," ",unescape(html)).strip()

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=12) as r:
        return r.read().decode("utf-8","ignore")

def candidate(url):
    html=fetch(url); text=_text(html)
    m=re.search(r"<title[^>]*>(.*?)</title>",html,re.I|re.S)
    title=_text(m.group(1)) if m else url
    return {"candidate_id":"kpd:"+re.sub(r"[^a-z0-9]+","-",url.lower()).strip("-"),"title":title[:240],"url":url,"summary":text[:500],"source":"Khám Phá Di Sản","source_type":"editorial_discovery","status":"CANDIDATE","provenance_required":True,"collected_at":datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")}

def main(urls):
    rows=[]
    for url in urls:
        try: rows.append(candidate(url))
        except Exception as exc: rows.append({"url":url,"status":"FAILED","error":str(exc)[:180]})
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Wrote {len(rows)} candidates to {OUT}")

if __name__=="__main__":
    import sys
    main(sys.argv[1:])
