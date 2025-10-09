from __future__ import annotations

from typing import Dict

from ...schemas import AgentState
from ...prompts import PromptManager
from .base import NodeBase
from .memory_decorators import with_memory_tracking


class AnalyzeIntentNode(NodeBase):
    """Determine query intent via PromptManager (LLM first, fallback keywords)."""

    @with_memory_tracking("intent_analysis")
    def __call__(self, state: AgentState) -> Dict[str, object]:
        try:
            query = state["query"]
            self.logger.info("[Node: analyze_intent] Analyzing query: %s", query)

            intent_info = PromptManager.analyze_query_intent(
                query,
                llm=self.llm,
                use_llm_analysis=True,
            )

            match_mode = "fuzzy"
            lowered_query = query.lower()
            exact_keywords = ["精确匹配", "精准匹配", "完全匹配", "完全一致", "精确查询", "exact match"]
            if any(keyword in lowered_query for keyword in exact_keywords):
                match_mode = "exact"

            thought_output = dict(intent_info or {})
            thought_output["match_mode"] = match_mode

            thought_step = {
                "step": 1,
                "type": "intent_analysis",
                "action": (
                    "analyze_query_intent_with_llm"
                    if self.llm
                    else "analyze_query_intent_with_keywords"
                ),
                "input": query,
                "output": thought_output,
                "status": "completed",
            }

            return {
                "query_intent": intent_info["intent_type"],
                "requires_spatial": intent_info["is_spatial"],
                "intent_info": intent_info,
                "match_mode": match_mode,
                "max_iterations": 3,
                "current_step": 0,
                "should_continue": True,
                "thought_chain": [thought_step],
            }

        except Exception as exc:
            self.logger.error("[Node: analyze_intent] Error: %s", exc)
            return {
                "error": f"意图分析失败: {str(exc)}",
                "should_continue": False,
                "query_intent": "query",
                "requires_spatial": False,
                "intent_info": None,
                "max_iterations": 3,
                "current_step": 0,
                "thought_chain": [],
            }


class EnhanceQueryNode(NodeBase):
    """Augment the query text with spatial hints when needed."""

    @with_memory_tracking("enhance_query")
    def __call__(self, state: AgentState) -> Dict[str, object]:
        try:
            query = state["query"]
            requires_spatial = state.get("requires_spatial", False)

            self.logger.info(
                "[Node: enhance_query] Enhancing query, spatial=%s", requires_spatial
            )

            if requires_spatial:
                enhanced_query = PromptManager.build_enhanced_query(
                    query,
                    add_spatial_hint=True,
                )
            else:
                enhanced_query = query

            thought_step = {
                "step": 2,
                "type": "query_enhancement",
                "action": "enhance_query",
                "input": query,
                "output": enhanced_query,
                "status": "completed",
            }

            return {
                "enhanced_query": enhanced_query,
                "thought_chain": [thought_step],
            }

        except Exception as exc:
            self.logger.error("[Node: enhance_query] Error: %s", exc)
            return {
                "enhanced_query": state.get("query", ""),
                "thought_chain": [
                    {
                        "step": 2,
                        "type": "query_enhancement",
                        "error": str(exc),
                        "status": "failed",
                    }
                ],
            }
