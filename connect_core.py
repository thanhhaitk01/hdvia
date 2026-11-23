"""HDVIA Connect Core — provider-agnostic integration foundation for Beta 1.9."""
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class ConnectorDescriptor:
    name: str
    display_name: str
    category: str
    enabled: bool = False


class ConnectorRegistry:
    def __init__(self, descriptors: Optional[Iterable[ConnectorDescriptor]] = None):
        self._items: Dict[str, ConnectorDescriptor] = {}
        for item in descriptors or ():
            self.register(item)

    def register(self, descriptor: ConnectorDescriptor) -> None:
        key = descriptor.name.strip().lower()
        if not key:
            raise ValueError("Connector name is required")
        self._items[key] = descriptor

    def get(self, name: str) -> Optional[ConnectorDescriptor]:
        return self._items.get((name or "").strip().lower())

    def all(self) -> list[ConnectorDescriptor]:
        return list(self._items.values())

    def public_status(self) -> list[Dict[str, Any]]:
        return [
            {"name": x.name, "display_name": x.display_name, "category": x.category, "enabled": x.enabled}
            for x in self._items.values()
        ]


DEFAULT_CONNECTORS = (
    ConnectorDescriptor("google", "Google", "identity"),
    ConnectorDescriptor("facebook", "Facebook", "identity"),
    ConnectorDescriptor("zalo", "Zalo", "identity"),
)


def build_registry(provider_enabled) -> ConnectorRegistry:
    return ConnectorRegistry(
        ConnectorDescriptor(x.name, x.display_name, x.category, bool(provider_enabled(x.name)))
        for x in DEFAULT_CONNECTORS
    )
