
import logging
import uuid
from typing import Dict, Any

from langgraph.graph import StateGraph

from .schemas import AgentState, QueryResult
from .graph.builder import GraphBuilder
from .db_checkpoint_manager import DbCheckpointManager  # 导入数据库版本
from .db_memory_manager_v16 import DbMemoryManager       # ✅ 导入 V16
from .sql_validator import SQLValidator
from .visualizer import Visualizer
from .database import DatabaseConnector

logger = logging.getLogger(__name__)

class SQLQueryAgentV16:
    """SQL 查询代理 V16

    集成 V15 的数据库持久化，并使用 V16 的真实 embedding 功能。
    """

    def __init__(self, db_connector: DatabaseConnector, db_schema: str):
        self.db_connector = db_connector
        self.db_schema = db_schema
        self.sql_validator = SQLValidator()
        self.visualizer = Visualizer()

        # ✅ 使用 V16 版本的 Memory Manager
        self.memory_manager = DbMemoryManager(db_connector=self.db_connector)

        # ✅ 使用数据库版本的 Checkpoint Manager
        self.checkpoint_manager = DbCheckpointManager(db_connector=self.db_connector)

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = GraphBuilder(self.db_connector, self.db_schema, self.sql_validator, self.visualizer)
        return builder.build_graph()

    def run(self, query: str, conversation_id: str = None) -> QueryResult:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            logger.info(f"开启新会话: {conversation_id}")

        # 尝试从数据库加载最新的 Checkpoint
        latest_checkpoint = self.checkpoint_manager.get_latest_checkpoint(conversation_id)

        if latest_checkpoint:
            logger.info(f"从 Checkpoint 加载会话: {conversation_id}")
            initial_state = latest_checkpoint
            initial_state["query"] = query  # 使用新查询
        else:
            logger.info(f"未找到 Checkpoint，创建新会话状态: {conversation_id}")
            initial_state = AgentState(
                query=query,
                conversation_id=conversation_id,
                session_history=[],
                steps=[],
                final_result=None,
                should_continue=True,
                reflection=None,
                search_queries=[],
                search_results=None,
                visualization=None
            )

        # 从长期记忆中寻找相似知识
        similar_knowledge = self.memory_manager.find_similar_knowledge(query)
        if similar_knowledge:
            logger.info(f"发现 {len(similar_knowledge)} 条相似知识")
            # 可以将相似知识注入到 initial_state 中以供 Agent 使用
            initial_state["session_history"].append(("system", f"Memory recall: Found similar past queries. Best match:\n- Query: {similar_knowledge[0]['query_text']}\n- SQL: {similar_knowledge[0]['sql_query']}"))

        final_state = self.graph.invoke(
            initial_state,
            # 使用数据库 Checkpoint 管理器
            config={"configurable": {"thread_id": conversation_id, "checkpoint_manager": self.checkpoint_manager}}
        )

        # 从最终状态提取并返回 QueryResult
        return self._prepare_result(final_state)

    def _prepare_result(self, final_state: AgentState) -> QueryResult:
        """将最终的 AgentState 转换为 QueryResult。"""
        if final_state.get("final_result"):
            final_result = final_state["final_result"]

            # 查询成功，学习经验
            self.memory_manager.learn_from_query(
                query=final_state["query"],
                sql=final_result.get("sql"),
                result=final_result, # 传递整个结果字典
                success=True
            )

            return QueryResult(
                success=True,
                message="查询成功。",
                sql=final_result.get("sql", ""),
                data=final_result.get("data"),
                visualization=final_state.get("visualization")
            )
        else:
            # 查询失败
            error_message = "Agent 실행 중 알 수 없는 오류가 발생했습니다." # 默认错误信息
            reflection = final_state.get("reflection")
            if reflection and reflection.error:
                error_message = reflection.error

            self.memory_manager.learn_from_query(
                query=final_state["query"],
                sql=None,
                result={"error": error_message},
                success=False
            )

            return QueryResult(
                success=False,
                message=error_message,
                sql=None,
                data=None,
                visualization=None
            )

