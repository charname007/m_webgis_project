
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
        builder = GraphBuilder(self.db_connector, self.db_schema, self.sql_validator, self.visualizer)
        return builder.build_graph()

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
        """将最终的 AgentState 转换为一个普通字典，以便在 main.py 中进一步处理。"""
        if final_state.get("final_result"):
            return {
                "success": True,
                "query": final_state.get("query", ""),
                "final_result": final_state["final_result"],
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
