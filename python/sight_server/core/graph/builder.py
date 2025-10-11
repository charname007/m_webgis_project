"""
LangGraph图构建器模块 - Sight Server
负责构建和编译LangGraph工作流
"""

import logging
from typing import Any, Callable, Dict

from langgraph.graph import StateGraph, END

from ..schemas import AgentState
from .edges import should_continue_querying, should_retry_or_fail, should_requery

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    LangGraph图构建器

    功能:
    - 构建多步查询流程
    - 注册执行节点
    - 配置条件边
    - 编译为可执行图
    - 支持 Fallback 重试策略
    """

    def __init__(self, db_connector, db_schema, sql_validator, visualizer):
        """
        初始化 GraphBuilder

        Args:
            db_connector: 数据库连接器
            db_schema: 数据库 schema
            sql_validator: SQL 验证器
            visualizer: 可视化器
        """
        self.db_connector = db_connector
        self.db_schema = db_schema
        self.sql_validator = sql_validator
        self.visualizer = visualizer

    def build_graph(self, node_handlers: Dict[str, Callable[[AgentState], Dict[str, Any]]]):
        """
        构建LangGraph工作流

        节点执行结构:
        `
        START
          → fetch_schema (获取数据库Schema)
          → analyze_intent (解析查询意图)
          → enhance_query (增强查询文本)
          → generate_sql (生成SQL)
          → execute_sql (执行SQL)
          → [条件] should_retry_or_fail
              ↘ handle_error (处理错误) 或 check_results (规则检查)
          → [条件] should_requery
              ↘ generate_sql (需要重新查询) 或 validate_results (结果验证)
          → [条件] should_continue_querying
              ↘ generate_sql (继续迭代) 或 generate_answer (生成答案)
              → END
        `

        Args:
            node_handlers: 节点名称到可调用对象的映射

        Returns:
            编译后的LangGraph
        """
        logger.info("Building LangGraph workflow with Fallback support...")

        required = {
            "fetch_schema",
            "analyze_intent",
            "enhance_query",
            "generate_sql",
            "execute_sql",
            "validate_results",
            "check_results",
            "generate_answer",
            "handle_error",
            "final_validation",
        }

        missing = required - set(node_handlers)
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"Missing node handlers: {missing_list}")

        workflow = StateGraph(AgentState)

        workflow.add_node("fetch_schema", node_handlers["fetch_schema"])

        workflow.add_node("analyze_intent", node_handlers["analyze_intent"])
        workflow.add_node("enhance_query", node_handlers["enhance_query"])
        workflow.add_node("generate_sql", node_handlers["generate_sql"])
        workflow.add_node("execute_sql", node_handlers["execute_sql"])
        workflow.add_node("handle_error", node_handlers["handle_error"])
        workflow.add_node("check_results", node_handlers["check_results"])
        workflow.add_node("validate_results", node_handlers["validate_results"])
        workflow.add_node("generate_answer", node_handlers["generate_answer"])
        workflow.add_node("final_validation", node_handlers["final_validation"])

        logger.info("✓ Added 10 nodes to workflow (including fetch_schema, handle_error, check_results, and validate_results)")

        workflow.set_entry_point(key="fetch_schema")

        workflow.add_edge("fetch_schema", "analyze_intent")
        workflow.add_edge("analyze_intent", "enhance_query")
        workflow.add_edge("enhance_query", "generate_sql")
        workflow.add_edge("generate_sql", "execute_sql")

        logger.info("✓ Added sequential edges")

        workflow.add_conditional_edges(
            "execute_sql",
            should_retry_or_fail,
            {
                "handle_error": "handle_error",
                "check_results": "check_results",
            },
        )

        logger.info("✓ Added conditional edge for error handling")

        workflow.add_edge("handle_error", "generate_sql")
        logger.info("✓ Added retry loop edge")

        workflow.add_conditional_edges(
            "check_results",
            should_requery,
            {
                "generate_sql": "generate_sql",
                "validate_results": "validate_results",
            },
        )

        logger.info("✓ Added conditional edge for result validation")

        workflow.add_conditional_edges(
            "validate_results",
            should_continue_querying,
            {
                "generate_sql": "generate_sql",
                "generate_answer": "generate_answer",
            },
        )

        logger.info("✓ Added conditional edge for iteration control")

        workflow.add_edge("generate_answer", "final_validation")
        workflow.add_edge("final_validation", END)
        logger.info("✓ Added final validation edge and end edge")

        compiled_graph = workflow.compile()

        logger.info("✓ LangGraph workflow built and compiled successfully with Fallback support")

        return compiled_graph

    def visualize(self, graph):
        """
        可视化当前工作流（可选功能）

        Args:
            graph: 编译后的工作流

        Returns:
            生成的Mermaid格式字符串
        """
        try:
            mermaid_str = graph.get_graph().draw_mermaid()
            return mermaid_str
        except Exception as e:
            logger.warning(f"Failed to visualize graph: {e}")
            return None


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== GraphBuilder 测试 ===\n")
    print("需要真实的 LegacyAgentNodes 实例才能完整测试")
