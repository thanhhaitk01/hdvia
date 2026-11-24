"""HDVIA External Data & AI Gateway.

Provider-neutral gateway for permitted external APIs. Credentials are read from
server environment variables only; never stored in warehouse records.
"""
from __future__ import annotations
import os, json, time, hashlib
from typing import Any, Dict, List, Optional
import requests

TIMEOUT=int(os.environ.get("HDVIA_CONNECT_TIMEOUT", "20"))

class ExternalGatewayError(Exception): pass

def _json(resp):
    try: return resp.json()
    except Exception: return {"raw": resp.text[:4000]}

def _secret(name): return os.environ.get(name, "").strip()

def _request(method, url, **kwargs):
    kwargs.setdefault("timeout", TIMEOUT)
    try: r=requests.request(method, url, **kwargs)
    except requests.RequestException as e: raise ExternalGatewayError(f"Kết nối nguồn thất bại: {e}") from e
    if r.status_code >= 400:
        data=_json(r); raise ExternalGatewayError(f"Nguồn trả HTTP {r.status_code}: {data.get('error', data) if isinstance(data,dict) else data}")
    return _json(r)

class ExternalDataGateway:
    VERSION="1.0.0"
    def status(self):
        return {
            "version":self.VERSION,
            "providers":{
                "google_places":{"enabled":bool(_secret("GOOGLE_MAPS_API_KEY"))},
                "google_cse":{"enabled":bool(_secret("GOOGLE_CSE_API_KEY") and _secret("GOOGLE_CSE_CX"))},
                "youtube":{"enabled":bool(_secret("YOUTUBE_API_KEY"))},
                "meta_graph":{"enabled":bool(_secret("META_ACCESS_TOKEN"))},
                "openai":{"enabled":bool(_secret("OPENAI_API_KEY"))},
                "gemini":{"enabled":bool(_secret("GEMINI_API_KEY"))},
                "anthropic":{"enabled":bool(_secret("ANTHROPIC_API_KEY"))},
            },
            "policy":"API/OAuth/Webhook only; no credential storage; external content enters CANDIDATE flow.",
        }

    def google_places_search(self, query, language="vi", max_results=5):
        key=_secret("GOOGLE_MAPS_API_KEY")
        if not key: raise ExternalGatewayError("Thiếu GOOGLE_MAPS_API_KEY")
        data=_request("POST","https://places.googleapis.com/v1/places:searchText",
            headers={"X-Goog-Api-Key":key,"X-Goog-FieldMask":"places.id,places.displayName,places.formattedAddress,places.location,places.types,places.websiteUri"},
            json={"textQuery":query,"languageCode":language,"pageSize":max(1,min(20,int(max_results)))})
        return {"provider":"google_places","query":query,"results":data.get("places",[])[:max_results]}

    def youtube_search(self, query, max_results=5):
        key=_secret("YOUTUBE_API_KEY")
        if not key: raise ExternalGatewayError("Thiếu YOUTUBE_API_KEY")
        data=_request("GET","https://www.googleapis.com/youtube/v3/search",params={"part":"snippet","q":query,"type":"video","maxResults":max(1,min(25,int(max_results))),"key":key})
        return {"provider":"youtube","query":query,"results":data.get("items",[])[:max_results]}

    def meta_graph_get(self, path, params=None):
        token=_secret("META_ACCESS_TOKEN")
        if not token: raise ExternalGatewayError("Thiếu META_ACCESS_TOKEN")
        version=os.environ.get("META_GRAPH_VERSION","v27.0")
        clean=str(path).strip().lstrip("/")
        if not clean: raise ExternalGatewayError("Thiếu Graph API path")
        params=dict(params or {}); params["access_token"]=token
        return {"provider":"meta_graph","path":clean,"data":_request("GET",f"https://graph.facebook.com/{version}/{clean}",params=params)}

    def openai(self, input_text, model=None):
        key=_secret("OPENAI_API_KEY")
        if not key: raise ExternalGatewayError("Thiếu OPENAI_API_KEY")
        model=model or os.environ.get("OPENAI_MODEL","gpt-5")
        data=_request("POST","https://api.openai.com/v1/responses",headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json={"model":model,"input":input_text})
        return {"provider":"openai","model":model,"response":data}

    def gemini(self, input_text, model=None):
        key=_secret("GEMINI_API_KEY")
        if not key: raise ExternalGatewayError("Thiếu GEMINI_API_KEY")
        model=model or os.environ.get("GEMINI_MODEL","gemini-2.5-flash")
        url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        data=_request("POST",url,params={"key":key},json={"contents":[{"parts":[{"text":input_text}]}]})
        return {"provider":"gemini","model":model,"response":data}

    def anthropic(self, input_text, model=None):
        key=_secret("ANTHROPIC_API_KEY")
        if not key: raise ExternalGatewayError("Thiếu ANTHROPIC_API_KEY")
        model=model or os.environ.get("ANTHROPIC_MODEL","claude-sonnet-4-5")
        data=_request("POST","https://api.anthropic.com/v1/messages",headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},json={"model":model,"max_tokens":1200,"messages":[{"role":"user","content":input_text}]})
        return {"provider":"anthropic","model":model,"response":data}

    def ai_ask(self, provider, prompt, model=None):
        provider=str(provider).lower()
        if provider=="openai": return self.openai(prompt,model)
        if provider=="gemini": return self.gemini(prompt,model)
        if provider=="anthropic": return self.anthropic(prompt,model)
        raise ExternalGatewayError("AI provider không được hỗ trợ")
