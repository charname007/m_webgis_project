"""
LangGraph图构建器模块 - Sight Server
负责构建和编译LangGraph工作流
"""

import logging
from typing import Any, Callable, Dict

from langgraph.graph import StateGraph, END

from ..schemas import AgentState
from .edges import should_continue_querying, should_retry_or_fail, should_requery, should_summarize_conversation, should_interrupt_after_intent
from .summarization import summarize_conversation
from .context_schemas import AgentContextSchema
from langgraph.checkpoint.memory import InMemorySaver
from config import settings
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

    @staticmethod
    def build(node_handlers: Dict[str, Callable[[AgentState], Dict[str, Any]]], checkpointer=None, store=None, enable_final_validation: bool = False):
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
            "interrupt_check",
            "enhance_query",
            "generate_sql",
            "execute_sql",
            "validate_results",
            "check_results",
            "generate_answer",
            "handle_error",
        }

        # ✅ 新增：final_validation节点可选
        if enable_final_validation:
            required.add("final_validation")

        missing = required - set(node_handlers)
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"Missing node handlers: {missing_list}")

        workflow = StateGraph(AgentState, context_schema=AgentContextSchema)

        workflow.add_node("fetch_schema", node_handlers["fetch_schema"])

        workflow.add_node("analyze_intent", node_handlers["analyze_intent"])
        workflow.add_node("interrupt_check", node_handlers["interrupt_check"])
        workflow.add_node("enhance_query", node_handlers["enhance_query"])
        workflow.add_node("generate_sql", node_handlers["generate_sql"])
        workflow.add_node("execute_sql", node_handlers["execute_sql"])
        workflow.add_node("handle_error", node_handlers["handle_error"])
        workflow.add_node("check_results", node_handlers["check_results"])
        workflow.add_node("validate_results", node_handlers["validate_results"])
        workflow.add_node("generate_answer", node_handlers["generate_answer"])

        # ✅ 新增：final_validation节点可选
        if enable_final_validation:
            workflow.add_node("final_validation", node_handlers["final_validation"])
            logger.info("✓ Added final_validation node (enabled)")

        # ✅ 新增：对话总结节点
        workflow.add_node("summarize_conversation", summarize_conversation)
        logger.info("✓ Added summarize_conversation node for memory optimization")

        node_count = 11 if not enable_final_validation else 12
        logger.info(f"✓ Added {node_count} nodes to workflow (including fetch_schema, interrupt_check, handle_error, check_results, and validate_results)")

        workflow.set_entry_point(key="fetch_schema")

        # 在查询开始前添加总结检查
        workflow.add_conditional_edges(
            "fetch_schema",
            should_summarize_conversation,
            {
                "summarize_conversation": "summarize_conversation",
                "continue": "analyze_intent",
            },
        )

        workflow.add_edge("summarize_conversation", "analyze_intent")
        logger.info("✓ Added summary check at workflow start")

        # 在analyze_intent后添加条件边
        workflow.add_conditional_edges(
            "analyze_intent",
            should_interrupt_after_intent,
            {
                "interrupt_check": "interrupt_check",
                "enhance_query": "enhance_query",
            },
        )
        logger.info("✓ Added interrupt check after intent analysis")

        # interrupt_check后重新回到analyze_intent
        workflow.add_edge("interrupt_check", "analyze_intent")
        logger.info("✓ Added interrupt restart edge")
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

        # 移除validate_results后的总结检查，因为现在在查询开始时检查

        workflow.add_conditional_edges(
            "validate_results",
            should_continue_querying,
            {
                "generate_sql": "generate_sql",
                "generate_answer": "generate_answer",
            },
        )

        logger.info("✓ Added conditional edge for iteration control")

        # ✅ 新增：final_validation节点可选
        if enable_final_validation:
            workflow.add_edge("generate_answer", "final_validation")
            workflow.add_edge("final_validation", END)
            logger.info("✓ Added final validation edge and end edge")
        else:
            workflow.add_edge("generate_answer", END)
            logger.info("✓ Added direct edge from generate_answer to END (final_validation disabled)")

        compiled_graph = workflow.compile(checkpointer=checkpointer,store=store)

        logger.info("✓ LangGraph workflow built and compiled successfully with Fallback support")

        return compiled_graph

    @staticmethod
    def visualize(graph):
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
