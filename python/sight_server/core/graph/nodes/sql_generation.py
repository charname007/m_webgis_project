from __future__ import annotations

from typing import Any, Dict, Optional, List

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
        match_mode = state.get("match_mode", "exact")

        self.logger.info("[Node: generate_sql] Generating SQL for step %s", current_step)
        if fallback_strategy:
            self.logger.info("[Node: generate_sql] Fallback strategy: %s", fallback_strategy)
        if validation_feedback:
            self.logger.info("[Node: generate_sql] Regenerating based on validation feedback")

        # 新增：在生成 SQL 前尝试使用模式缓存
        if current_step == 0 and not validation_feedback and not fallback_strategy:
            pattern_result = self._try_generate_sql_from_patterns(state, enhanced_query)
            if pattern_result:
                self.logger.info("[Node: generate_sql] Successfully generated SQL using pattern cache")
                return pattern_result

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

    # ==================== 模式缓存相关方法 ====================

    def _try_generate_sql_from_patterns(self, state: AgentState, query: str) -> Optional[Dict[str, Any]]:
        """
        尝试从模式缓存中生成 SQL

        Args:
            state: Agent状态
            query: 查询文本

        Returns:
            如果成功生成则返回结果，否则返回None
        """
        try:
            # 获取数据库连接器
            db_connector = getattr(self.context, "db_connector", None)
            if not db_connector:
                self.logger.debug("[Node: generate_sql] No database connector available for pattern cache")
                return None

            # 查找相似的模式
            similar_patterns = self._find_similar_patterns(query, db_connector)
            if not similar_patterns:
                self.logger.debug("[Node: generate_sql] No similar patterns found")
                return None

            # 选择最佳模式
            best_pattern = self._select_best_pattern(similar_patterns)
            if not best_pattern:
                self.logger.debug("[Node: generate_sql] No suitable pattern selected")
                return None

            # 基于模式生成 SQL
            sql = self._generate_sql_from_pattern(query, best_pattern, state)
            if not sql:
                self.logger.debug("[Node: generate_sql] Failed to generate SQL from pattern")
                return None

            self.logger.info(
                f"[Node: generate_sql] Generated SQL using pattern: {best_pattern['query_template']} "
                f"(success_count: {best_pattern['success_count']}, avg_response_time: {best_pattern['avg_response_time']:.2f}s)"
            )

            # 构建返回结果
            current_step = state.get("current_step", 0)
            thought_step = {
                "step": current_step + 3,
                "type": "sql_generation",
                "action": "generate_sql_from_pattern",
                "input": query,
                "output": sql,
                "pattern_used": best_pattern["query_template"],
                "pattern_success_count": best_pattern["success_count"],
                "pattern_avg_response_time": best_pattern["avg_response_time"],
                "status": "completed",
            }

            return {
                "current_sql": sql,
                "should_continue": True,
                "match_mode": state.get("match_mode", "fuzzy"),
                "thought_chain": [thought_step],
                "pattern_based": True,
                "pattern_info": {
                    "query_template": best_pattern["query_template"],
                    "success_count": best_pattern["success_count"],
                    "avg_response_time": best_pattern["avg_response_time"]
                }
            }

        except Exception as e:
            self.logger.warning(f"[Node: generate_sql] Pattern-based generation failed: {e}")
            return None

    def _find_similar_patterns(self, query: str, db_connector) -> List[Dict[str, Any]]:
        """
        查找与查询相似的模式，同时使用数据库和内存管理器中的学习数据

        Args:
            query: 查询文本
            db_connector: 数据库连接器

        Returns:
            相似模式列表
        """
        try:
            # 提取查询模板
            query_template = self._extract_query_template(query)
            self.logger.debug(f"[Node: generate_sql] Query template: {query_template}")

            similar_patterns = []

            # 1. 从数据库获取模式
            try:
                db_patterns = db_connector.get_all_patterns()
                if db_patterns:
                    for pattern in db_patterns:
                        pattern_template = pattern.get("query_template", "")
                        if self._is_similar_template(query_template, pattern_template):
                            similar_patterns.append(pattern)
                    self.logger.debug(f"[Node: generate_sql] Found {len(db_patterns)} patterns from database")
            except Exception as e:
                self.logger.warning(f"[Node: generate_sql] Failed to get patterns from database: {e}")

            # 2. 从内存管理器获取学习到的模式
            try:
                memory_manager = getattr(self.context, "memory_manager", None)
                if memory_manager and hasattr(memory_manager, "knowledge_base"):
                    knowledge_base = memory_manager.knowledge_base
                    
                    # 从成功模式中查找
                    success_patterns = knowledge_base.get("success_patterns", [])
                    for pattern in success_patterns:
                        pattern_template = pattern.get("query_template", "")
                        if self._is_similar_template(query_template, pattern_template):
                            # 转换为与数据库模式相同的格式
                            memory_pattern = {
                                "query_template": pattern_template,
                                "sql_template": pattern.get("sql_template", ""),
                                "success_count": 1,  # 内存中的模式至少成功一次
                                "avg_response_time": pattern.get("response_time", 1.0),
                                "last_used": pattern.get("learned_at", ""),
                                "source": "memory"
                            }
                            similar_patterns.append(memory_pattern)
                    
                    self.logger.debug(f"[Node: generate_sql] Found {len(success_patterns)} patterns from memory")
            except Exception as e:
                self.logger.warning(f"[Node: generate_sql] Failed to get patterns from memory: {e}")

            self.logger.debug(f"[Node: generate_sql] Total similar patterns found: {len(similar_patterns)}")
            return similar_patterns

        except Exception as e:
            self.logger.warning(f"[Node: generate_sql] Failed to find similar patterns: {e}")
            return []

    def _extract_query_template(self, query: str) -> str:
        """
        提取查询模板（简化实现）

        Args:
            query: 查询文本

        Returns:
            查询模板
        """
        # 简单实现：提取关键词
        keywords = []

        # 查询类型
        if "查询" in query or "查找" in query:
            keywords.append("查询")
        if "统计" in query or "多少" in query:
            keywords.append("统计")
        if "距离" in query or "附近" in query:
            keywords.append("空间")

        # 实体类型
        if "景区" in query or "景点" in query:
            keywords.append("景区")
        if "省" in query or "市" in query:
            keywords.append("地区")
        if "5A" in query or "4A" in query:
            keywords.append("评级")

        return " + ".join(keywords) if keywords else "通用查询"

    def _is_similar_template(self, template1: str, template2: str) -> bool:
        """
        判断两个模板是否相似

        Args:
            template1: 模板1
            template2: 模板2

        Returns:
            是否相似
        """
        if not template1 or not template2:
            return False

        # 简单实现：检查关键词重叠
        keywords1 = set(template1.split(" + "))
        keywords2 = set(template2.split(" + "))

        # 至少50%关键词重叠
        overlap = len(keywords1 & keywords2)
        total = max(len(keywords1), len(keywords2))

        return overlap / total >= 0.5 if total > 0 else False

    def _select_best_pattern(self, patterns: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        选择最佳的模式

        Args:
            patterns: 模式列表

        Returns:
            最佳模式
        """
        if not patterns:
            return None

        # 根据成功次数和响应时间排序
        scored_patterns = []
        for pattern in patterns:
            score = self._calculate_pattern_score(pattern)
            scored_patterns.append((score, pattern))

        # 选择分数最高的模式
        scored_patterns.sort(key=lambda x: x[0], reverse=True)
        return scored_patterns[0][1] if scored_patterns else None

    def _calculate_pattern_score(self, pattern: Dict[str, Any]) -> float:
        """
        计算模式的质量分数

        Args:
            pattern: 模式数据

        Returns:
            质量分数
        """
        score = 0.0

        # 成功次数越多越好（权重：0.5）
        success_count = pattern.get("success_count", 0)
        score += 0.5 * min(success_count / 10.0, 1.0)  # 最大10次成功

        # 响应时间越短越好（权重：0.3）
        avg_response_time = pattern.get("avg_response_time", 10.0)
        if avg_response_time > 0:
            score += 0.3 * (1.0 / avg_response_time)

        # 最近使用（权重：0.2）
        last_used = pattern.get("last_used")
        if last_used:
            # 简化实现：假设最近使用的模式更好
            score += 0.2

        return score

    def _generate_sql_from_pattern(self, query: str, pattern: Dict[str, Any], state: AgentState) -> Optional[str]:
        """
        基于模式生成 SQL

        Args:
            query: 查询文本
            pattern: 模式数据
            state: Agent状态

        Returns:
            生成的 SQL，如果失败则返回None
        """
        try:
            sql_template = pattern.get("sql_template", "")
            if not sql_template:
                return None

            # 使用 SQL 生成器的模式适配功能
            if hasattr(self.sql_generator, "generate_sql_from_pattern"):
                return self.sql_generator.generate_sql_from_pattern(
                    query=query,
                    sql_template=sql_template,
                    intent_info=state.get("intent_info")
                )
            else:
                # 回退到简单的模板适配
                return self._adapt_sql_template(query, sql_template, state)

        except Exception as e:
            self.logger.warning(f"[Node: generate_sql] Failed to generate SQL from pattern: {e}")
            return None

    def _adapt_sql_template(self, query: str, sql_template: str, state: AgentState) -> str:
        """
        改进的 SQL 模板适配，利用学习到的模式

        Args:
            query: 查询文本
            sql_template: SQL模板
            state: Agent状态

        Returns:
            适配后的 SQL
        """
        try:
            # 基本的模板适配逻辑
            adapted_sql = sql_template
            
            # 1. 提取查询中的关键词
            query_lower = query.lower()
            
            # 2. 根据查询类型进行适配
            if "武汉" in query_lower:
                # 适配武汉相关的查询
                if "大学" in query_lower:
                    # 武汉大学查询
                    adapted_sql = adapted_sql.replace("WHERE 1=1", "WHERE name LIKE '%武汉大学%'")
                elif "景区" in query_lower or "景点" in query_lower:
                    # 武汉景区查询
                    adapted_sql = adapted_sql.replace("WHERE 1=1", "WHERE city LIKE '%武汉%'")
            
            elif "黄鹤楼" in query_lower:
                # 黄鹤楼查询
                adapted_sql = adapted_sql.replace("WHERE 1=1", "WHERE name LIKE '%黄鹤楼%'")
            
            elif "东湖" in query_lower:
                # 东湖查询
                adapted_sql = adapted_sql.replace("WHERE 1=1", "WHERE name LIKE '%东湖%'")
            
            # 3. 根据查询意图进行适配
            intent_info = state.get("intent_info", {})
            intent_type = intent_info.get("intent_type", "")
            
            if intent_type == "spatial_query":
                # 空间查询适配
                if "ST_DWithin" not in adapted_sql and "ST_Distance" not in adapted_sql:
                    # 添加空间查询条件
                    adapted_sql = adapted_sql.replace("WHERE 1=1", "WHERE ST_DWithin(geom, ST_GeomFromText('POINT(114.3055 30.5928)', 4326), 10000)")
            
            elif intent_type == "statistical_query":
                # 统计查询适配
                if "COUNT" not in adapted_sql and "SUM" not in adapted_sql:
                    # 添加统计函数
                    adapted_sql = adapted_sql.replace("SELECT *", "SELECT COUNT(*) as count")
            
            # 4. 确保 SQL 语法正确
            if "WHERE 1=1" in adapted_sql and "WHERE" in adapted_sql:
                # 移除多余的 WHERE 1=1
                adapted_sql = adapted_sql.replace("WHERE 1=1 AND ", "WHERE ")
                adapted_sql = adapted_sql.replace("WHERE 1=1", "")
            
            self.logger.debug(f"[Node: generate_sql] Adapted SQL template: {adapted_sql}")
            return adapted_sql
            
        except Exception as e:
            self.logger.warning(f"[Node: generate_sql] Failed to adapt SQL template: {e}")
            # 回退到原始模板
            return sql_template
