from __future__ import annotations

from typing import Any, Dict, Optional

from ...schemas import AgentState
from .base import NodeBase
from .memory_decorators import with_memory_tracking


class GenerateSqlNode(NodeBase):
    """Generate SQL with cache support and failure capping."""

    CACHE_FIELD = "cached_result"
    FAILURE_FIELD = "generation_failure_count"

    @with_memory_tracking("sql_generation")
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        try:
            cached_payload = self._maybe_load_cache(state)
            if cached_payload is not None:
                return cached_payload

            result = self._generate_sql_internal(state)
            result[self.FAILURE_FIELD] = 0
            return result
        except Exception as exc:
            return self._handle_generation_error(state, exc)

    # ------------------------------------------------------------------
    def _generate_sql_internal(self, state: AgentState) -> Dict[str, Any]:
        current_step = state.get("current_step", 0)
        enhanced_query = state.get("enhanced_query", state["query"])
        fallback_strategy = state.get("fallback_strategy")
        last_error = state.get("last_error")
        validation_feedback = state.get("validation_feedback")
        match_mode = state.get("match_mode", "fuzzy")

        self.logger.info("[Node: generate_sql] Generating SQL for step %s", current_step)
        if fallback_strategy:
            self.logger.info("[Node: generate_sql] Fallback strategy: %s", fallback_strategy)
        if validation_feedback:
            self.logger.info("[Node: generate_sql] Regenerating based on validation feedback")

        sql: Optional[str] = None
        validation_retry_count = state.get("validation_retry_count", 0)

        if validation_feedback:
            previous_sql = state.get("current_sql") or (
                state["sql_history"][-1] if state.get("sql_history") else None
            )
            if previous_sql:
                intent_info = state.get("intent_info")
                sql = self.sql_generator.regenerate_with_feedback(
                    query=enhanced_query,
                    previous_sql=previous_sql,
                    feedback=validation_feedback,
                    intent_info=intent_info,
                )
                validation_retry_count += 1
            else:
                sql = self.sql_generator.generate_initial_sql(
                    enhanced_query,
                    intent_info=state.get("intent_info"),
                    match_mode=match_mode,
                )
        elif fallback_strategy == "retry_sql" and last_error:
            previous_sql = state.get("current_sql") or (
                state["sql_history"][-1] if state.get("sql_history") else None
            )
            if previous_sql:
                error_context = state.get("error_context", {})
                if hasattr(self.sql_generator, "fix_sql_with_context"):
                    sql = self.sql_generator.fix_sql_with_context(
                        sql=previous_sql,
                        error_context=error_context,
                        query=enhanced_query,
                        intent_type_override=state.get("query_intent"),
                    )
                else:
                    sql = self.sql_generator.fix_sql_with_error(
                        sql=previous_sql,
                        error=last_error,
                        query=enhanced_query,
                        intent_type=state.get("query_intent"),
                    )
            else:
                sql = self.sql_generator.generate_initial_sql(
                    enhanced_query,
                    match_mode=match_mode,
                )
        elif fallback_strategy == "simplify_query":
            previous_sql = state.get("current_sql") or (
                state["sql_history"][-1] if state.get("sql_history") else None
            )
            if previous_sql:
                sql = self.sql_generator.simplify_sql(previous_sql, max_limit=50)
            else:
                sql = self.sql_generator.generate_initial_sql(
                    enhanced_query,
                    match_mode=match_mode,
                )
                sql = self.sql_generator.simplify_sql(sql, max_limit=50)
        elif current_step == 0:
            intent_info = state.get("intent_info")
            self.logger.info("[Node: generate_sql] Using intent info: %s", intent_info)
            sql = self.sql_generator.generate_initial_sql(
                enhanced_query,
                intent_info=intent_info,
                match_mode=match_mode,
            )
        else:
            sql = self._generate_followup_sql(state, enhanced_query)
            if sql is None:
                return {
                    "current_sql": None,
                    "should_continue": False,
                    "match_mode": match_mode,
                    "thought_chain": [
                        {
                            "step": state.get("current_step", 0) + 3,
                            "type": "sql_generation",
                            "action": "skip_followup",
                            "status": "completed",
                        }
                    ],
                }

        if not sql:
            raise RuntimeError("SQL generation returned empty result")

        thought_step = {
            "step": current_step + 3,
            "type": "sql_generation",
            "action": "generate_sql",
            "input": enhanced_query,
            "output": sql,
            "status": "completed",
        }

        result: Dict[str, Any] = {
            "current_sql": sql,
            "should_continue": True,
            "match_mode": match_mode,
            "thought_chain": [thought_step],
        }

        if validation_feedback:
            result["validation_retry_count"] = validation_retry_count
            result["validation_feedback"] = None

        return result

    def _generate_followup_sql(self, state: AgentState, enhanced_query: str) -> Optional[str]:
        previous_data = state.get("final_data")
        previous_sql = state["sql_history"][-1] if state.get("sql_history") else ""

        record_count = len(previous_data) if previous_data else 0
        self.logger.info(
            "[Node: generate_sql] Preparing follow-up query; previous record count: %s",
            record_count,
        )

        match_mode = state.get("match_mode", "fuzzy")
        sql = self.sql_generator.generate_followup_sql(
            original_query=enhanced_query,
            previous_sql=previous_sql,
            record_count=record_count,
            match_mode=match_mode,
        )

        sql_history = state.get("sql_history", [])
        if sql in sql_history:
            self.logger.warning(
                "[Node: generate_sql] Generated SQL is duplicate of previous query, stopping"
            )
            return None

        return sql

    # ------------------------------------------------------------------
    def _maybe_load_cache(self, state: AgentState) -> Optional[Dict[str, Any]]:
        if not self.cache_manager:
            return None
        if state.get("current_step", 0) != 0:
            return None

        query = state.get("query", "")
        cache_key = self._build_cache_key(state, query)
        if not cache_key:
            return None

        cached = self.cache_manager.get(cache_key)
        if not cached:
            return None

        cached_sql = cached.get("sql")
        if not cached_sql:
            return None

        self.logger.info("[Node: generate_sql] Cache hit for query")

        thought_step = {
            "step": state.get("current_step", 0) + 3,
            "type": "sql_generation",
            "action": "use_cached_sql",
            "output": cached_sql,
            "status": "completed",
        }

        payload: Dict[str, Any] = {
            "current_sql": cached_sql,
            "match_mode": state.get("match_mode", "fuzzy"),
            "should_continue": True,
            "thought_chain": [thought_step],
            self.CACHE_FIELD: cached,
            self.FAILURE_FIELD: 0,
        }
        return payload

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
            self.logger.warning("[Node: generate_sql] Failed to compute cache key: %s", exc)
            return None

    def _handle_generation_error(self, state: AgentState, exc: Exception) -> Dict[str, Any]:
        failure_count = state.get(self.FAILURE_FIELD, 0) + 1
        max_failures = state.get("max_retries", 5)
        should_continue = failure_count < max_failures

        self.logger.error(
            "[Node: generate_sql] Error: %s (failure %s/%s)",
            exc,
            failure_count,
            max_failures,
        )

        payload: Dict[str, Any] = {
            "error": f"SQL生成失败: {str(exc)}",
            "match_mode": state.get("match_mode", "fuzzy"),
            "should_continue": should_continue,
            "thought_chain": [
                {
                    "step": state.get("current_step", 0) + 3,
                    "type": "sql_generation",
                    "error": str(exc),
                    "status": "failed",
                    "failure_count": failure_count,
                }
            ],
            self.FAILURE_FIELD: failure_count,
        }

        if not should_continue:
            payload["fallback_strategy"] = "fail"

        return payload
