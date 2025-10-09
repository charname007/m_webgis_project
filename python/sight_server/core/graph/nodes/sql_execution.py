from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Optional

from ...schemas import AgentState
from .base import NodeBase
from .memory_decorators import with_memory_tracking


class ExecuteSqlNode(NodeBase):
    """Execute SQL, merge results, and leverage cache when available."""

    CACHE_FIELD = "cached_result"
    FAILURE_FIELD = "generation_failure_count"

    @with_memory_tracking("sql_execution")
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        start_time = time.time()
        current_sql = state.get("current_sql")
        current_step = state.get("current_step", 0)

        if not current_sql:
            self.logger.info("[Node: execute_sql] No SQL to execute, skipping")
            return {
                "thought_chain": [
                    {
                        "step": current_step + 4,
                        "type": "sql_execution",
                        "action": "skip_execution",
                        "output": "无SQL需要执行",
                        "status": "skipped",
                    }
                ]
            }

        cached_payload = state.get(self.CACHE_FIELD)
        if cached_payload:
            return self._use_cached_result(state, cached_payload, current_sql)

        execution_result = self.sql_executor.execute(current_sql)
        if execution_result.get("status") == "error":
            return self._handle_execution_error(state, execution_result, start_time)

        final_data, thought_step = self._merge_results(state, execution_result)

        payload = {
            "current_result": execution_result,
            "final_data": final_data,
            "execution_results": [execution_result],
            "sql_history": [current_sql],
            "retry_count": 0,
            "fallback_strategy": None,
            self.FAILURE_FIELD: 0,
            "thought_chain": [thought_step],
        }

        self._log_sql_execution(state, current_sql, execution_result, start_time)
        self._maybe_cache_result(state, current_sql, execution_result, final_data)

        return payload

    def _use_cached_result(self, state: AgentState, cached: Dict[str, Any], current_sql: str) -> Dict[str, Any]:
        current_step = state.get("current_step", 0)
        execution_result = cached.get("execution_result") or {
            "status": "success",
            "data": cached.get("data"),
            "count": cached.get("count", 0),
            "message": cached.get("message", "来自缓存的结果"),
        }
        final_data = cached.get("final_data")

        thought_step = {
            "step": current_step + 4,
            "type": "sql_execution",
            "action": "use_cached_result",
            "input": current_sql,
            "output": {
                "count": execution_result.get("count"),
                "status": execution_result.get("status"),
                "cached": True,
            },
            "status": "completed",
        }

        return {
            "current_result": execution_result,
            "final_data": final_data,
            "execution_results": [execution_result],
            "sql_history": [current_sql],
            "retry_count": 0,
            "fallback_strategy": None,
            self.FAILURE_FIELD: 0,
            "thought_chain": [thought_step],
        }

    def _handle_execution_error(self, state: AgentState, execution_result: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        current_step = state.get("current_step", 0)
        error_context = self._build_error_context(state, execution_result, start_time)

        if self.structured_logger:
            query_id = state.get("query_id", "unknown")
            self.structured_logger.log_error(
                query_id=query_id,
                error_type="sql_execution_error",
                error_message=execution_result.get("error"),
                failed_sql=state.get("current_sql"),
                retry_count=state.get("retry_count", 0),
                error_code=error_context.get("error_code"),
            )

        return {
            "error": execution_result.get("error"),
            "error_context": error_context,
            "should_continue": False,
            self.FAILURE_FIELD: state.get(self.FAILURE_FIELD, 0),
            "thought_chain": [
                {
                    "step": current_step + 4,
                    "type": "sql_execution",
                    "action": "execute_sql",
                    "input": state.get("current_sql"),
                    "error": execution_result.get("error"),
                    "status": "failed",
                }
            ],
        }

    def _merge_results(self, state: AgentState, execution_result: Dict[str, Any]) -> tuple[list, dict]:
        current_step = state.get("current_step", 0)
        if current_step == 0:
            final_data = execution_result.get("data")
        else:
            previous_data = state.get("final_data", []) or []
            current_data = execution_result.get("data") or []
            final_data = self.result_parser.merge_results([previous_data, current_data])

        thought_step = {
            "step": current_step + 4,
            "type": "sql_execution",
            "action": "execute_sql",
            "input": state.get("current_sql"),
            "output": {
                "count": execution_result.get("count"),
                "status": execution_result.get("status"),
            },
            "status": "completed",
        }
        return final_data, thought_step

    def _log_sql_execution(self, state: AgentState, sql: str, execution_result: Dict[str, Any], start_time: float) -> None:
        duration_ms = (time.time() - start_time) * 1000
        if self.structured_logger:
            query_id = state.get("query_id", "unknown")
            self.structured_logger.log_sql_execution(
                query_id=query_id,
                sql=sql,
                step=state.get("current_step", 0),
                status="success",
                duration_ms=duration_ms,
                rows_returned=execution_result.get("count", 0),
            )

    def _maybe_cache_result(self, state: AgentState, sql: str, execution_result: Dict[str, Any], final_data: Any) -> None:
        if not self.cache_manager:
            return
        if state.get("current_step", 0) != 0:
            return

        query = state.get("query", "")
        cache_key = self._build_cache_key(state, query)
        if not cache_key:
            return

        payload = {
            "sql": sql,
            "execution_result": execution_result,
            "final_data": final_data,
            "message": execution_result.get("message", ""),
            "timestamp": datetime.now().isoformat(),
        }

        try:
            self.cache_manager.set(cache_key, payload, query=query)
        except Exception as exc:
            self.logger.warning('[Node: execute_sql] Failed to cache result: %s', exc)

    def _build_cache_key(self, state: AgentState, query: str) -> Optional[str]:
        if not self.cache_manager:
            return None

        context = {
            "enable_spatial": state.get("requires_spatial", False),
            "query_intent": state.get("query_intent", "query"),
            "include_sql": True,
        }

        try:
            return self.cache_manager.get_cache_key(query, context)
        except Exception as exc:
            self.logger.warning('[Node: execute_sql] Failed to compute cache key: %s', exc)
            return None

    def _build_error_context(self, state: AgentState, execution_result: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        return {
            "failed_sql": state.get("current_sql"),
            "error_message": execution_result.get("error"),
            "failed_at_step": state.get("current_step", 0),
            "query_context": {
                "original_query": state.get("query"),
                "enhanced_query": state.get("enhanced_query"),
                "intent_type": state.get("query_intent"),
                "requires_spatial": state.get("requires_spatial", False),
            },
            "execution_context": {
                "execution_time_ms": (time.time() - start_time) * 1000,
                "rows_affected": 0,
                "timestamp": datetime.now().isoformat(),
            },
        }
