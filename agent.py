"""HDVIA AI Agent foundation with explicit tool permissions and audit-friendly traces."""
from __future__ import annotations
from typing import Any, Callable, Dict

class AgentPermissionError(Exception): pass

class ToolRegistry:
    def __init__(self): self._tools: Dict[str, Callable[..., Any]] = {}
    def register(self, name: str, fn: Callable[..., Any]): self._tools[name] = fn
    def names(self): return sorted(self._tools)
    def execute(self, name: str, *, allowed: set[str], **kwargs):
        if name not in allowed: raise AgentPermissionError(f"Tool not permitted: {name}")
        if name not in self._tools: raise ValueError(f"Unknown tool: {name}")
        return self._tools[name](**kwargs)

class HDVIAAgent:
    VERSION = "1.0.0-foundation"
    def __init__(self, registry: ToolRegistry): self.registry = registry
    def inspect_tour(self, *, user: Dict[str, Any], journey: Dict[str, Any] | None):
        allowed = {"journey.summary", "weather.summary"}
        trace=[]
        summary=self.registry.execute("journey.summary", allowed=allowed, journey=journey); trace.append("journey.summary")
        weather=self.registry.execute("weather.summary", allowed=allowed, journey=journey); trace.append("weather.summary")
        return {"ok":True,"agent":"HDVIA Tour Agent","version":self.VERSION,"summary":summary,"weather":weather,"trace":trace,"actions": ["prepare_plan_b"] if (weather.get("risk_count",0)>0) else []}
