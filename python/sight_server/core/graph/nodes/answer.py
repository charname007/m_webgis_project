from __future__ import annotations

from typing import Any, Dict, List, Optional

from ...schemas import AgentState
from .base import NodeBase
from .memory_decorators import with_memory_tracking


class GenerateAnswerNode(NodeBase):
    """Generate the final answer with optional deep analysis support."""

    @with_memory_tracking("generate_answer")
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        query = state.get("query", "")
        final_data: Optional[List[Dict[str, Any]]] = state.get("final_data")
        count = len(final_data) if final_data else 0
        query_intent = state.get("query_intent", "query")
        requires_spatial = state.get("requires_spatial", False)
        intent_info = state.get("intent_info")
        current_step = state.get("current_step", 0)

        try:
            self.logger.info(
                "[Node: generate_answer] Generating answer with deep analysis for %s records",
                count,
            )
            self.logger.info(
                "[Node: generate_answer] Query intent: %s, Spatial: %s",
                query_intent,
                requires_spatial,
            )

            if self.data_analyzer:
                self.logger.info(
                    "[Node: generate_answer] Using DataAnalyzer for deep analysis",
                )
                analysis_result = self.data_analyzer.analyze(
                    query=query,
                    final_data=final_data or [],
                    intent_info=intent_info,
                )

                answer = analysis_result.answer
                analysis = analysis_result.analysis
                insights = analysis_result.insights
                suggestions = analysis_result.suggestions
                analysis_type = analysis_result.analysis_type

                self.logger.info(
                    "[Node: generate_answer] Analysis completed - Type: %s",
                    analysis_type,
                )
            else:
                self.logger.warning(
                    "[Node: generate_answer] DataAnalyzer not available, using EnhancedAnswerGenerator",
                )
                from ...processors.enhanced_answer_generator import (
                    EnhancedAnswerGenerator,
                )

                enhanced_generator = EnhancedAnswerGenerator(self.llm)
                answer, analysis_details = enhanced_generator.generate_enhanced_answer(
                    query,
                    final_data,
                    count,
                    query_intent,
                    requires_spatial,
                )

                analysis = analysis_details.get("analysis", "")
                insights = analysis_details.get("insights", [])
                suggestions = analysis_details.get("suggestions")
                analysis_type = analysis_details.get("analysis_type", "general")

            status, message = self._derive_status(state, count)
            should_return_data = query_intent != "summary"

            thought_step = {
                "step": current_step + 7,
                "type": "final_answer",
                "content": answer,
                "analysis_type": analysis_type,
                "insights_count": len(insights) if insights else 0,
                "has_suggestions": bool(suggestions),
                "query_intent": query_intent,
                "should_return_data": should_return_data,
                "status": "completed",
            }

            return {
                "answer": answer,
                "analysis": analysis,
                "insights": insights,
                "suggestions": suggestions,
                "analysis_type": analysis_type,
                "status": status,
                "message": message,
                "should_return_data": should_return_data,
                "thought_chain": [thought_step],
            }

        except Exception as exc:
            self.logger.error("[Node: generate_answer] Error: %s", exc)
            return self._fallback_answer(
                state,
                query=query,
                final_data=final_data,
                count=count,
                error=exc,
            )

    # ------------------------------------------------------------------
    def _derive_status(self, state: AgentState, count: int) -> tuple[str, str]:
        if state.get("error"):
            return "error", state["error"]
        if count > 0:
            return "success", "查询成功"
        return "success", "查询完成，但未找到匹配结果"

    def _fallback_answer(
        self,
        state: AgentState,
        query: str,
        final_data: Optional[List[Dict[str, Any]]],
        count: int,
        error: Exception,
    ) -> Dict[str, Any]:
        current_step = state.get("current_step", 0)
        query_intent = state.get("query_intent", "query")
        should_return_data = query_intent != "summary"

        try:
            answer = self.answer_generator.generate(query, final_data, count)
            return {
                "answer": answer,
                "analysis": None,
                "insights": None,
                "suggestions": None,
                "analysis_type": None,
                "status": "success",
                "message": "查询成功，使用回退回答生成",
                "should_return_data": should_return_data,
                "thought_chain": [
                    {
                        "step": current_step + 7,
                        "type": "final_answer",
                        "content": answer,
                        "status": "completed",
                    }
                ],
            }
        except Exception as fallback_error:
            self.logger.error(
                "[Node: generate_answer] Fallback also failed: %s",
                fallback_error,
            )
            return {
                "answer": "",
                "analysis": None,
                "insights": None,
                "suggestions": None,
                "analysis_type": None,
                "status": "error",
                "message": f"回答生成失败: {str(error)}",
                "thought_chain": [
                    {
                        "step": current_step + 7,
                        "type": "final_answer",
                        "error": str(error),
                        "status": "failed",
                    }
                ],
            }
