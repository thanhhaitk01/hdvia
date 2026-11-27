"""HDVIA 1.23 AI Gateway.

Provider-neutral, safe-by-default bridge for external AI APIs.  The gateway is
usable without any provider key (dry-run/local contract mode) and becomes live
when runtime credentials are configured.  It never writes directly to the
published knowledge warehouse.
"""
from __future__ import annotations
import json, os, urllib.request, urllib.error
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional


@dataclass
class AIProvider:
    name: str
    base_url: str
    api_key_env: str
    model_env: str
    default_model: str
    enabled: bool = False
    timeout: int = 30

    def status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "enabled": bool(self.enabled),
            "configured": bool(os.environ.get(self.api_key_env, "").strip()),
            "model": os.environ.get(self.model_env, self.default_model),
            "capabilities": ["generate", "classify", "knowledge_review"],
        }

    def generate(self, prompt: str, *, system: str = "", temperature: float = 0.2) -> Dict[str, Any]:
        key = os.environ.get(self.api_key_env, "").strip()
        if not self.enabled or not key:
            return {"ok": False, "status": "NOT_CONFIGURED", "provider": self.name}
        model = os.environ.get(self.model_env, self.default_model)
        if self.name == "gemini":
            url = f"{self.base_url.rstrip('/')}/models/{model}:generateContent?key={key}"
            body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": temperature}}
            if system:
                body["systemInstruction"] = {"parts": [{"text": system}]}
        else:
            url = self.base_url.rstrip("/") + "/chat/completions"
            body = {"model": model, "messages": ([{"role":"system","content":system}] if system else []) + [{"role":"user","content":prompt}], "temperature": temperature}
        req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(),
                                     headers={"Content-Type":"application/json","Accept":"application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data=json.loads(resp.read().decode("utf-8", "replace"))
            text=self._extract(data)
            return {"ok": True, "provider": self.name, "model": model, "text": text, "raw": data}
        except urllib.error.HTTPError as exc:
            return {"ok": False, "provider": self.name, "status": "HTTP_ERROR", "http_status": exc.code}
        except Exception as exc:
            return {"ok": False, "provider": self.name, "status": "NETWORK_ERROR", "error": str(exc)[:240]}

    def _extract(self, data: Mapping[str, Any]) -> str:
        if self.name == "gemini":
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            return "\n".join(str(p.get("text", "")) for p in parts if p.get("text"))
        return str(data.get("choices", [{}])[0].get("message", {}).get("content", ""))


class AIGateway:
    VERSION = "1.23.1"
    def __init__(self, providers: Iterable[AIProvider]):
        self.providers={p.name:p for p in providers}

    def status(self):
        return {"version":self.VERSION,"providers":[p.status() for p in self.providers.values()]}

    def ask(self, prompt: str, *, system: str = "", providers: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        # Bound external calls so a malformed client request cannot consume
        # unlimited provider quota or create unexpectedly large prompts.
        prompt = str(prompt or "")[:12000]
        system = str(system or "")[:6000]
        order=list(providers or self.providers.keys())
        attempts=[]
        for name in order:
            p=self.providers.get(name)
            if not p: continue
            result=p.generate(prompt, system=system)
            attempts.append({"provider":name,"ok":bool(result.get("ok")),"status":result.get("status","")})
            if result.get("ok"):
                return {"ok":True,"result":result,"attempts":attempts}
        return {"ok":False,"status":"NO_PROVIDER_AVAILABLE","attempts":attempts}


def build_ai_gateway_from_env() -> AIGateway:
    providers=[AIProvider("gemini", "https://generativelanguage.googleapis.com/v1beta", "GEMINI_API_KEY", "HDVIA_GEMINI_MODEL", "gemini-2.5-flash-lite", enabled=True)]
    # Generic OpenAI-compatible endpoint is optional and lets HDVIA connect to
    # other free/low-cost providers without changing application code.
    if os.environ.get("HDVIA_OPENAI_COMPAT_BASE", "").strip():
        providers.append(AIProvider("openai_compat", os.environ["HDVIA_OPENAI_COMPAT_BASE"].strip(), "HDVIA_OPENAI_COMPAT_API_KEY", "HDVIA_OPENAI_COMPAT_MODEL", "", enabled=True))
    return AIGateway(providers)
