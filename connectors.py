"""Provider-neutral connector contracts used by HDVIA Beta 1.9.

This module deliberately contains contracts, not provider secrets or provider-specific
network calls. Concrete integrations can implement these operations in later releases.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseConnector(ABC):
    """Minimum lifecycle contract for every external HDVIA connector."""

    name = "base"
    category = "external"

    @abstractmethod
    def status(self) -> Dict[str, Any]:
        """Return a safe, non-secret public status payload."""

    @abstractmethod
    def connect(self, **kwargs: Any) -> Dict[str, Any]:
        """Start or describe a connection flow without exposing secrets."""

    @abstractmethod
    def callback(self, **kwargs: Any) -> Dict[str, Any]:
        """Normalize an external callback result."""

    @abstractmethod
    def get_profile(self, **kwargs: Any) -> Dict[str, Any]:
        """Return a normalized external profile."""

    @abstractmethod
    def disconnect(self, **kwargs: Any) -> Dict[str, Any]:
        """Disconnect the external identity from HDVIA."""


class OAuthConnector(BaseConnector):
    """Provider-neutral OAuth connector contract.

    The concrete provider adapter is intentionally left to the integration release;
    these methods only define the stable interface used by HDVIA Connect.
    """

    def __init__(self, provider: str, enabled: bool = False):
        self.name = provider
        self.category = "identity"
        self.enabled = bool(enabled)

    def status(self) -> Dict[str, Any]:
        return {"name": self.name, "category": self.category, "enabled": self.enabled}

    def connect(self, **kwargs: Any) -> Dict[str, Any]:
        return {"ok": False, "provider": self.name, "error": "Connector flow not implemented"}

    def callback(self, **kwargs: Any) -> Dict[str, Any]:
        return {"ok": False, "provider": self.name, "error": "Connector callback not implemented"}

    def get_profile(self, **kwargs: Any) -> Dict[str, Any]:
        return {"ok": False, "provider": self.name, "error": "Profile sync not implemented"}

    def disconnect(self, **kwargs: Any) -> Dict[str, Any]:
        return {"ok": False, "provider": self.name, "error": "Disconnect flow not implemented"}
