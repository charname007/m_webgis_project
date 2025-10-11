
import logging
import uuid

from langgraph.graph import StateGraph

from .schemas import AgentState, QueryResult
from .graph.builder import GraphBuilder
from .db_checkpoint_manager import DbCheckpointManager
from .db_memory_manager_v16 import DbMemoryManager
from .sql_validator import SQLValidator
from .visualizer import Visualizer
from .database import DatabaseConnector

from .graph.nodes import AgentNodes

logger = logging.getLogger(__name__)

class SQLQueryAgentV17:
    """SQL 查询代理 V17

    此版本将缓存逻辑完全移至 API 入口层 (main.py)，
    Agent 自身专注于执行 LangGraph 工作流。
    """

    def __init__(self, db_connector: DatabaseConnector, db_schema: str):
        self.db_connector = db_connector
        self.db_schema = db_schema
        self.sql_validator = SQLValidator()
        self.visualizer = Visualizer()
        self.memory_manager = DbMemoryManager(db_connector=self.db_connector)
        self.checkpoint_manager = DbCheckpointManager(db_connector=self.db_connector)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        nodes = AgentNodes(self.db_connector, self.db_schema, self.sql_validator, self.visualizer)
        node_handlers = {
            "fetch_schema": nodes.fetch_schema,
            "analyze_intent": nodes.analyze_intent,
            "enhance_query": nodes.enhance_query,
            "generate_sql": nodes.generate_sql,
            "execute_sql": nodes.execute_sql,
            "validate_results": nodes.validate_results,
            "check_results": nodes.check_results,
            "generate_answer": nodes.generate_answer,
            "handle_error": nodes.handle_error,
            "final_validation": nodes.final_validation,
        }
        builder = GraphBuilder(self.db_connector, self.db_schema, self.sql_validator, self.visualizer)
        return builder.build_graph(node_handlers)

    def run(self, query: str, conversation_id: str = None) -> QueryResult:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            logger.info(f"开启新会话: {conversation_id}")

        latest_checkpoint = self.checkpoint_manager.get_latest_checkpoint(conversation_id)

        if latest_checkpoint:
            logger.info(f"从 Checkpoint 加载会话: {conversation_id}")
            initial_state = latest_checkpoint
            initial_state["query"] = query
        else:
            logger.info(f"未找到 Checkpoint，创建新会话状态: {conversation_id}")
            initial_state = AgentState(
                # ==================== 输入查询 ====================
                query=query,
                enhanced_query=query,
                query_intent=None,
                requires_spatial=False,
                intent_info=None,

                # ==================== 数据库Schema ====================
                database_schema=None,
                schema_fetched=False,

                # ==================== 多步查询累积 ====================
                sql_history=[],
                execution_results=[],
                thought_chain=[],

                # ==================== 当前步骤状态 ====================
                current_step=0,
                current_sql=None,
                current_result=None,

                # ==================== 控制流程 ====================
                should_continue=True,
                max_iterations=10,
                error=None,

                # ==================== Fallback 重试机制 ====================
                retry_count=0,
                max_retries=3,
                last_error=None,
                error_history=[],
                fallback_strategy=None,
                error_type=None,
                error_context=None,

                # ==================== 日志追踪 ====================
                query_id=str(uuid.uuid4()),
                query_start_time="",
                node_execution_logs=[],

                # ==================== Memory 机制 ====================
                session_history=[],
                conversation_id=conversation_id,
                knowledge_base=None,
                learned_patterns=[],

                # ==================== Checkpoint 机制 ====================
                saved_checkpoint_id=None,
                saved_checkpoint_step=None,
                is_resumed_from_checkpoint=False,
                last_checkpoint_time=None,

                # ==================== 结果验证 ====================
                validation_history=[],
                validation_retry_count=0,
                max_validation_retries=3,
                validation_feedback=None,
                is_validation_enabled=True,
                should_return_data=True,

                # ==================== 深度分析 ====================
                analysis=None,
                insights=None,
                suggestions=None,
                analysis_type=None,

                # ==================== 最终输出 ====================
                final_data=None,
                answer="",
                status="pending",
                message="",

                # ==================== 其他字段 ====================
                reflection=None,
                search_queries=[],
                search_results=None,
                visualization=None
            )

        similar_knowledge = self.memory_manager.find_similar_knowledge(query)
        if similar_knowledge:
            logger.info(f"发现 {len(similar_knowledge)} 条相似知识，将注入 Agent 提示。")
            recalled_knowledge = (f"Memory recall: Found similar past queries. Best match:\n"
                                f"- Query: {similar_knowledge[0]['query_text']}\n"
                                f"- SQL: {similar_knowledge[0]['sql_query']}")
            initial_state["session_history"].append(("system", recalled_knowledge))

        final_state = self.graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": conversation_id, "checkpoint_manager": self.checkpoint_manager}}
        )

        # 此处的 learn_from_query 调用将被移到 main_v17.py 中，在缓存未命中后调用
        # 以确保只有最终成功且未被缓存的结果才被学习
        return self._prepare_result(final_state)

    def _prepare_result(self, final_state: AgentState) -> dict:
        """将最终的 AgentState 转换为与 QueryResult 兼容的字典格式。"""
        if final_state.get("final_result"):
            final_result = final_state["final_result"]
            return {
                "success": True,
                "query": final_state.get("query", ""),
                "final_result": final_result,
                "visualization": final_state.get("visualization")
            }
        else:
            error_message = "Agent execution failed with an unknown error."
            reflection = final_state.get("reflection")
            if reflection and reflection.error:
                error_message = reflection.error
            return {
                "success": False,
                "query": final_state.get("query", ""),
                "error": error_message
            }
