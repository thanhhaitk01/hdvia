"""CLI for safe external-data ingestion.
Usage: python scripts_data_acquisition.py --url https://... --kind knowledge
It writes a candidate JSON artifact; publication remains a separate review step.
"""
import argparse, json
from data_acquisition import candidate_from_web

p=argparse.ArgumentParser(); p.add_argument("--url",required=True); p.add_argument("--kind",default="knowledge"); p.add_argument("--destination-id",default=""); p.add_argument("--admin-id",default="")
a=p.parse_args()
item=candidate_from_web(url=a.url,requested_kind=a.kind,destination_id=a.destination_id,admin_id=a.admin_id)
print(json.dumps(item,ensure_ascii=False,indent=2))
