"""External Connect v2 foundation. No provider secrets are stored here."""
from dataclasses import dataclass
from typing import Any, Dict, Iterable

@dataclass(frozen=True)
class ExternalConnector:
    name: str
    category: str
    enabled: bool = False
    capabilities: tuple[str,...] = ()

class ExternalConnectManager:
    def __init__(self, connectors: Iterable[ExternalConnector]): self._items={c.name:c for c in connectors}
    def status(self):
        return [{"name":c.name,"category":c.category,"enabled":c.enabled,"capabilities":list(c.capabilities)} for c in self._items.values()]
    def get(self,name): return self._items.get(name)

DEFAULT_EXTERNAL_CONNECTORS=(
    ExternalConnector("google","identity",False,("login","identity_linking")),
    ExternalConnector("facebook","identity",False,("login","identity_linking")),
    ExternalConnector("zalo","identity",False,("login","identity_linking")),
    ExternalConnector("weather","travel-data",True,("forecast_7_day","risk")),
    ExternalConnector("maps","travel-data",False,("route","distance")),
)
