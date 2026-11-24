"""One-way seed helper for the 8-domain data core.
Existing warehouse records are never deleted or overwritten."""
import json, os
from data_core import seed

def write_snapshot(path=None):
    path=path or os.path.join(os.path.dirname(__file__),'data','warehouse','seed_v2_snapshot.json')
    with open(path,'w',encoding='utf-8') as f: json.dump(seed(),f,ensure_ascii=False,indent=2)
    return path

if __name__=='__main__': print(write_snapshot())
