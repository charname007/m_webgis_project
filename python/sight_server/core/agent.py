"""
SQL查询Agent模块 - Sight Server
提供基于LangGraph的多步查询Agent，支持自然语言查询转SQL
支持Memory和Checkpoint机制
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
import json
from datetime import datetime
import time
import uuid

from .llm import BaseLLM
from .database import DatabaseConnector
from .prompts import PromptManager, PromptType
from .schemas import QueryResult, AgentState
from .processors import SQLGenerator, SQLExecutor, ResultParser, AnswerGenerator,OptimizedSQLExecutor
from .graph import build_node_context, build_node_mapping, GraphBuilder
from .memory import MemoryManager
from .optimized_memory_manager import OptimizedMemoryManager
from .checkpoint import CheckpointManager
from .error_handler import EnhancedErrorHandler  # ✅ 导入错误处理器
from .cache_manager import QueryCacheManager  # ✅ 导入缓存管理器
from .structured_logger import StructuredLogger  # ✅ 导入结构化日志器

logger = logging.getLogger(__name__)


class SQLQueryAgent:
    """
    SQL查询Agent (LangGraph + Memory + Checkpoint 实现)

    功能:
    - 自然语言转SQL查询
    - 基于LangGraph多步查询框架（最多10次迭代）
    - 支持迭代查询和结果补充
    - 支持思维链捕获
    - PostGIS空间查询支持
    - 景区旅游数据专用
    - Memory机制：短期和长期记忆
    - Checkpoint机制：断点续传和状态持久化

    架构:
    - 使用处理器组件（Processors）处理各环节
    - 使用LangGraph构建工作流
    - 支持多步迭代直到获取完整数据
    - Memory管理器记录查询历史和学习模式
    - Checkpoint管理器支持状态保存和恢复
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        enable_spatial: bool = True,
        prompt_type: PromptType = PromptType.SCENIC_QUERY,
        enable_memory: bool = True,
        enable_checkpoint: bool = True,
        checkpoint_dir: str = "./checkpoints",
        checkpoint_interval: int = 3,
        enable_error_handler: bool = True,  # ✅ 新增：是否启用增强错误处理器
        enable_cache: bool = True,  # ✅ 新增：是否启用查询缓存
        cache_manager: Optional[QueryCacheManager] = None,  # ✅ 新增：外部传入缓存管理器
        cache_ttl: int = 3600,  # ? ʱ䣨룩
        max_retries: int = 5,  # ? Դ
        graph_recursion_limit: int = 40,
    ):
        """
        初始化SQL查询Agent

        Args:
            system_prompt: 自定义系统提示词。默认使用PromptManager获取
            temperature: LLM温度参数。默认使用配置文件
            enable_spatial: 是否启用空间查询功能
            prompt_type: 提示词类型
            enable_memory: 是否启用Memory机制
            enable_checkpoint: 是否启用Checkpoint机制
            checkpoint_dir: Checkpoint保存目录
            checkpoint_interval: Checkpoint保存间隔（步数）
            enable_error_handler: 是否启用增强错误处理器（✅ 新增）
            enable_cache: 是否启用查询缓存（✅ 新增）
            cache_ttl: 缓存生存时间（秒）（✅ 新增）
            max_retries: 最大重试次数（✅ 新增）
            graph_recursion_limit: LangGraph 最大递归层数限制
        """
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgent (LangGraph + Memory + Checkpoint mode)...")

        self.enable_spatial = enable_spatial
        self.enable_memory = enable_memory
        self.enable_checkpoint = enable_checkpoint
        self.checkpoint_interval = checkpoint_interval
        self.enable_error_handler = enable_error_handler  # ✅ 新增
        self.enable_cache = enable_cache  # ✅ 新增
        self.graph_recursion_limit = graph_recursion_limit

        # ==================== 初始化核心组件 ====================

        # 初始化数据库连接
        try:
            self.db_connector = DatabaseConnector()
            self.logger.info("✓ DatabaseConnector initialized")
        except Exception as e:
            self.logger.error(f"✗ DatabaseConnector initialization failed: {e}")
            raise

        # 初始化LLM
        try:
            self.llm = BaseLLM(temperature=temperature)
            self.logger.info("✓ BaseLLM initialized")
        except Exception as e:
            self.logger.error(f"✗ BaseLLM initialization failed: {e}")
            raise

        # 获取基础提示词
        base_prompt = system_prompt or PromptManager.get_prompt(prompt_type)
        self.logger.info(f"Using prompt type: {prompt_type.value}")

        # ==================== 初始化处理器组件 ====================

        # SQL生成器
        self.sql_generator = SQLGenerator(self.llm, base_prompt)
        self.logger.info("✓ SQLGenerator initialized")

        # SQL执行器
        self.sql_executor = OptimizedSQLExecutor(self.db_connector)
        self.logger.info("✓ OptimizedSQLExecutor initialized")

        # 结果解析器
        self.result_parser = ResultParser()
        self.logger.info("✓ ResultParser initialized")

        # 答案生成器
        self.answer_generator = AnswerGenerator(self.llm)
        self.logger.info("✓ AnswerGenerator initialized")

        # Schema获取器
        from .processors import SchemaFetcher
        self.schema_fetcher = SchemaFetcher(self.db_connector)
        self.logger.info("✓ SchemaFetcher initialized")

        # ✅ 增强错误处理器（新增）
        if self.enable_error_handler:
            self.error_handler = EnhancedErrorHandler(max_retries=max_retries, enable_learning=True)
            self.logger.info("✓ EnhancedErrorHandler initialized")
        else:
            self.error_handler = None

        # 缓存管理器初始化
        if cache_manager:
            self.cache_manager = cache_manager  # ✅ 使用外部传入的缓存管理器
            self.logger.info("✓ Using external cache manager")
        elif self.enable_cache:
            try:
                self.cache_manager = QueryCacheManager(ttl=cache_ttl)
                self.logger.info("✓ QueryCacheManager initialized")
            except Exception as cache_error:
                self.logger.warning(f"QueryCacheManager unavailable, disabling cache: {cache_error}")
                self.cache_manager = None
        else:
            self.cache_manager = None

        self.result_validator = None
        self.data_analyzer = None

        # ==================== 构建LangGraph工作流 ====================

        # ✅ 初始化结构化日志器
        self.structured_logger = StructuredLogger(log_dir="./logs")
        self.logger.info("✓ StructuredLogger initialized")

        # 创建节点函数
        self.node_context = build_node_context(
            sql_generator=self.sql_generator,
            sql_executor=self.sql_executor,
            result_parser=self.result_parser,
            answer_generator=self.answer_generator,
            schema_fetcher=self.schema_fetcher,
            llm=self.llm,
            error_handler=self.error_handler,
            cache_manager=self.cache_manager,
            structured_logger=self.structured_logger,
            result_validator=self.result_validator,
            data_analyzer=self.data_analyzer,
        )
        self.node_handlers = build_node_mapping(self.node_context)
        self.logger.info("? Node handlers registered")

        # 构建图
        self.graph = GraphBuilder(
            db_connector=self.db_connector,
            db_schema=None,  # 将在运行时获取
            sql_validator=None,  # 将在运行时获取
            visualizer=None  # 将在运行时获取
        ).build_graph(self.node_handlers)
        self.logger.info("✓ LangGraph workflow compiled")

        # ==================== 初始化Memory和Checkpoint ====================

        # Memory管理器
        if self.enable_memory:
            self.memory_manager = OptimizedMemoryManager()
            self.logger.info("✓ OptimizedMemoryManager initialized")
        else:
            self.memory_manager = None

        # Checkpoint管理器
        if self.enable_checkpoint:
            self.checkpoint_manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            self.logger.info(f"✓ CheckpointManager initialized (dir: {checkpoint_dir})")
        else:
            self.checkpoint_manager = None

        self.logger.info("✓ SQLQueryAgent initialized successfully")

    def run(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        resume_from_checkpoint: Optional[str] = None
    ) -> str:
        """执行自然语言 SQL 查询，返回结构化 JSON 字符串。"""
        start_time = time.time()
        query_id: Optional[str] = None
        memory_data: Dict[str, Any] = {}

        try:
            if not isinstance(query, str):
                query = str(query)

            (
                initial_state,
                memory_data,
                conversation_id,
                query_id,
            ) = self._prepare_run_context(query, conversation_id, resume_from_checkpoint)

            result_state = self._run_with_checkpoints(initial_state)  # type: ignore

            self._update_memory_post_run(query, result_state, memory_data)

            query_result, sql_history, final_data_snapshot, data_count = self._build_query_result(result_state)
            self._log_result_details(result_state, final_data_snapshot, sql_history, query_result)

            json_output = self._serialize_query_result(query_result)

            execution_time_ms = (time.time() - start_time) * 1000
            self._log_query_completion(query_id, query_result.status, data_count, execution_time_ms)

            return json_output

        except Exception as exc:
            self.logger.error(f"Query execution failed: {exc}", exc_info=True)

            error_result = QueryResult(
                status="error",
                answer="",
                data=None,
                count=0,
                message=f"查询执行失败: {str(exc)}",
                sql=None,
            )
            json_output = error_result.model_dump_json(indent=2)

            if query_id:
                execution_time_ms = (time.time() - start_time) * 1000
                self._log_query_completion(query_id, "error", 0, execution_time_ms)

            return json_output

    def _prepare_run_context(
        self,
        query: str,
        conversation_id: Optional[str],
        resume_from_checkpoint: Optional[str],
    ) -> Tuple[AgentState, Dict[str, Any], str, str]:
        """构建初始状态并处理会话、Checkpoint 准备。"""
        self.logger.info(f"Processing query: {query}")

        if conversation_id is None:
            conversation_id = f"session_{uuid.uuid4().hex[:8]}"

        query_id = f"{conversation_id}_{int(time.time())}"
        self.structured_logger.log_query_start(query_id, query)

        memory_data: Dict[str, Any] = {}
        if self.enable_memory and self.memory_manager:
            memory_data = self.memory_manager.start_session(conversation_id)
            if memory_data:
                self.logger.debug(f"Memory session initialized with keys: {list(memory_data.keys())}")

        if resume_from_checkpoint and self.checkpoint_manager:
            self.logger.info(f"Resuming from checkpoint: {resume_from_checkpoint}")
            resumed_state = self.checkpoint_manager.resume_from_checkpoint(resume_from_checkpoint)
            if resumed_state is not None:
                initial_state = resumed_state  # type: ignore[assignment]
                self.logger.info("Successfully resumed from checkpoint")
            else:
                self.logger.warning("Checkpoint not found, creating new state")
                initial_state = self._create_initial_state(query, conversation_id, memory_data)
        else:
            initial_state = self._create_initial_state(query, conversation_id, memory_data)

        initial_state["query_id"] = query_id
        return initial_state, memory_data, conversation_id, query_id

    def _update_memory_post_run(
        self,
        query: str,
        result_state: AgentState,
        memory_data: Dict[str, Any],
    ) -> None:
        """根据查询结果更新 Memory。"""
        if not (self.enable_memory and self.memory_manager):
            return

        final_data = result_state.get("final_data")
        data_count = len(final_data) if final_data else 0
        sql_history = result_state.get("sql_history", [])
        if memory_data:
            self.logger.debug(f"Memory session bootstrap keys: {list(memory_data.keys())}")
        joined_sql = "; ".join(sql_history)
        success = result_state.get("status") == "success"

        self.memory_manager.learn_from_query(
            query=query,
            sql=joined_sql,
            result={"count": data_count},
            success=success,
        )

        self.memory_manager.add_query_to_session(
            query=query,
            result={"count": data_count},
            sql=joined_sql,
            success=success,
        )

    def _build_query_result(
        self,
        result_state: AgentState,
    ) -> Tuple[QueryResult, List[str], Optional[List[Dict[str, Any]]], int]:
        """根据工作流结果生成 QueryResult 对象。"""
        final_data = result_state.get("final_data")
        data_count = len(final_data) if final_data else 0
        should_return_data = result_state.get("should_return_data", True)
        data_for_response = final_data if should_return_data else None

        sql_history = result_state.get("sql_history", [])
        sql_string = "; ".join(sql_history) if sql_history else None

        query_result = QueryResult(
            status=result_state.get("status", "success"),
            answer=result_state.get("answer", ""),
            data=data_for_response,
            count=data_count,
            message=result_state.get("message", "查询成功"),
            sql=sql_string,
            intent_info=result_state.get("intent_info"),
        )

        return query_result, sql_history, final_data, data_count

    def _log_result_details(
        self,
        result_state: AgentState,
        final_data: Optional[List[Dict[str, Any]]],
        sql_history: List[str],
        query_result: QueryResult,
    ) -> None:
        """输出调试信息，便于排查。"""
        data_count = len(final_data) if final_data else 0
        self.logger.info(f"final_data type: {type(final_data)}")
        self.logger.info(f"final_data length: {data_count}")
        if final_data:
            self.logger.info(f"final_data[0] type: {type(final_data[0])}")
            self.logger.info(f"final_data[0] value: {final_data[0]}")

        should_return_data = result_state.get("should_return_data", True)
        query_intent = result_state.get("query_intent", "query")
        if not should_return_data:
            self.logger.info(
                "Query intent is '%s', clearing data field (only return count and answer)",
                query_intent,
            )
        else:
            self.logger.info("Query intent is '%s', returning full data", query_intent)

        self.logger.debug(f"Result state keys: {list(result_state.keys())}")
        self.logger.info(f"SQL history length: {len(sql_history)}")
        if sql_history:
            self.logger.info(f"SQL history content: {sql_history}")
            self.logger.info(f"First SQL length: {len(sql_history[0])}")
            self.logger.info(
                f"First SQL preview: {sql_history[0][:100] if sql_history[0] else 'EMPTY'}"
            )
        else:
            self.logger.warning("SQL history is empty!")

        self.logger.info(
            f"Final SQL string: {query_result.sql[:100] if query_result.sql else 'None'}..."
        )

    def _serialize_query_result(self, query_result: QueryResult) -> str:
        """序列化 QueryResult 并输出调试日志。"""
        json_output = query_result.model_dump_json(indent=2, exclude_none=True)
        self.logger.info(f"JSON output length: {len(json_output)}")
        self.logger.info(f"'sql' in JSON output: {'"sql"' in json_output}")

        parsed_json = json.loads(json_output)
        self.logger.info(f"Parsed JSON keys: {list(parsed_json.keys())}")
        self.logger.info(
            f"Parsed JSON sql field: {str(parsed_json.get('sql', 'MISSING'))[:100]}"
        )

        self.logger.info(
            f"QueryResult.sql field: {query_result.sql[:100] if query_result.sql else 'None'}..."
        )
        self.logger.info(f"QueryResult.sql type: {type(query_result.sql)}")
        self.logger.info(f"QueryResult.sql is None: {query_result.sql is None}")

        return json_output

    def _log_query_completion(
        self,
        query_id: Optional[str],
        status: str,
        result_count: int,
        execution_time_ms: float,
    ) -> None:
        """记录查询完成信息。"""
        if query_id:
            self.structured_logger.log_query_end(
                query_id=query_id,
                status=status,
                result_count=result_count,
                execution_time_ms=execution_time_ms,
            )

        self.logger.info(
            "✓ Query completed: status=%s, count=%s, time=%.0fms",
            status,
            result_count,
            execution_time_ms,
        )

    def _run_with_checkpoints(self, state: AgentState) -> Dict[str, Any]:
        """
        执行工作流并自动保存Checkpoint

        Args:
            state: 初始状态

        Returns:
            最终状态
        """
        # 如果启用Checkpoint，使用流式执行以支持中间保存
        if self.enable_checkpoint and self.checkpoint_manager:
            # TODO: LangGraph的流式执行需要特殊API
            # 这里先使用简单invoke，后续可以升级为stream()
            result_state = self.graph.invoke(state, config={"recursion_limit": self.graph_recursion_limit})

            # 执行完成后保存最终Checkpoint
            final_checkpoint_id = f"{state.get('conversation_id', 'unknown')}_final_{int(datetime.now().timestamp())}"
            self.checkpoint_manager.save_checkpoint(
                checkpoint_id=final_checkpoint_id,
                state=result_state,
                step=result_state.get("current_step", 0)
            )
            self.logger.info(f"Saved final checkpoint: {final_checkpoint_id}")

            return result_state
        else:
            # 不使用Checkpoint，直接执行
            return self.graph.invoke(state, config={"recursion_limit": self.graph_recursion_limit})

    def _create_initial_state(
        self,
        query: str,
        conversation_id: str,
        memory_data: Dict[str, Any]
    ) -> AgentState:
        """
        创建初始状态

        Args:
            query: 查询文本
            conversation_id: 会话ID
            memory_data: Memory数据

        Returns:
            初始化的AgentState
        """
        initial_state: AgentState = {
            "query": query,
            "enhanced_query": "",
            "query_intent": None,
            "requires_spatial": self.enable_spatial,
            "intent_info": None,  # ✅ 添加完整的意图信息字段
            # Schema字段
            "database_schema": None,
            "schema_fetched": False,
            "sql_history": [],
            "execution_results": [],
            "thought_chain": [],
            "current_step": 0,
            "current_sql": None,
            "current_result": None,
            "should_continue": True,
            "max_iterations": 10,  # ✨ 最大10次迭代
            "error": None,
            # Fallback重试机制字段
            "retry_count": 0,
            "max_retries": 5,
            "last_error": None,
            "error_history": [],
            "fallback_strategy": None,
            "error_type": None,
            "final_data": None,
            "answer": "",
            "status": "pending",
            "message": "",
            # Memory字段
            "session_history": memory_data.get("session_history", []),
            "conversation_id": conversation_id,
            "knowledge_base": memory_data.get("knowledge_base"),
            "learned_patterns": memory_data.get("learned_patterns", []),
            # Checkpoint字段（注意：避免使用LangGraph保留字段名）
            "saved_checkpoint_id": None,
            "saved_checkpoint_step": None,
            "is_resumed_from_checkpoint": False,
            "last_checkpoint_time": None
        }
        return initial_state

    def run_with_thought_chain(
        self,
        query: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行SQL查询并返回完整的思维链

        LangGraph模式下自动记录所有节点的执行步骤

        Args:
            query: 自然语言查询字符串
            conversation_id: 会话ID

        Returns:
            包含思维链和最终结果的字典:
            {
                "status": "success" | "error",
                "final_answer": str,
                "thought_chain": List[Dict],
                "step_count": int,
                "sql_queries_with_results": List[Dict],
                "result_data": Dict,
                "memory_info": Dict (可选),
                "checkpoint_info": Dict (可选)
            }
        """
        try:
            if not isinstance(query, str):
                query = str(query)

            self.logger.info(f"Processing query with thought chain: {query}")

            # 生成会话ID
            if conversation_id is None:
                conversation_id = f"session_{uuid.uuid4().hex[:8]}"

            # 初始化Memory
            memory_data = {}
            if self.enable_memory and self.memory_manager:
                memory_data = self.memory_manager.start_session(conversation_id)

            # 创建初始状态
            initial_state = self._create_initial_state(query, conversation_id, memory_data)

            # 执行LangGraph工作流
            result_state = self._run_with_checkpoints(initial_state)

            # 学习查询模式
            if self.enable_memory and self.memory_manager:
                # learned_pattern 变量未使用，注释掉以避免警告
                # learned_pattern = self.memory_manager.learn_from_query(
                self.memory_manager.learn_from_query(
                    query=query,
                    sql="; ".join(result_state.get("sql_history", [])),
                    result={"count": len(result_state.get("final_data", []))},
                    success=(result_state.get("status") == "success")
                )

            # 构建SQL查询记录
            sql_queries_with_results = []
            for i, sql in enumerate(result_state.get("sql_history", [])):
                execution_results = result_state.get("execution_results", [])
                result_data = execution_results[i] if i < len(execution_results) else None

                sql_queries_with_results.append({
                    "sql": sql,
                    "result": result_data.get("data") if result_data else None,
                    "count": result_data.get("count", 0) if result_data else 0,
                    "step": i + 1,
                    "status": result_data.get("status", "unknown") if result_data else "unknown"
                })

            # 构建返回结果
            response = {
                "status": result_state.get("status", "success"),
                "final_answer": result_state.get("answer", ""),
                "thought_chain": result_state.get("thought_chain", []),
                "step_count": len(result_state.get("thought_chain", [])),
                "sql_queries_with_results": sql_queries_with_results,
                "result_data": {
                    "status": result_state.get("status"),
                    "answer": result_state.get("answer"),
                    "data": result_state.get("final_data"),
                    "count": len(result_state.get("final_data", [])),
                    "message": result_state.get("message"),
                    "sql": "; ".join(result_state.get("sql_history", []))
                }
            }

            # 添加Memory信息
            if self.enable_memory and self.memory_manager:
                response["memory_info"] = {
                    "conversation_id": conversation_id,
                    "learned_patterns_count": len(result_state.get("learned_patterns", [])),
                    "session_queries_count": len(self.memory_manager.current_session.get("query_history", []))
                }

            # 添加Checkpoint信息
            if self.enable_checkpoint:
                response["checkpoint_info"] = {
                    "checkpoint_id": result_state.get("saved_checkpoint_id"),
                    "checkpoint_step": result_state.get("saved_checkpoint_step"),
                    "is_resumed": result_state.get("is_resumed_from_checkpoint", False)
                }

            return response

        except Exception as e:
            self.logger.error(f"Error in run_with_thought_chain: {e}")
            return {
                "status": "error",
                "error": f"处理查询时出现问题：{str(e)}",
                "final_answer": "",
                "thought_chain": [],
                "step_count": 0,
                "sql_queries_with_results": []
            }

    # ==================== Memory和Checkpoint管理方法 ====================

    def get_memory_export(self) -> Dict[str, Any]:
        """
        导出Memory数据

        Returns:
            Memory数据字典
        """
        if self.memory_manager:
            return self.memory_manager.export_memory()
        return {}

    def import_memory(self, memory_data: Dict[str, Any]) -> bool:
        """
        导入Memory数据

        Args:
            memory_data: Memory数据

        Returns:
            是否成功
        """
        if self.memory_manager:
            return self.memory_manager.import_memory(memory_data)
        return False

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """
        列出所有Checkpoint

        Returns:
            Checkpoint列表
        """
        if self.checkpoint_manager:
            return self.checkpoint_manager.list_checkpoints()
        return []

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        删除指定Checkpoint

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            是否成功
        """
        if self.checkpoint_manager:
            return self.checkpoint_manager.delete_checkpoint(checkpoint_id)
        return False

    def cleanup_old_checkpoints(self, keep_latest: int = 10) -> int:
        """
        清理旧的Checkpoint

        Args:
            keep_latest: 保留的最新Checkpoint数量

        Returns:
            删除的数量
        """
        if self.checkpoint_manager:
            return self.checkpoint_manager.cleanup_old_checkpoints(keep_latest)
        return 0

    # ==================== 兼容性方法（已废弃，保留以兼容旧代码）====================

    def _enhance_query(self, query: str) -> str:
        """
        [已废弃] 使用PromptManager增强查询

        注意: LangGraph模式下此方法已由 enhance_query 节点代替
        保留此方法仅为兼容性

        Args:
            query: 原始查询

        Returns:
            增强后的查询
        """
        if not self.enable_spatial:
            return query

        # 使用PromptManager检测查询类型
        query_type = PromptManager.detect_query_type(query)

        # 如果检测到空间查询，添加空间提示
        if query_type == PromptType.SPATIAL_QUERY:
            enhanced = PromptManager.build_enhanced_query(
                query,
                add_spatial_hint=True
            )
            self.logger.info("Added spatial query enhancement")
            return enhanced

        return query

    def run_structured(self, query: str) -> QueryResult:
        """
        执行SQL查询并返回 Pydantic 对象

        Args:
            query: 自然语言查询文本

        Returns:
            QueryResult Pydantic 对象
        """
        try:
            # 调用 run 获取 JSON 字符串
            json_result = self.run(query)

            # 解析为 Pydantic 对象
            result_dict = json.loads(json_result)
            result_obj = QueryResult(**result_dict)

            return result_obj

        except Exception as e:
            self.logger.error(f"Error in run_structured: {e}")

            # 返回错误对象
            return QueryResult(
                status="error",
                data=None,
                count=0,
                message=f"查询失败：{str(e)}",
                sql=None
            )

    def close(self):
        """关闭并清理资源"""
        if hasattr(self, 'db_connector'):
            self.db_connector.close()
            self.logger.info("✓ SQLQueryAgent resources closed")


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # 创建Agent（启用Memory和Checkpoint）
        print("\n=== 测试SQL查询Agent (Memory + Checkpoint) ===")
        agent = SQLQueryAgent(
            enable_memory=True,
            enable_checkpoint=True,
            checkpoint_dir="./test_checkpoints"
        )

        # 测试查询1: 简单查询
        print("\n--- 测试1: 查询5A景区 ---")
        result = agent.run("查询浙江省的5A景区", conversation_id="test-001")
        print(f"Result: {result[:200]}...")

        # 测试查询2: 带思维链
        print("\n--- 测试2: 带思维链查询 ---")
        result_with_chain = agent.run_with_thought_chain("查询杭州市的景区", conversation_id="test-001")
        print(f"Status: {result_with_chain['status']}")
        print(f"Step count: {result_with_chain['step_count']}")
        print(f"SQL queries: {len(result_with_chain['sql_queries_with_results'])}")

        if "memory_info" in result_with_chain:
            print(f"Memory info: {result_with_chain['memory_info']}")

        if "checkpoint_info" in result_with_chain:
            print(f"Checkpoint info: {result_with_chain['checkpoint_info']}")

        # 测试3: 列出Checkpoint
        print("\n--- 测试3: 列出Checkpoint ---")
        checkpoints = agent.list_checkpoints()
        print(f"Found {len(checkpoints)} checkpoints")

        # 清理资源
        agent.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
