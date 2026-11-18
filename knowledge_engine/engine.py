import json, re, urllib.parse, urllib.request
from html import unescape
from urllib.parse import urlparse

class KnowledgeIngestionEngine:
    """Provider-neutral beta ingestion layer.
    Collects source material, normalizes it, and produces a reusable knowledge record.
    External AI providers can be plugged in later without changing the data model.
    """
    def __init__(self):
        self.ua = "HDVIA/1.5-beta Travel Intelligence (+knowledge ingestion)"

    def _safe_url(self, url):
        p=urlparse(url)
        if p.scheme not in ("http","https") or not p.netloc:
            raise ValueError("URL không hợp lệ")
        host=(p.hostname or "").lower()
        blocked=("localhost","127.0.0.1","0.0.0.0","::1")
        if host in blocked or host.endswith(".local"):
            raise ValueError("URL nội bộ bị chặn")
        return url

    def fetch_url(self, url, timeout=8, max_bytes=800000):
        url=self._safe_url(url)
        req=urllib.request.Request(url, headers={"User-Agent":self.ua})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data=r.read(max_bytes)
            ctype=r.headers.get("Content-Type","")
        text=data.decode("utf-8", errors="ignore")
        text=re.sub(r"<script[\s\S]*?</script>"," ",text,flags=re.I)
        text=re.sub(r"<style[\s\S]*?</style>"," ",text,flags=re.I)
        text=re.sub(r"<[^>]+>"," ",text)
        text=unescape(re.sub(r"\s+"," ",text)).strip()
        return {"url":url,"content_type":ctype,"text":text[:120000]}

    def wikipedia(self, query):
        q=urllib.parse.urlencode({"action":"query","format":"json","generator":"search","gsrsearch":query,"gsrlimit":3,"prop":"extracts|info","exintro":1,"explaintext":1,"inprop":"url"})
        req=urllib.request.Request("https://vi.wikipedia.org/w/api.php?"+q,headers={"User-Agent":self.ua})
        with urllib.request.urlopen(req,timeout=8) as r:
            data=json.loads(r.read().decode("utf-8"))
        out=[]
        for page in data.get("query",{}).get("pages",{}).values():
            out.append({"title":page.get("title"),"url":page.get("fullurl"),"extract":page.get("extract","")})
        return out

    def local_ai_extract(self, title, text):
        """Deterministic beta fallback. It creates structured reusable facts without claiming LLM verification."""
        sentences=[s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip())>40]
        return {
            "summary": " ".join(sentences[:3])[:1000],
            "facts": sentences[:12],
            "entities": [title] if title else [],
            "ai_mode": "local_fallback",
            "confidence": "medium"
        }
