from __future__ import annotations

from typing import Any, Callable, Dict

from ...schemas import AgentState
from .answer import GenerateAnswerNode
from .base import NodeContext
from .error import HandleErrorNode
from .fetch_schema import FetchSchemaNode
from .intent import AnalyzeIntentNode, EnhanceQueryNode
from .legacy import LegacyAgentNodes  # Legacy compatibility
from .sql_execution import ExecuteSqlNode
from .sql_generation import GenerateSqlNode
from .validation import CheckResultsNode, ValidateResultsNode

NodeCallable = Callable[[AgentState], Dict[str, Any]]


def build_node_context(**kwargs: Any) -> NodeContext:
    return NodeContext(**kwargs)


def build_legacy_nodes(**kwargs: Any) -> LegacyAgentNodes:
    return LegacyAgentNodes(**kwargs)


def build_node_mapping(context: NodeContext) -> Dict[str, NodeCallable]:
    return {
        "fetch_schema": FetchSchemaNode(context),
        "analyze_intent": AnalyzeIntentNode(context),
        "enhance_query": EnhanceQueryNode(context),
        "generate_sql": GenerateSqlNode(context),
        "execute_sql": ExecuteSqlNode(context),
        "validate_results": ValidateResultsNode(context),
        "check_results": CheckResultsNode(context),
        "generate_answer": GenerateAnswerNode(context),
        "handle_error": HandleErrorNode(context),
    }


class AgentNodes:
    """Facade providing direct access to node callables for compatibility."""

    def __init__(self, **kwargs: Any) -> None:
        self.context = build_node_context(**kwargs)
        self.fetch_schema = FetchSchemaNode(self.context)
        self.analyze_intent = AnalyzeIntentNode(self.context)
        self.enhance_query = EnhanceQueryNode(self.context)
        self.generate_sql = GenerateSqlNode(self.context)
        self.execute_sql = ExecuteSqlNode(self.context)
        self.validate_results = ValidateResultsNode(self.context)
        self.check_results = CheckResultsNode(self.context)
        self.generate_answer = GenerateAnswerNode(self.context)
        self.handle_error = HandleErrorNode(self.context)

    def _classify_error(self, error: Any) -> str:
        return self.handle_error._classify_error(error)

    def _determine_fallback_strategy(self, error_type: str, retry_count: int) -> str:
        return self.handle_error._determine_fallback_strategy(error_type, retry_count)

