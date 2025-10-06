from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from ...schemas import AgentState
from .base import NodeBase


class HandleErrorNode(NodeBase):
    """Enhanced error handling node with retry and fallback strategies."""

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        error = state.get("error") or state.get("last_error")
        retry_count = state.get("retry_count", 0)
        current_sql = state.get("current_sql")
        current_step = state.get("current_step", 0)
        error_context = state.get("error_context", {}) or {}

        try:
            if self.error_handler:
                self.logger.info(
                    "[Node: handle_error] Using enhanced error handler, retry %s",
                    retry_count,
                )
                analysis = self.error_handler.analyze_error(
                    error_message=error,
                    sql=current_sql or "",
                    context={
                        "current_step": current_step,
                        "retry_count": retry_count,
                        "query": state.get("query"),
                    },
                )

                strategy_info = self.error_handler.determine_retry_strategy(
                    error_analysis=analysis,
                    retry_count=retry_count,
                    context={"current_step": current_step},
                )

                error_record = {
                    "step": current_step,
                    "error": error,
                    "error_type": analysis["error_type"],
                    "retry_count": retry_count,
                    "strategy": strategy_info["strategy_type"],
                    "analysis": analysis,
                }

                thought_step = self._build_enhanced_thought(
                    state,
                    error,
                    retry_count,
                    analysis,
                    strategy_info,
                )

                if not strategy_info["should_retry"]:
                    return {
                        "error": f"错误不可恢复 ({strategy_info['reason']}): {error}",
                        "error_type": analysis["error_type"],
                        "fallback_strategy": "fail",
                        "should_continue": False,
                        "error_context": error_context,
                        "error_history": [error_record],
                        "thought_chain": [thought_step],
                    }

                backoff = strategy_info.get("backoff_seconds", 0)
                if backoff > 0:
                    self.logger.info("Applying backoff: %ss", backoff)
                    time.sleep(backoff)

                strategy_type = strategy_info["strategy_type"]
                payload: Dict[str, Any] = {
                    "retry_count": retry_count + 1,
                    "last_error": error,
                    "error_type": analysis["error_type"],
                    "fallback_strategy": strategy_type,
                    "error_context": error_context,
                    "error_history": [error_record],
                    "error": None,
                    "thought_chain": [thought_step],
                }

                if strategy_type in {"retry_sql", "simplify_query"}:
                    payload["current_sql"] = None
                return payload

            return self._handle_error_basic(
                state,
                error=error,
                retry_count=retry_count,
                current_step=current_step,
                error_context=error_context,
            )

        except Exception as exc:
            self.logger.error(
                "[Node: handle_error] Error in enhanced handler: %s",
                exc,
            )
            return self._handle_error_basic(
                state,
                error=error,
                retry_count=state.get("retry_count", 0),
                current_step=state.get("current_step", 0),
                error_context=state.get("error_context", {}) or {},
            )

    # ------------------------------------------------------------------
    def _build_enhanced_thought(
        self,
        state: AgentState,
        error: Optional[str],
        retry_count: int,
        analysis: Dict[str, Any],
        strategy_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "step": state.get("current_step", 0) + 7,
            "type": "error_handling",
            "action": "enhanced_error_analysis",
            "input": {
                "error": error,
                "error_type": analysis.get("error_type"),
                "retry_count": retry_count,
            },
            "output": {
                "strategy": strategy_info,
                "root_cause": analysis.get("root_cause"),
                "fix_suggestions": (analysis.get("fix_suggestions") or [])[:3],
            },
            "status": "completed",
        }

    def _handle_error_basic(
        self,
        state: AgentState,
        error: Optional[str],
        retry_count: int,
        current_step: int,
        error_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        max_retries = state.get("max_retries", 5)
        error_context = error_context or {}

        if retry_count >= max_retries:
            self.logger.warning(
                "[Node: handle_error] Max retries exceeded (%s/%s)",
                retry_count,
                max_retries,
            )
            return {
                "error": f"重试次数已达到上限 ({max_retries}次): {error}",
                "should_continue": False,
                "fallback_strategy": "fail",
                "thought_chain": [
                    {
                        "step": current_step + 7,
                        "type": "error_handling",
                        "action": "max_retries_exceeded",
                        "error": error,
                        "retry_count": retry_count,
                        "status": "failed",
                    }
                ],
            }

        error_type = self._classify_error(error)
        strategy = self._determine_fallback_strategy(error_type, retry_count)

        error_record = {
            "step": current_step,
            "error": error,
            "error_type": error_type,
            "retry_count": retry_count,
            "strategy": strategy,
        }

        thought_step = {
            "step": current_step + 7,
            "type": "error_handling",
            "action": "classify_and_retry",
            "input": {
                "error": error,
                "error_type": error_type,
                "retry_count": retry_count,
            },
            "output": {
                "strategy": strategy,
                "will_retry": strategy != "fail",
            },
            "status": "completed",
        }

        if strategy == "retry_sql":
            return {
                "retry_count": retry_count + 1,
                "last_error": error,
                "error_type": error_type,
                "fallback_strategy": strategy,
                "error_history": [error_record],
                "current_sql": None,
                "error": None,
                "thought_chain": [thought_step],
            }

        if strategy == "simplify_query":
            return {
                "retry_count": retry_count + 1,
                "last_error": error,
                "error_type": error_type,
                "fallback_strategy": strategy,
                "error_history": [error_record],
                "current_sql": None,
                "error": None,
                "thought_chain": [thought_step],
            }

        if strategy == "retry_execution":
            backoff_time = min(2 ** retry_count, 5)
            self.logger.info(
                "[Node: handle_error] Retrying execution after %ss backoff",
                backoff_time,
            )
            time.sleep(backoff_time)
            return {
                "retry_count": retry_count + 1,
                "last_error": error,
                "error_type": error_type,
                "fallback_strategy": strategy,
                "error_history": [error_record],
                "error": None,
                "thought_chain": [thought_step],
            }

        return {
            "error": f"错误不可恢复: {error}",
            "error_type": error_type,
            "fallback_strategy": "fail",
            "should_continue": False,
            "error_history": [error_record],
            "thought_chain": [thought_step],
        }

    # ------------------------------------------------------------------
    def _classify_error(self, error: Optional[str]) -> str:
        if not error:
            return "unknown"

        error_lower = error.lower()

        # 优先识别超时错误（包含中文和英文关键词）
        if any(keyword in error_lower for keyword in ["timeout", "timed out", "查询超时", "超时"]):
            return "execution_timeout"
        if any(keyword in error_lower for keyword in ["syntax", "near", "unexpected"]):
            return "sql_syntax_error"
        if any(keyword in error_lower for keyword in ["aggregate", "聚合", "嵌套"]):
            return "sql_syntax_error"
        if any(keyword in error_lower for keyword in ["from子句", "缺少from", "missing from", "from-clause"]):
            return "sql_syntax_error"
        if any(keyword in error_lower for keyword in ["connection", "connect", "refused"]):
            return "connection_error"
        if any(keyword in error_lower for keyword in ["column", "field", "relation", "does not exist"]):
            return "field_error"
        if any(keyword in error_lower for keyword in ["permission", "denied", "access"]):
            return "permission_error"
        if any(keyword in error_lower for keyword in ["parse", "format", "decode"]):
            return "data_format_error"
        return "unknown_error"

    def _determine_fallback_strategy(self, error_type: str, retry_count: int) -> str:
        if error_type in {"sql_syntax_error", "field_error"}:
            return "retry_sql"
        if error_type == "execution_timeout":
            return "simplify_query"
        if error_type == "connection_error":
            return "retry_execution" if retry_count < 2 else "fail"
        if error_type == "data_format_error":
            return "retry_sql" if retry_count == 0 else "fail"
        if error_type == "permission_error":
            return "fail"
        return "retry_sql" if retry_count == 0 else "fail"

    def _extract_error_position(self, error_message: str) -> Optional[int]:
        pattern = r"LINE\s+(\d+):|at character\s+(\d+)"
        match = re.search(pattern, error_message)
        if match:
            return int(match.group(1) or match.group(2))
        return None

    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        pattern = r"FROM\s+([a-z_]+)|JOIN\s+([a-z_]+)"
        matches = re.findall(pattern, sql, re.IGNORECASE)
        tables: List[str] = []
        for match in matches:
            tables.extend([table for table in match if table])
        return list(set(tables))
