"""HDVIA 1.23 controlled self-update engine.

Turns knowledge gaps and external AI suggestions into auditable candidates.
Publication remains explicit/validated; this module never silently overwrites
curated knowledge.
"""
from __future__ import annotations
import hashlib, json, os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable
from knowledge_learning import KnowledgeLearningPipeline
from knowledge_quality import assess
from data_acquisition import candidate_from_web


def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

class SelfUpdateEngine:
    VERSION="1.23.1"
    def __init__(self, gateway, learning=None):
        self.gateway=gateway
        self.learning=learning or KnowledgeLearningPipeline()

    def discover(self, question: str, *, place: str = "", domain: str = "") -> Dict[str,Any]:
        prompt=("Bạn là bộ thu thập tri thức cho HDVIA. Hãy xác định dữ liệu du lịch Việt Nam "
                 "nào đang thiếu để trả lời câu hỏi dưới đây. Chỉ đề xuất thông tin có thể kiểm chứng; "
                 "không bịa nguồn. Trả JSON gồm gap, facts_to_verify, source_types.\n"
                 f"Địa điểm: {place}\nLĩnh vực: {domain}\nCâu hỏi: {question}")
        return self.gateway.ask(prompt, system="HDVIA knowledge acquisition; concise JSON only.")

    def enrich(self, *, question: str, place: str = "", domain: str = "") -> Dict[str, Any]:
        """Ask a configured external AI for a bounded, auditable knowledge candidate.

        The provider may suggest a source URL, but publication is never automatic.
        When source fetching is explicitly enabled, only public HTTP(S) sources pass
        through the existing SSRF-safe acquisition layer.
        """
        result = self.discover(question, place=place, domain=domain)
        if not result.get("ok"):
            return {"ok": False, "status": "AI_UNAVAILABLE", "gateway": result}
        text = str((result.get("result") or {}).get("text", "")).strip()
        candidate = {"gap": "", "facts_to_verify": [], "source_types": [], "source_url": "", "content": text}
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                candidate.update(parsed)
        except Exception:
            pass
        source_url = str(candidate.get("source_url") or candidate.get("url") or "").strip()
        content = str(candidate.get("content") or text).strip()[:12000]
        fetched = None
        if source_url and os.environ.get("HDVIA_SELF_UPDATE_FETCH_SOURCES", "0") == "1":
            try:
                fetched = candidate_from_web(url=source_url, requested_kind="knowledge", destination_id=place)
                content = str((fetched.get("record") or {}).get("content") or content)[:12000]
            except Exception as exc:
                fetched = {"ok": False, "error": str(exc)[:240]}
        rec = self.candidate_from_external(question=question, place=place, domain=domain, content=content, source_url=source_url)
        rec["external_candidate"] = candidate
        rec["source_fetch"] = fetched
        rec["quality"] = assess({"source": source_url, "source_type": "external_ai", "content": content, "updated_at": now()})
        return {"ok": True, "status": "CANDIDATE", "candidate": rec}

    def candidate_from_external(self, *, question: str, place: str, domain: str, content: str, source_url: str) -> Dict[str,Any]:
        rec=self.learning.ingest(source_type="external_ai", title=f"AI candidate: {place or domain}", content=content, source_url=source_url)
        rec["idempotency_key"]=hashlib.sha256((question+place+domain+content+source_url).encode("utf-8")).hexdigest()
        rec["created_at"]=now(); rec["domain"]=domain; rec["destination"]=place
        rec["publication_policy"]="REVIEW_BEFORE_PUBLISH"
        return rec

    def health(self) -> Dict[str,Any]:
        return {"version":self.VERSION,"mode":"controlled_self_update","publish_policy":"review_or_validation_required","ai_gateway":self.gateway.status()}
