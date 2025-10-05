from __future__ import annotations

from typing import Any, Callable, Dict

from ...schemas import AgentState
from .answer import GenerateAnswerNode
from .error import HandleErrorNode
from .fetch_schema import FetchSchemaNode
from .intent import AnalyzeIntentNode, EnhanceQueryNode
from .legacy import LegacyAgentNodes
from .sql_execution import ExecuteSqlNode
from .sql_generation import GenerateSqlNode
from .validation import CheckResultsNode, ValidateResultsNode

NodeCallable = Callable[[AgentState], Dict[str, Any]]


def build_legacy_nodes(**kwargs) -> LegacyAgentNodes:
    """Helper to instantiate the legacy implementation."""
    return LegacyAgentNodes(**kwargs)


def build_node_mapping(legacy: LegacyAgentNodes) -> Dict[str, NodeCallable]:
    """Create mapping from node name to callable handler."""
    return {
        "fetch_schema": FetchSchemaNode(legacy),
        "analyze_intent": AnalyzeIntentNode(legacy),
        "enhance_query": EnhanceQueryNode(legacy),
        "generate_sql": GenerateSqlNode(legacy),
        "execute_sql": ExecuteSqlNode(legacy),
        "validate_results": ValidateResultsNode(legacy),
        "check_results": CheckResultsNode(legacy),
        "generate_answer": GenerateAnswerNode(legacy),
        "handle_error": HandleErrorNode(legacy),
    }

# Backwards compatibility --------------------------------------------------
AgentNodes = LegacyAgentNodes
