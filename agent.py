"""HDVIA AI Agent with context-aware, permissioned actions."""
from __future__ import annotations
from typing import Any, Callable, Dict

class AgentPermissionError(Exception): pass

class ToolRegistry:
    def __init__(self): self._tools: Dict[str, Callable[..., Any]] = {}
    def register(self,name:str,fn:Callable[...,Any]): self._tools[name]=fn
    def names(self): return sorted(self._tools)
    def execute(self,name:str,*,allowed:set[str],**kwargs):
        if name not in allowed: raise AgentPermissionError(f"Tool not permitted: {name}")
        if name not in self._tools: raise ValueError(f"Unknown tool: {name}")
        return self._tools[name](**kwargs)

class HDVIAAgent:
    VERSION="2.0.0-context-aware"
    def __init__(self,registry:ToolRegistry): self.registry=registry
    def inspect_tour(self,*,user:Dict[str,Any],journey:Dict[str,Any]|None,data_context:Dict[str,Any]|None=None):
        allowed={"journey.summary","weather.summary"}
        data_context=data_context or (journey or {}).get("data_context") or {}
        trace=[]
        summary=self.registry.execute("journey.summary",allowed=allowed,journey=journey); trace.append("journey.summary")
        weather=self.registry.execute("weather.summary",allowed=allowed,journey=journey); trace.append("weather.summary")
        risks=[x for x in data_context.get("weather_risk",[]) if isinstance(x,dict) and str(x.get("risk_level","UNKNOWN")).upper() in ("HIGH","MEDIUM")]
        experiences=[x for x in data_context.get("experiences",[]) if isinstance(x,dict)]
        actions=[]
        if risks: actions += ["prepare_plan_b","recheck_live_weather"]
        if experiences: actions.append("review_guide_experience")
        return {"ok":True,"agent":"HDVIA Tour Agent","version":self.VERSION,"summary":summary,"weather":weather,
                "trace":trace,"actions":actions,"data_core":{"linked":bool(data_context),"counts":{k:len(v) for k,v in data_context.items() if isinstance(v,list)},"risk_records":len(risks),"experience_records":len(experiences)}}
