from __future__ import annotations

from typing import Any, Dict

from ...schemas import AgentState
from .legacy import LegacyAgentNodes


class FetchSchemaNode:
    """Thin wrapper around LegacyAgentNodes.fetch_schema."""

    def __init__(self, impl: LegacyAgentNodes) -> None:
        self._impl = impl

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        return self._impl.fetch_schema(state)
