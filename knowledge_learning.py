"""Controlled Knowledge Learning Pipeline.

AI never writes directly into published knowledge. Sources enter as candidates,
then pass validation/review before publication. This is the safe substitute for
unsupervised self-training in the foundation release.
"""
from __future__ import annotations
from typing import Any, Dict

class KnowledgeLearningPipeline:
    VERSION="1.0.0-foundation"
    def ingest(self, *, source_type: str, title: str, content: str, source_url: str=""):
        if not title.strip() or not content.strip(): raise ValueError("Thiếu tiêu đề hoặc nội dung")
        return {"status":"CANDIDATE","source_type":source_type,"title":title.strip(),"content":content.strip(),"source_url":source_url.strip(),"checks":["non_empty","provenance_required_for_publish"]}
    def validate(self, record: Dict[str,Any]):
        issues=[]
        if record.get("source_type") in ("web","external") and not record.get("source_url"): issues.append("MISSING_PROVENANCE")
        if len(record.get("content", "")) < 40: issues.append("CONTENT_TOO_SHORT")
        return {"ok":not issues,"status":"VALIDATED" if not issues else "REJECTED","issues":issues}
