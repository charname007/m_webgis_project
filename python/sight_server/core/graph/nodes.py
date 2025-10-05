"""
LangGraph节点函数模块 - Sight Server
定义所有Agent工作流的节点函数
"""

import logging
from typing import Dict, Any, Optional, List

from ..schemas import AgentState
from ..prompts import PromptManager, PromptType

logger = logging.getLogger(__name__)


class AgentNodes:
    """
    Agent节点函数集合

    包含LangGraph工作流的所有节点：
    0. fetch_schema - 获取数据库Schema
    1. analyze_intent - 分析查询意图
    2. enhance_query - 增强查询文本
    3. generate_sql - 生成SQL查询
    4. execute_sql - 执行SQL
    5. validate_results - 验证查询结果（✅ 新增）
    6. check_results - 检查结果完整性
    7. generate_answer - 生成最终答案
    8. handle_error - 错误处理和重试
    """

    def __init__(
        self,
        sql_generator,
        sql_executor,
        result_parser,
        answer_generator,
        schema_fetcher,
        llm=None,  # ✅ 新增：LLM 实例
        error_handler=None,  # ✅ 新增：错误处理器
        cache_manager=None,  # ✅ 新增：缓存管理器
        structured_logger=None,  # ✅ 新增：结构化日志器
        result_validator=None,  # ✅ 新增：结果验证器
        data_analyzer=None  # ✅ 新增：数据分析器
    ):
        """
        初始化节点函数

        Args:
            sql_generator: SQL生成器实例
            sql_executor: SQL执行器实例
            result_parser: 结果解析器实例
            answer_generator: 答案生成器实例
            schema_fetcher: Schema获取器实例
            llm: LLM 实例（用于意图分析）（✅ 新增）
            error_handler: 增强错误处理器实例（可选）（✅ 新增）
            cache_manager: 查询缓存管理器实例（可选）（✅ 新增）
            structured_logger: 结构化日志器实例（可选）（✅ 新增）
            result_validator: 结果验证器实例（可选）（✅ 新增）
            data_analyzer: 数据分析器实例（可选）（✅ 新增）
        """
        self.sql_generator = sql_generator
        self.sql_executor = sql_executor
        self.result_parser = result_parser
        self.answer_generator = answer_generator
        self.schema_fetcher = schema_fetcher
        self.llm = llm  # ✅ 保存 LLM 实例
        self.error_handler = error_handler  # ✅ 新增
        self.cache_manager = cache_manager  # ✅ 新增
        self.slog = structured_logger  # ✅ 新增：结构化日志器
        self.result_validator = result_validator  # ✅ 新增：结果验证器
        self.data_analyzer = data_analyzer  # ✅ 新增：数据分析器
        self.logger = logger

    def fetch_schema(self, state: AgentState) -> Dict[str, Any]:
        """
        节点0: 获取数据库Schema

        功能:
        - 获取数据库所有表的schema信息
        - 格式化为易于LLM理解的结构
        - 缓存到state中供后续使用

        Args:
            state: Agent状态

        Returns:
            状态更新字典
        """
        try:
            # 检查是否已获取schema
            if state.get("schema_fetched"):
                self.logger.info("[Node: fetch_schema] Schema already fetched, skipping")
                return {}

            self.logger.info("[Node: fetch_schema] Fetching database schema...")

            # 获取schema
            schema = self.schema_fetcher.fetch_schema(use_cache=True)

            # 检查是否成功
            if "error" in schema:
                self.logger.error(f"[Node: fetch_schema] Failed: {schema['error']}")
                return {
                    "database_schema": None,
                    "schema_fetched": False,
                    "thought_chain": [{
                        "step": 0,
                        "type": "schema_fetch",
                        "action": "fetch_database_schema",
                        "error": schema["error"],
                        "status": "failed"
                    }]
                }

            # 记录思维链
            thought_step = {
                "step": 0,
                "type": "schema_fetch",
                "action": "fetch_database_schema",
                "output": {
                    "table_count": len(schema.get("tables", {})),
                    "spatial_table_count": len(schema.get("spatial_tables", {}))
                },
                "status": "completed"
            }

            self.logger.info(
                f"[Node: fetch_schema] ✓ Fetched {len(schema.get('tables', {}))} tables, "
                f"{len(schema.get('spatial_tables', {}))} spatial"
            )

            return {
                "database_schema": schema,
                "schema_fetched": True,
                "thought_chain": [thought_step]
            }

        except Exception as e:
            self.logger.error(f"[Node: fetch_schema] Error: {e}")
            return {
                "database_schema": None,
                "schema_fetched": False,
                "thought_chain": [{
                    "step": 0,
                    "type": "schema_fetch",
                    "error": str(e),
                    "status": "failed"
                }]
            }

    def analyze_intent(self, state: AgentState) -> Dict[str, Any]:
        """
        节点1: 分析查询意图

        功能:
        - 使用 LLM 检测查询类型（query/summary）
        - 判断是否涉及空间查询
        - 初始化状态控制变量

        Args:
            state: Agent状态

        Returns:
            状态更新字典
        """
        try:
            query = state["query"]
            self.logger.info(f"[Node: analyze_intent] Analyzing query: {query}")

            # ✅ 使用 LLM 进行意图分析（如果 LLM 可用）
            intent_info = PromptManager.analyze_query_intent(
                query,
                llm=self.llm,  # ✅ 传递 LLM 实例
                use_llm_analysis=True  # ✅ 启用 LLM 分析
            )

            # 记录思维链
            thought_step = {
                "step": 1,
                "type": "intent_analysis",
                "action": "analyze_query_intent_with_llm" if self.llm else "analyze_query_intent_with_keywords",  # ✅ 标记使用的方法
                "input": query,
                "output": intent_info,
                "status": "completed"
            }

            self.logger.info(
                f"[Node: analyze_intent] Result: type={intent_info['intent_type']}, "
                f"spatial={intent_info['is_spatial']}, confidence={intent_info['confidence']:.2f}"
            )

            return {
                "query_intent": intent_info["intent_type"],
                "requires_spatial": intent_info["is_spatial"],
                "intent_info": intent_info,  # ✅ 保存完整的意图分析信息
                "max_iterations": 3,  # 最多3次迭代
                "current_step": 0,
                "should_continue": True,
                "thought_chain": [thought_step]
            }

        except Exception as e:
            self.logger.error(f"[Node: analyze_intent] Error: {e}")
            return {
                "error": f"意图分析失败：{str(e)}",
                "should_continue": False
            }

    def enhance_query(self, state: AgentState) -> Dict[str, Any]:
        """
        节点2: 增强查询文本

        功能:
        - 如果是空间查询，添加空间提示
        - 丰富查询上下文

        Args:
            state: Agent状态

        Returns:
            状态更新字典
        """
        try:
            query = state["query"]
            requires_spatial = state.get("requires_spatial", False)

            self.logger.info(f"[Node: enhance_query] Enhancing query, spatial={requires_spatial}")

            # 构建增强查询
            if requires_spatial:
                enhanced_query = PromptManager.build_enhanced_query(
                    query,
                    add_spatial_hint=True
                )
            else:
                enhanced_query = query

            # 记录思维链
            thought_step = {
                "step": 2,
                "type": "query_enhancement",
                "action": "enhance_query",
                "input": query,
                "output": enhanced_query,
                "status": "completed"
            }

            return {
                "enhanced_query": enhanced_query,
                "thought_chain": [thought_step]
            }

        except Exception as e:
            self.logger.error(f"[Node: enhance_query] Error: {e}")
            return {
                "enhanced_query": state["query"],  # 回退到原始查询
                "thought_chain": [{
                    "step": 2,
                    "type": "query_enhancement",
                    "error": str(e),
                    "status": "failed"
                }]
            }

    def generate_sql(self, state: AgentState) -> Dict[str, Any]:
        """
        节点3: 生成SQL查询

        功能:
        - 首次查询：生成初始SQL
        - 后续查询：根据缺失信息生成补充SQL
        - Fallback支持：根据错误修复或简化SQL
        - ✅ 缓存支持：检查是否有缓存结果（新增）

        Args:
            state: Agent状态

        Returns:
            状态更新字典
        """
        try:
            current_step = state.get("current_step", 0)
            enhanced_query = state.get("enhanced_query", state["query"])
            fallback_strategy = state.get("fallback_strategy")
            last_error = state.get("last_error")
            validation_feedback = state.get("validation_feedback")  # ✅ 新增：获取验证反馈

            # ✅ 缓存已迁移到 API 层（main.py），此处不再处理
            # 旧的节点内缓存逻辑已移除（2025-10-04）
            # if current_step == 0 and self.cache_manager:
            #     cache_key = self.cache_manager.get_cache_key(...)
            #     cached_result = self.cache_manager.get(cache_key)
            #     if cached_result: return {...}

            self.logger.info(f"[Node: generate_sql] Generating SQL for step {current_step}")
            if fallback_strategy:
                self.logger.info(f"Fallback strategy: {fallback_strategy}")
            if validation_feedback:
                self.logger.info(f"[Node: generate_sql] ✅ Regenerating based on validation feedback")

            # ✅ 获取并格式化数据库Schema
            database_schema_dict = state.get("database_schema")
            database_schema_str = None
            if database_schema_dict:
                database_schema_str = self.schema_fetcher.format_schema_for_llm(database_schema_dict)
                self.logger.debug(f"Formatted schema length: {len(database_schema_str)} chars")

            # ✅ 新增：优先处理验证反馈
            if validation_feedback:
                previous_sql = state.get("current_sql") or (
                    state["sql_history"][-1] if state.get("sql_history") else None
                )

                if previous_sql:
                    self.logger.info("[Node: generate_sql] Regenerating SQL based on validation feedback")
                    intent_info = state.get("intent_info")

                    # 调用 SQL 生成器的反馈重新生成方法
                    sql = self.sql_generator.regenerate_with_feedback(
                        query=enhanced_query,
                        previous_sql=previous_sql,
                        feedback=validation_feedback,
                        intent_info=intent_info,
                        database_schema=database_schema_str
                    )

                    # 增加验证重试计数
                    validation_retry_count = state.get("validation_retry_count", 0) + 1
                else:
                    # 没有之前的SQL，生成新的
                    sql = self.sql_generator.generate_initial_sql(
                        enhanced_query,
                        database_schema=database_schema_str
                    )
                    validation_retry_count = state.get("validation_retry_count", 0)

            # ✅ Fallback: 根据策略生成SQL
            elif fallback_strategy == "retry_sql" and last_error:
                # 策略1: 重新生成SQL（带错误信息）
                previous_sql = state.get("current_sql") or (
                    state["sql_history"][-1] if state.get("sql_history") else None
                )
                if previous_sql:
                    self.logger.info("Attempting to fix SQL based on error")
                    
                    # ✅ 获取错误上下文
                    error_context = state.get("error_context", {})
                    
                    # ✅ 检查是否有增强的修复方法
                    if hasattr(self.sql_generator, 'fix_sql_with_context'):
                        sql = self.sql_generator.fix_sql_with_context(
                            sql=previous_sql,
                            error_context=error_context,
                            query=enhanced_query,
                            database_schema=database_schema_str
                        )
                    else:
                        # 回退到基本修复方法
                        sql = self.sql_generator.fix_sql_with_error(
                            sql=previous_sql,
                            error=last_error,
                            query=enhanced_query,
                            database_schema=database_schema_str  # ✅ 传递Schema
                        )
                else:
                    # 没有之前的SQL，生成新的
                    sql = self.sql_generator.generate_initial_sql(
                        enhanced_query,
                        database_schema=database_schema_str  # ✅ 传递Schema
                    )

            elif fallback_strategy == "simplify_query":
                # 策略2: 简化查询
                previous_sql = state.get("current_sql") or (
                    state["sql_history"][-1] if state.get("sql_history") else None
                )
                if previous_sql:
                    self.logger.info("Simplifying SQL to avoid timeout")
                    sql = self.sql_generator.simplify_sql(previous_sql, max_limit=50)
                else:
                    # 没有之前的SQL，生成新的并添加LIMIT
                    sql = self.sql_generator.generate_initial_sql(
                        enhanced_query,
                        database_schema=database_schema_str  # ✅ 传递Schema
                    )
                    sql = self.sql_generator.simplify_sql(sql, max_limit=50)

            # 正常流程：初始查询或后续查询
            elif current_step == 0:
                # 初始查询
                intent_info = state.get("intent_info")  # ✅ 获取意图信息
                self.logger.info(f"Using intent info: {intent_info}")
                sql = self.sql_generator.generate_initial_sql(
                    enhanced_query,
                    intent_info=intent_info,  # ✅ 传递意图信息到生成器
                    database_schema=database_schema_str  # ✅ 传递Schema
                )
            else:
                # 后续查询：分析缺失信息
                previous_data = state.get("final_data")
                previous_sql = state["sql_history"][-1] if state.get("sql_history") else ""

                # 分析缺失信息
                missing_analysis = self.sql_generator.analyze_missing_info(
                    enhanced_query,
                    previous_data
                )

                self.logger.info(f"Missing analysis: {missing_analysis['suggestion']}")

                # 根据分析结果决定是否继续生成SQL
                if not missing_analysis["has_missing"]:
                    # 数据已完整或无法补充，不需要再查询
                    return {
                        "current_sql": None,
                        "should_continue": False,
                        "thought_chain": [{
                            "step": current_step + 3,
                            "type": "sql_generation",
                            "action": "skip_generation",
                            "output": missing_analysis["suggestion"],
                            "status": "completed"
                        }]
                    }

                # 生成补充查询
                sql = self.sql_generator.generate_followup_sql(
                    original_query=enhanced_query,
                    previous_sql=previous_sql,
                    record_count=len(previous_data) if previous_data else 0,
                    missing_fields=missing_analysis["missing_fields"],
                    database_schema=database_schema_str  # ✅ 传递Schema
                )

                # 检查生成的SQL是否与之前的重复
                sql_history = state.get("sql_history", [])
                if sql in sql_history:
                    self.logger.warning(f"Generated SQL is duplicate of previous query, stopping")
                    return {
                        "current_sql": None,
                        "should_continue": False,
                        "thought_chain": [{
                            "step": current_step + 3,
                            "type": "sql_generation",
                            "action": "skip_duplicate",
                            "output": "生成的SQL与之前查询重复，停止迭代",
                            "status": "completed"
                        }]
                    }

            # 记录思维链
            thought_step = {
                "step": current_step + 3,
                "type": "sql_generation",
                "action": "generate_sql",
                "input": enhanced_query,
                "output": sql,
                "status": "completed"
            }

            # ✅ 构建返回值
            result = {
                "current_sql": sql,
                "thought_chain": [thought_step]
            }

            # ✅ 如果有验证反馈，添加重试计数和清除反馈
            if validation_feedback:
                result["validation_retry_count"] = validation_retry_count
                result["validation_feedback"] = None  # 清除反馈，避免重复使用

            return result

        except Exception as e:
            self.logger.error(f"[Node: generate_sql] Error: {e}")
            return {
                "error": f"SQL生成失败：{str(e)}",
                "should_continue": False,
                "thought_chain": [{
                    "step": state.get("current_step", 0) + 3,
                    "type": "sql_generation",
                    "error": str(e),
                    "status": "failed"
                }]
            }

    def execute_sql(self, state: AgentState) -> Dict[str, Any]:
        """
        节点4: 执行SQL查询

        功能:
        - 执行当前SQL
        - 解析结果
        - 合并多步查询结果
        - ✅ 新增：构建错误上下文和结构化日志记录

        Args:
            state: Agent状态

        Returns:
            状态更新字典
        """
        # ✅ 导入必要模块
        import time
        from datetime import datetime

        # ✅ 记录开始时间
        start_time = time.time()

        try:
            current_sql = state.get("current_sql")
            current_step = state.get("current_step", 0)

            if not current_sql:
                # ✅ 没有SQL时直接跳过，不报错（generate_sql已经设置了should_continue=False）
                self.logger.info(f"[Node: execute_sql] No SQL to execute, skipping")
                return {
                    "thought_chain": [{
                        "step": current_step + 4,
                        "type": "sql_execution",
                        "action": "skip_execution",
                        "output": "没有SQL需要执行",
                        "status": "skipped"
                    }]
                }

            self.logger.info(f"[Node: execute_sql] Executing SQL for step {current_step}")

            # 执行SQL
            execution_result = self.sql_executor.execute(current_sql)

            if execution_result["status"] == "error":
                # ✅ 计算执行耗时
                execution_time_ms = (time.time() - start_time) * 1000

                # ✅ 构建完整错误上下文
                error_context = {
                    "failed_sql": current_sql,
                    "error_message": execution_result["error"],
                    "error_code": self._extract_pg_error_code(execution_result["error"]),
                    "error_position": self._extract_error_position(execution_result["error"]),
                    "failed_at_step": current_step,
                    "query_context": {
                        "original_query": state.get("query"),
                        "enhanced_query": state.get("enhanced_query"),
                        "intent_type": state.get("query_intent"),
                        "requires_spatial": state.get("requires_spatial", False)
                    },
                    "database_context": {
                        "schema_used": state.get("database_schema"),
                        "tables_accessed": self._extract_tables_from_sql(current_sql)
                    },
                    "execution_context": {
                        "execution_time_ms": execution_time_ms,
                        "rows_affected": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                }

                # ✅ 记录结构化日志（如果日志器可用）
                if hasattr(self, 'slog') and self.slog:
                    query_id = state.get("query_id", "unknown")
                    self.slog.log_error(
                        query_id=query_id,
                        error_type="sql_execution_error",
                        error_message=execution_result["error"],
                        failed_sql=current_sql,
                        retry_count=state.get("retry_count", 0),
                        error_code=error_context["error_code"]
                    )

                # 执行失败，返回错误上下文
                return {
                    "error": execution_result["error"],
                    "error_context": error_context,  # ✅ 传递完整上下文
                    "should_continue": False,
                    "thought_chain": [{
                        "step": current_step + 4,
                        "type": "sql_execution",
                        "action": "execute_sql",
                        "input": current_sql,
                        "error": execution_result["error"],
                        "status": "failed"
                    }]
                }

            # 执行成功
            current_result = execution_result

            # 合并结果（如果是多步查询）
            if current_step == 0:
                # 首次查询，直接使用结果
                final_data = execution_result["data"]
            else:
                # 后续查询，合并结果
                previous_data = state.get("final_data", [])
                current_data = execution_result["data"] or []

                final_data = self.result_parser.merge_results(
                    [previous_data, current_data]
                )

            # ✅ 计算执行耗时
            execution_time_ms = (time.time() - start_time) * 1000

            # ✅ 记录SQL成功执行日志
            if hasattr(self, 'slog') and self.slog:
                query_id = state.get("query_id", "unknown")
                self.slog.log_sql_execution(
                    query_id=query_id,
                    sql=current_sql,
                    step=current_step,
                    status="success",
                    duration_ms=execution_time_ms,
                    rows_returned=execution_result.get("count", 0)
                )

            # 记录思维链
            thought_step = {
                "step": current_step + 4,
                "type": "sql_execution",
                "action": "execute_sql",
                "input": current_sql,
                "output": {
                    "count": execution_result["count"],
                    "status": execution_result["status"]
                },
                "status": "completed"
            }

            # ✅ 修复：确保SQL被记录到sql_history
            # ✅ 缓存已迁移到 API 层（main.py），此处不再保存缓存（2025-10-04）
            # cache_saved = False
            # if current_step == 0 and self.cache_manager and execution_result["status"] == "success":
            #     cache_key = self.cache_manager.get_cache_key(...)
            #     cache_saved = self.cache_manager.set(cache_key, execution_result, state["query"])
            #     if cache_saved: self.logger.info(...)

            return {
                "current_result": current_result,
                "final_data": final_data,
                "execution_results": [current_result],
                "sql_history": [current_sql],  # 添加SQL到历史记录
                "retry_count": 0,  # ✅ 执行成功，重置重试计数
                "fallback_strategy": None,  # ✅ 清除fallback策略
                "thought_chain": [thought_step]
                # ❌ 移除 "_cache_saved" 字段（不再需要）
            }

        except Exception as e:
            self.logger.error(f"[Node: execute_sql] Error: {e}")
            return {
                "error": f"SQL执行失败：{str(e)}",
                "should_continue": False,
                "thought_chain": [{
                    "step": state.get("current_step", 0) + 4,
                    "type": "sql_execution",
                    "error": str(e),
                    "status": "failed"
                }]
            }

    # def validate_results(self, state: AgentState) -> Dict[str, Any]:
        """
        节点5: 验证查询结果

        功能:
        - 使用 LLM 验证查询结果是否符合用户需求
        - 检查数据完整性、准确性、相关性
        - 对于空间查询，检查是否包含必要的坐标信息
        - 决定是否需要重新查询

        Args:
            state: Agent状态

        Returns:
            状态更新字典
        """
        try:
            current_step = state.get("current_step", 0)

            # 检查验证是否启用
            if not state.get("is_validation_enabled", True):
                self.logger.info(f"[Node: validate_results] Validation disabled, skipping")
                return {
                    "validation_history": [{
                        "step": current_step,
                        "is_valid": True,
                        "message": "验证已禁用",
                        "issues": [],
                        "suggestions": []
                    }]
                }

            # 检查验证器是否可用
            if not self.result_validator:
                self.logger.warning(f"[Node: validate_results] Validator not available, skipping")
                return {
                    "validation_history": [{
                        "step": current_step,
                        "is_valid": True,
                        "message": "验证器未初始化",
                        "issues": [],
                        "suggestions": []
                    }]
                }

            self.logger.info(f"[Node: validate_results] Validating results for step {current_step}")

            # 提取验证所需的信息
            query = state.get("query", "")
            intent_info = state.get("intent_info")
            current_result = state.get("current_result", {})

            # 调用验证器
            validation_result = self.result_validator.validate(
                query=query,
                intent_info=intent_info,
                current_result=current_result,
                current_step=current_step
            )

            # 记录验证历史
            validation_record = {
                "step": current_step,
                "is_valid": validation_result.is_valid,
                "message": validation_result.validation_message,
                "issues": validation_result.issues,
                "suggestions": validation_result.improvement_suggestions,
                "confidence": validation_result.confidence
            }

            # 构建思维链记录
            thought_record = {
                "step": current_step + 4.5,  # 在 execute_sql 和 check_results 之间
                "type": "result_validation",
                "action": "validate_query_result",
                "input": {
                    "query": query,
                    "data_count": len(current_result.get("data", []))
                },
                "output": {
                    "is_valid": validation_result.is_valid,
                    "message": validation_result.validation_message,
                    "confidence": validation_result.confidence
                },
                "status": "completed" if validation_result.is_valid else "需要改进"
            }

            # 准备返回值
            result = {
                "validation_history": [validation_record],
                "thought_chain": [thought_record]
            }

            # 如果验证失败，添加反馈信息
            if not validation_result.is_valid:
                # 构建反馈信息
                feedback = f"{validation_result.validation_message}\n问题: {', '.join(validation_result.issues)}\n建议: {', '.join(validation_result.improvement_suggestions)}"
                result["validation_feedback"] = feedback

                self.logger.warning(
                    f"[Node: validate_results] ❌ Validation failed: {validation_result.validation_message}"
                )
                self.logger.info(f"Issues: {validation_result.issues}")
                self.logger.info(f"Suggestions: {validation_result.improvement_suggestions}")
            else:
                # 验证通过，清除之前的反馈
                result["validation_feedback"] = None
                self.logger.info(
                    f"[Node: validate_results] ✅ Validation passed: {validation_result.validation_message}"
                )

            return result

        except Exception as e:
            self.logger.error(f"[Node: validate_results] Error: {e}")
            # 验证出错时默认通过，避免阻塞流程
            return {
                "validation_history": [{
                    "step": state.get("current_step", 0),
                    "is_valid": True,
                    "message": f"验证过程出错，默认通过: {str(e)}",
                    "issues": [],
                    "suggestions": [],
                    "confidence": 0.5
                }],
                "validation_feedback": None,
                "thought_chain": [{
                    "step": state.get("current_step", 0) + 4.5,
                    "type": "result_validation",
                    "error": str(e),
                    "status": "failed"
                }]
            }

    def check_results(self, state: AgentState) -> Dict[str, Any]:
        """
        节点6: 检查结果完整性

        功能:
        - 评估结果完整性
        - 决定是否继续查询
        - 更新迭代步数

        Args:
            state: Agent状态

        Returns:
            状态更新字典
        """
        try:
            current_step = state.get("current_step", 0)
            max_iterations = state.get("max_iterations", 3)
            final_data = state.get("final_data")

            self.logger.info(f"[Node: check_results] Checking results for step {current_step}")

            # ✅ 改进1: 先检查是否有数据
            if not final_data:
                reason = "查询无结果"
                self.logger.warning(f"No data returned, stopping iterations")
                return {
                    "current_step": current_step + 1,
                    "should_continue": False,
                    "thought_chain": [{
                        "step": current_step + 5,
                        "type": "result_check",
                        "action": "check_completeness",
                        "output": {
                            "completeness": {"complete": False, "completeness_score": 0.0},
                            "should_continue": False,
                            "reason": reason
                        },
                        "status": "completed"
                    }]
                }

            # 评估完整性
            completeness = self.result_parser.evaluate_completeness(final_data)

            # ✅ 获取查询意图
            query_intent = state.get("query_intent")  # "query" 或 "summary"

            # ✅ Summary 查询：一次查询即可，不需要迭代补充
            if query_intent == "summary":
                count = len(final_data) if final_data else 0
                if count > 0:
                    self.logger.info(f"[Node: check_results] Summary query complete with count={count}, no iteration needed")
                    thought_step = {
                        "step": current_step + 5,
                        "type": "result_check",
                        "action": "check_completeness",
                        "output": {
                            "query_intent": "summary",
                            "count": count,
                            "reason": "Summary 查询一次完成，不需要补充数据"
                        },
                        "status": "completed"
                    }
                    return {
                        "current_step": current_step + 1,
                        "should_continue": False,  # Summary 查询不继续迭代
                        "thought_chain": [thought_step]
                    }

            # ✅ 改进2: Query 查询的完整性判断逻辑
            should_continue = False
            reason = ""

            # 首先检查迭代次数
            if current_step >= max_iterations - 1:
                # 达到最大迭代次数
                reason = f"达到最大迭代次数 ({current_step + 1}/{max_iterations})"
                self.logger.info(reason)
            # ✅ 改进3: 检查数据完整性（完整度 >= 90%）
            elif completeness["complete"] or completeness["completeness_score"] >= 0.9:
                # 数据足够完整
                reason = f"数据完整度达标 ({completeness['completeness_score']:.1%})"
                self.logger.info(reason)
            # ✅ 改进4: 如果首次查询完整度就很低（< 30%），直接停止
            elif current_step == 0 and completeness["completeness_score"] < 0.3:
                # 数据源本身不完整，无需继续查询
                reason = f"首次查询完整度过低 ({completeness['completeness_score']:.1%})，可能是数据源问题"
                self.logger.warning(reason)
            # ✅ 改进5: 检查是否有缺失字段可补充
            elif completeness["records_with_missing"] == 0:
                # 所有记录都完整
                reason = "所有记录字段完整"
                self.logger.info(reason)
            else:
                # ✅ 改进6: 只有在有明确缺失字段且未达到最大次数时才继续
                should_continue = True
                reason = f"数据不完整（完整度: {completeness['completeness_score']:.1%}，缺失字段: {completeness['missing_fields']}）"
                self.logger.info(f"{reason}, continuing to next iteration")

            # 记录思维链
            thought_step = {
                "step": current_step + 5,
                "type": "result_check",
                "action": "check_completeness",
                "output": {
                    "completeness": completeness,
                    "should_continue": should_continue,
                    "reason": reason
                },
                "status": "completed"
            }

            return {
                "current_step": current_step + 1,
                "should_continue": should_continue,
                "thought_chain": [thought_step]
            }

        except Exception as e:
            self.logger.error(f"[Node: check_results] Error: {e}")
            return {
                "should_continue": False,
                "thought_chain": [{
                    "step": state.get("current_step", 0) + 5,
                    "type": "result_check",
                    "error": str(e),
                    "status": "failed"
                }]
            }

    def validate_results(self, state: AgentState) -> Dict[str, Any]:
        """
        节点6: 验证结果质量

        功能:
        - 使用LLM验证查询结果是否符合用户问题要求
        - 检查结果的相关性、完整性和准确性
        - 如果验证失败，携带错误信息和指导重新生成SQL
        - 如果验证通过，继续生成最终答案

        Args:
            state: Agent状态

        Returns:
            状态更新字典
        """
        try:
            query = state["query"]
            final_data = state.get("final_data")
            count = len(final_data) if final_data else 0
            query_intent = state.get("query_intent")
            current_step = state.get("current_step", 0)

            self.logger.info(f"[Node: validate_results] Validating results for {count} records")
            self.logger.info(f"[Node: validate_results] Query intent: {query_intent}")

            # 无数据情况直接通过验证
            if count == 0 or not final_data:
                self.logger.info("[Node: validate_results] No data to validate, passing through")
                return {
                    "validation_passed": True,
                    "validation_reason": "无数据，无需验证",
                    "thought_chain": [{
                        "step": current_step + 6,
                        "type": "result_validation",
                        "action": "skip_validation",
                        "output": "无数据，跳过验证",
                        "status": "skipped"
                    }]
                }

            # 使用LLM验证结果质量
            validation_result = self._validate_with_llm(query, final_data, count, query_intent)

            if validation_result["passed"]:
                # 验证通过，继续生成答案
                self.logger.info("[Node: validate_results] ✓ Validation passed")
                return {
                    "validation_passed": True,
                    "validation_reason": validation_result["reason"],
                    "thought_chain": [{
                        "step": current_step + 6,
                        "type": "result_validation",
                        "action": "validate_results",
                        "output": {
                            "passed": True,
                            "reason": validation_result["reason"],
                            "confidence": validation_result["confidence"]
                        },
                        "status": "completed"
                    }]
                }
            else:
                # 验证失败，返回错误信息和指导重新生成SQL
                self.logger.warning(f"[Node: validate_results] ✗ Validation failed: {validation_result['reason']}")
                return {
                    "validation_passed": False,
                    "validation_error": validation_result["reason"],
                    "validation_guidance": validation_result["guidance"],
                    "should_continue": True,  # 继续工作流，但会重新生成SQL
                    "fallback_strategy": "retry_sql",  # 触发重新生成SQL
                    "last_error": f"结果验证失败: {validation_result['reason']}",
                    "thought_chain": [{
                        "step": current_step + 6,
                        "type": "result_validation",
                        "action": "validate_results",
                        "output": {
                            "passed": False,
                            "reason": validation_result["reason"],
                            "guidance": validation_result["guidance"],
                            "confidence": validation_result["confidence"]
                        },
                        "status": "completed"
                    }]
                }

        except Exception as e:
            self.logger.error(f"[Node: validate_results] Error: {e}")
            # 验证过程中出错，保守起见认为验证通过
            return {
                "validation_passed": True,
                "validation_reason": f"验证过程出错，默认通过: {str(e)}",
                "thought_chain": [{
                    "step": state.get("current_step", 0) + 6,
                    "type": "result_validation",
                    "error": str(e),
                    "status": "failed"
                }]
            }

    def generate_answer(self, state: AgentState) -> Dict[str, Any]:
        """
        节点7: 生成最终答案（深度分析版）

        功能:
        - 使用数据分析器生成深度分析回答
        - 结合SQL执行结果和用户问题进行智能分析
        - 生成关键洞察和相关建议
        - 设置最终状态
        - 根据查询意图决定是否在最终结果中保留完整 data

        Args:
            state: Agent状态

        Returns:
            状态更新字典
        """
        try:
            query = state["query"]
            final_data = state.get("final_data")
            count = len(final_data) if final_data else 0
            query_intent = state.get("query_intent")  # "query" 或 "summary"
            requires_spatial = state.get("requires_spatial", False)
            intent_info = state.get("intent_info")

            self.logger.info(f"[Node: generate_answer] Generating answer with deep analysis for {count} records")
            self.logger.info(f"[Node: generate_answer] Query intent: {query_intent}, Spatial: {requires_spatial}")

            # ✅ 使用新的数据分析器（如果可用）
            if self.data_analyzer:
                self.logger.info("[Node: generate_answer] Using DataAnalyzer for deep analysis")

                # 调用数据分析器
                analysis_result = self.data_analyzer.analyze(
                    query=query,
                    final_data=final_data or [],
                    intent_info=intent_info
                )

                # 提取分析结果
                answer = analysis_result.answer
                analysis = analysis_result.analysis
                insights = analysis_result.insights
                suggestions = analysis_result.suggestions
                analysis_type = analysis_result.analysis_type

                self.logger.info(f"[Node: generate_answer] Analysis completed - Type: {analysis_type}")

            else:
                # 回退：使用增强答案生成器
                self.logger.warning("[Node: generate_answer] DataAnalyzer not available, using EnhancedAnswerGenerator")

                from ..processors.enhanced_answer_generator import EnhancedAnswerGenerator
                enhanced_generator = EnhancedAnswerGenerator(self.llm)
                answer, analysis_details = enhanced_generator.generate_enhanced_answer(
                    query, final_data, count, query_intent, requires_spatial
                )

                # 转换为新格式
                analysis = analysis_details.get("analysis", "")
                insights = analysis_details.get("insights", [])
                suggestions = None
                analysis_type = "general"

            # 确定最终状态
            if state.get("error"):
                status = "error"
                message = state["error"]
            elif count > 0:
                status = "success"
                message = "查询成功"
            else:
                status = "success"
                message = "查询完成，但未找到匹配数据"

            # ✅ 根据查询意图决定是否保留 data
            # summary 类型：只返回统计结果，清空 final_data（在 agent.py 中处理）
            # query 类型：保留完整 data
            should_return_data = (query_intent != "summary")

            # 记录思维链
            thought_step = {
                "step": state.get("current_step", 0) + 7,
                "type": "final_answer",
                "content": answer,
                "analysis_type": analysis_type,
                "insights_count": len(insights) if insights else 0,
                "has_suggestions": bool(suggestions),
                "query_intent": query_intent,
                "should_return_data": should_return_data,
                "status": "completed"
            }

            return {
                "answer": answer,
                "analysis": analysis,  # ✅ 新增：深度分析内容
                "insights": insights,  # ✅ 新增：关键洞察列表
                "suggestions": suggestions,  # ✅ 新增：相关建议列表
                "analysis_type": analysis_type,  # ✅ 新增：分析类型
                "status": status,
                "message": message,
                "should_return_data": should_return_data,
                "thought_chain": [thought_step]
            }

        except Exception as e:
            self.logger.error(f"[Node: generate_answer] Error: {e}")
            # 回退到基本答案生成器
            try:
                answer = self.answer_generator.generate(query, final_data, count)
                return {
                    "answer": answer,
                    "analysis": None,  # ✅ 错误时无分析
                    "insights": None,
                    "suggestions": None,
                    "analysis_type": None,
                    "status": "success",
                    "message": "查询成功（使用基本答案生成器）",
                    "should_return_data": (state.get("query_intent") != "summary"),
                    "thought_chain": [{
                        "step": state.get("current_step", 0) + 7,
                        "type": "final_answer",
                        "content": answer,
                        "status": "completed"
                    }]
                }
            except Exception as fallback_error:
                self.logger.error(f"[Node: generate_answer] Fallback also failed: {fallback_error}")
                return {
                    "answer": "",
                    "analysis": None,
                    "insights": None,
                    "suggestions": None,
                    "analysis_type": None,
                    "status": "error",
                    "message": f"答案生成失败：{str(e)}",
                    "thought_chain": [{
                        "step": state.get("current_step", 0) + 7,
                        "type": "final_answer",
                        "error": str(e),
                        "status": "failed"
                    }]
                }

    def handle_error(self, state: AgentState) -> Dict[str, Any]:
        """
        节点8: 增强的错误处理和重试

        功能:
        - 使用增强的错误处理器进行深度错误分析
        - 智能重试策略和退避机制
        - 错误模式学习和预防
        - 自动修复建议生成
        - ✅ 新增：保留error_context

        Args:
            state: Agent状态

        Returns:
            状态更新字典
        """
        try:
            error = state.get("error") or state.get("last_error")
            retry_count = state.get("retry_count", 0)
            current_sql = state.get("current_sql")
            current_step = state.get("current_step", 0)
            
            # ✅ 获取错误上下文
            error_context = state.get("error_context", {})
            
            # 获取增强的错误处理器（如果可用）
            error_handler = getattr(self, 'error_handler', None)
            
            if error_handler:
                # 使用增强的错误处理器
                self.logger.info(f"[Node: handle_error] Using enhanced error handler, retry {retry_count}")
                
                # 深度错误分析
                error_analysis = error_handler.analyze_error(
                    error_message=error,
                    sql=current_sql or "",
                    context={
                        "current_step": current_step,
                        "retry_count": retry_count,
                        "query": state.get("query")
                    }
                )
                
                # 确定重试策略
                retry_strategy = error_handler.determine_retry_strategy(
                    error_analysis=error_analysis,
                    retry_count=retry_count,
                    context={"current_step": current_step}
                )
                
                # 记录错误历史
                error_record = {
                    "step": current_step,
                    "error": error,
                    "error_type": error_analysis["error_type"],
                    "retry_count": retry_count,
                    "strategy": retry_strategy["strategy_type"],
                    "analysis": error_analysis
                }
                
                # 记录思维链
                thought_step = {
                    "step": current_step + 7,
                    "type": "error_handling",
                    "action": "enhanced_error_analysis",
                    "input": {
                        "error": error,
                        "error_type": error_analysis["error_type"],
                        "retry_count": retry_count
                    },
                    "output": {
                        "strategy": retry_strategy,
                        "root_cause": error_analysis["root_cause"],
                        "fix_suggestions": error_analysis["fix_suggestions"][:3]  # 只显示前3条建议
                    },
                    "status": "completed"
                }
                
                # 根据策略返回不同的状态更新
                if not retry_strategy["should_retry"]:
                    # 不重试，直接失败
                    return {
                        "error": f"错误无法恢复 ({retry_strategy['reason']}): {error}",
                        "error_type": error_analysis["error_type"],
                        "fallback_strategy": "fail",
                        "should_continue": False,
                        "error_context": error_context,  # ✅ 保留错误上下文
                        "error_history": [error_record],
                        "thought_chain": [thought_step]
                    }
                
                # 应用退避时间
                if retry_strategy["backoff_seconds"] > 0:
                    import time
                    self.logger.info(f"Applying backoff: {retry_strategy['backoff_seconds']}s")
                    time.sleep(retry_strategy["backoff_seconds"])
                
                # 根据策略类型返回状态更新
                if retry_strategy["strategy_type"] == "retry_sql":
                    return {
                        "retry_count": retry_count + 1,
                        "last_error": error,
                        "error_type": error_analysis["error_type"],
                        "fallback_strategy": retry_strategy["strategy_type"],
                        "error_context": error_context,  # ✅ 保留错误上下文
                        "error_history": [error_record],
                        "current_sql": None,  # 清除当前SQL，强制重新生成
                        "error": None,  # 清除错误标志，允许重试
                        "thought_chain": [thought_step]
                    }
                    
                elif retry_strategy["strategy_type"] == "simplify_query":
                    return {
                        "retry_count": retry_count + 1,
                        "last_error": error,
                        "error_type": error_analysis["error_type"],
                        "fallback_strategy": retry_strategy["strategy_type"],
                        "error_context": error_context,  # ✅ 保留错误上下文
                        "error_history": [error_record],
                        "current_sql": None,
                        "error": None,
                        "thought_chain": [thought_step]
                    }
                    
                elif retry_strategy["strategy_type"] == "retry_execution":
                    return {
                        "retry_count": retry_count + 1,
                        "last_error": error,
                        "error_type": error_analysis["error_type"],
                        "fallback_strategy": retry_strategy["strategy_type"],
                        "error_context": error_context,  # ✅ 保留错误上下文
                        "error_history": [error_record],
                        "error": None,
                        "thought_chain": [thought_step]
                    }
                    
            else:
                # 回退到基本错误处理
                return self._handle_error_basic(state, error, retry_count, current_step, error_context)
                
        except Exception as e:
            self.logger.error(f"[Node: handle_error] Error in enhanced error handler: {e}")
            # 回退到基本错误处理
            return self._handle_error_basic(state, error, state.get("retry_count", 0), state.get("current_step", 0), state.get("error_context", {}))

    def _handle_error_basic(self, state: AgentState, error: str, retry_count: int, current_step: int, error_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        基本错误处理（回退方法）

        Args:
            state: Agent状态
            error: 错误信息
            retry_count: 重试次数
            current_step: 当前步骤
            error_context: 错误上下文（可选）

        Returns:
            状态更新字典
        """
        max_retries = state.get("max_retries", 5)

        # 检查是否超过最大重试次数
        if retry_count >= max_retries:
            self.logger.warning(f"Max retries exceeded ({retry_count}/{max_retries})")
            return {
                "error": f"重试次数已达上限 ({max_retries}次): {error}",
                "should_continue": False,
                "fallback_strategy": "fail",
                "thought_chain": [{
                    "step": current_step + 7,
                    "type": "error_handling",
                    "action": "max_retries_exceeded",
                    "error": error,
                    "retry_count": retry_count,
                    "status": "failed"
                }]
            }

        # 分类错误类型
        error_type = self._classify_error(error)
        self.logger.info(f"Error classified as: {error_type}")

        # 根据错误类型决定策略
        strategy = self._determine_fallback_strategy(error_type, retry_count)
        self.logger.info(f"Fallback strategy: {strategy}")

        # 记录错误历史
        error_record = {
            "step": current_step,
            "error": error,
            "error_type": error_type,
            "retry_count": retry_count,
            "strategy": strategy
        }

        # 记录思维链
        thought_step = {
            "step": current_step + 7,
            "type": "error_handling",
            "action": "classify_and_retry",
            "input": {
                "error": error,
                "error_type": error_type,
                "retry_count": retry_count
            },
            "output": {
                "strategy": strategy,
                "will_retry": strategy != "fail"
            },
            "status": "completed"
        }

        # 根据策略返回不同的状态更新
        if strategy == "retry_sql":
            # 重新生成SQL
            return {
                "retry_count": retry_count + 1,
                "last_error": error,
                "error_type": error_type,
                "fallback_strategy": strategy,
                "error_history": [error_record],
                "current_sql": None,  # 清除当前SQL，强制重新生成
                "error": None,  # ✅ 清除错误标志，允许重试
                "thought_chain": [thought_step]
            }

        elif strategy == "simplify_query":
            # 简化查询（通过设置标志让generate_sql简化）
            return {
                "retry_count": retry_count + 1,
                "last_error": error,
                "error_type": error_type,
                "fallback_strategy": strategy,
                "error_history": [error_record],
                "current_sql": None,
                "error": None,  # ✅ 清除错误标志，允许重试
                "thought_chain": [thought_step]
            }

        elif strategy == "retry_execution":
            # 直接重试执行（保留当前SQL）
            import time
            # 指数退避：1s, 2s, 4s
            backoff_time = 2 ** retry_count
            self.logger.info(f"Retrying execution after {backoff_time}s backoff")
            time.sleep(min(backoff_time, 5))  # 最多等待5秒

            return {
                "retry_count": retry_count + 1,
                "last_error": error,
                "error_type": error_type,
                "fallback_strategy": strategy,
                "error_history": [error_record],
                "error": None,  # 清除错误标志，允许继续
                "thought_chain": [thought_step]
            }

        else:  # fail
            # 无法恢复，直接失败
            return {
                "error": f"错误无法恢复: {error}",
                "error_type": error_type,
                "fallback_strategy": "fail",
                "should_continue": False,
                "error_history": [error_record],
                "thought_chain": [thought_step]
            }

    def _classify_error(self, error: Optional[str]) -> str:
        """
        分类错误类型

        Args:
            error: 错误信息

        Returns:
            错误类型: sql_syntax/timeout/connection/field/permission/unknown
        """
        if not error:
            return "unknown"

        error_lower = error.lower()

        # ✅ 优先级1：SQL语法错误（细分类型）
        if any(keyword in error_lower for keyword in ["syntax", "near", "unexpected"]):
            return "sql_syntax_error"
        # ✅ 新增：聚合函数错误
        elif any(keyword in error_lower for keyword in ["aggregate", "聚合", "嵌套"]):
            return "sql_syntax_error"
        # ✅ 新增：FROM子句错误
        elif any(keyword in error_lower for keyword in ["from子句", "丢失from", "missing from", "from-clause"]):
            return "sql_syntax_error"
        # 优先级2：超时错误
        elif any(keyword in error_lower for keyword in ["timeout", "timed out"]):
            return "execution_timeout"
        # 优先级3：连接错误
        elif any(keyword in error_lower for keyword in ["connection", "connect", "refused"]):
            return "connection_error"
        # 优先级4：字段/表错误
        elif any(keyword in error_lower for keyword in ["column", "field", "relation", "does not exist"]):
            return "field_error"
        # 优先级5：权限错误
        elif any(keyword in error_lower for keyword in ["permission", "denied", "access"]):
            return "permission_error"
        # 优先级6：数据格式错误
        elif any(keyword in error_lower for keyword in ["parse", "format", "decode"]):
            return "data_format_error"
        else:
            return "unknown_error"

    def _determine_fallback_strategy(
        self,
        error_type: str,
        retry_count: int
    ) -> str:
        """
        根据错误类型和重试次数决定回退策略

        Args:
            error_type: 错误类型
            retry_count: 当前重试次数

        Returns:
            策略: retry_sql/simplify_query/retry_execution/fail
        """
        # SQL语法错误或字段错误 → 重新生成SQL
        if error_type in ["sql_syntax_error", "field_error"]:
            return "retry_sql"

        # 超时错误 → 简化查询
        elif error_type == "execution_timeout":
            return "simplify_query"

        # 连接错误 → 直接重试（带退避）
        elif error_type == "connection_error":
            if retry_count < 2:  # 只重试2次
                return "retry_execution"
            else:
                return "fail"

        # 数据格式错误 → 第一次重试，第二次失败
        elif error_type == "data_format_error":
            if retry_count == 0:
                return "retry_sql"
            else:
                return "fail"

        # 权限错误 → 直接失败
        elif error_type == "permission_error":
            return "fail"

        # 未知错误 → 第一次重试SQL，之后失败
        else:
            if retry_count == 0:
                return "retry_sql"
            else:
                return "fail"

    # ==================== 辅助方法（用于错误上下文构建）====================

    def _extract_pg_error_code(self, error_message: str) -> Optional[str]:
        """
        从PostgreSQL错误信息中提取错误码

        Args:
            error_message: 错误信息

        Returns:
            错误码（如 "42P01"）或 None
        """
        import re

        # 方法1：从SQLSTATE中提取
        pattern1 = r'SQLSTATE:\s*([0-9A-Z]{5})'
        match = re.search(pattern1, error_message)
        if match:
            return match.group(1)

        # 方法2：从错误信息中推断常见错误码
        error_lower = error_message.lower()
        if 'does not exist' in error_lower:
            if 'column' in error_lower:
                return "42703"  # undefined_column
            elif 'table' in error_lower or 'relation' in error_lower:
                return "42P01"  # undefined_table
        elif 'syntax error' in error_lower:
            return "42601"  # syntax_error
        elif 'permission denied' in error_lower:
            return "42501"  # insufficient_privilege

        return None

    def _extract_error_position(self, error_message: str) -> Optional[int]:
        """
        从错误信息中提取错误位置

        Args:
            error_message: 错误信息

        Returns:
            错误位置（字符偏移）或 None
        """
        import re

        # 提取LINE或at character
        pattern = r'LINE\s+(\d+):|at character\s+(\d+)'
        match = re.search(pattern, error_message)
        if match:
            return int(match.group(1) or match.group(2))

        return None

    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """
        从SQL中提取表名

        Args:
            sql: SQL语句

        Returns:
            表名列表
        """
        import re

        tables = []
        # FROM table1, FROM table1 JOIN table2
        pattern = r'FROM\s+([a-z_]+)|JOIN\s+([a-z_]+)'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        for match in matches:
            tables.extend([t for t in match if t])

        return list(set(tables))

    def _validate_with_llm(
        self,
        query: str,
        data: List[Dict[str, Any]],
        count: int,
        query_intent: str
    ) -> Dict[str, Any]:
        """
        使用LLM验证结果质量

        Args:
            query: 用户查询
            data: 查询结果数据
            count: 结果数量
            query_intent: 查询意图

        Returns:
            验证结果字典
        """
        try:
            if not self.llm:
                # 没有LLM时默认通过验证
                return {
                    "passed": True,
                    "reason": "无LLM可用，默认通过验证",
                    "confidence": 0.5,
                    "guidance": ""
                }

            # 准备数据预览
            data_preview = self._prepare_validation_data_preview(data, count)

            # 构建验证提示词
            prompt = f"""你是一个数据质量验证专家。请评估以下查询结果是否符合用户问题的要求。

## 用户查询
{query}

## 查询意图
{query_intent}

## 查询结果
- 结果数量: {count}
- 数据预览: {data_preview}

## 验证标准
请从以下角度评估结果质量：

### 1. 相关性
- 结果是否直接回答了用户的问题？
- 数据是否与查询意图匹配？

### 2. 完整性
- 结果是否完整？是否有明显缺失？
- 对于统计查询，数据是否足够进行有意义的分析？

### 3. 准确性
- 数据看起来是否合理和准确？
- 是否有明显的异常值或错误数据？

### 4. 实用性
- 这些结果对用户是否有实际价值？
- 是否需要更多数据才能满足用户需求？

请给出评估结果：
- 如果结果质量良好，请说明原因
- 如果结果质量不佳，请指出具体问题并提供改进建议

评估结果:"""

            # 调用LLM
            response = self.llm.llm.invoke(prompt)

            if hasattr(response, 'content'):
                validation_text = response.content.strip()
            else:
                validation_text = str(response).strip()

            # 解析验证结果
            return self._parse_validation_result(validation_text, query, count)

        except Exception as e:
            self.logger.error(f"LLM validation failed: {e}")
            # 验证失败时默认通过
            return {
                "passed": True,
                "reason": f"验证过程出错，默认通过: {str(e)}",
                "confidence": 0.3,
                "guidance": "请检查数据源和查询条件"
            }

    def _prepare_validation_data_preview(self, data: List[Dict[str, Any]], count: int) -> str:
        """
        准备验证用的数据预览

        Args:
            data: 查询结果
            count: 结果数量

        Returns:
            数据预览字符串
        """
        if not data:
            return "无数据"

        # 限制预览记录数
        preview_count = min(5, len(data))
        preview_data = data[:preview_count]

        preview_lines = []
        for i, record in enumerate(preview_data):
            # 提取关键信息
            key_info = []
            for field in ['name', 'level', '评分', '所属省份', '所属城市']:
                if field in record and record[field]:
                    key_info.append(f"{field}: {record[field]}")
            
            if key_info:
                preview_lines.append(f"记录 {i+1}: {', '.join(key_info)}")

        preview_text = "\n".join(preview_lines)

        if count > preview_count:
            preview_text += f"\n... 还有 {count - preview_count} 条记录"

        return preview_text

    def _parse_validation_result(self, validation_text: str, query: str, count: int) -> Dict[str, Any]:
        """
        解析LLM验证结果

        Args:
            validation_text: LLM验证文本
            query: 用户查询
            count: 结果数量

        Returns:
            结构化的验证结果
        """
        validation_lower = validation_text.lower()

        # 判断验证是否通过
        passed_keywords = ['良好', '合适', '符合', '正确', '通过', 'good', 'suitable', 'appropriate', 'correct']
        failed_keywords = ['不佳', '不完整', '不相关', '错误', '失败', 'poor', 'incomplete', 'irrelevant', 'wrong', 'failed']

        passed = any(keyword in validation_lower for keyword in passed_keywords)
        failed = any(keyword in validation_lower for keyword in failed_keywords)

        # 计算置信度
        if passed and not failed:
            confidence = 0.8
            reason = "结果质量良好，符合用户查询要求"
            guidance = ""
        elif failed and not passed:
            confidence = 0.2
            reason = "结果质量不佳，需要改进"
            # 提取改进建议
            guidance = self._extract_guidance(validation_text)
        else:
            # 不确定的情况
            confidence = 0.5
            reason = "结果质量一般，建议进一步验证"
            guidance = "请检查查询条件和数据源"

        return {
            "passed": passed,
            "reason": reason,
            "confidence": confidence,
            "guidance": guidance,
            "raw_validation": validation_text
        }

    def _extract_guidance(self, validation_text: str) -> str:
        """
        从验证文本中提取改进建议

        Args:
            validation_text: 验证文本

        Returns:
            改进建议
        """
        # 简单的关键词提取
        guidance_keywords = ['建议', '改进', '应该', '需要', '可以', 'suggest', 'recommend', 'should', 'need', 'could']
        
        lines = validation_text.split('\n')
        guidance_lines = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in guidance_keywords):
                guidance_lines.append(line.strip())
        
        if guidance_lines:
            return "\n".join(guidance_lines[:3])  # 最多返回3条建议
        
        return "请调整查询条件或检查数据源"


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== AgentNodes 测试 ===\n")

    # 测试状态初始化
    test_state: AgentState = {
        "query": "查询浙江省的5A景区",
        "enhanced_query": "",
        "query_intent": None,
        "requires_spatial": False,
        "sql_history": [],
        "execution_results": [],
        "thought_chain": [],
        "current_step": 0,
        "current_sql": None,
        "current_result": None,
        "should_continue": True,
        "max_iterations": 3,
        "error": None,
        "final_data": None,
        "answer": "",
        "status": "pending",
        "message": ""
    }

    print(f"Initial state: query='{test_state['query']}'")
    print(f"Max iterations: {test_state['max_iterations']}")
