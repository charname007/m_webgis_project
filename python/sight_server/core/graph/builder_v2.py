
import logging
from langgraph.graph import StateGraph, END
from ..schemas import AgentState

logger = logging.getLogger(__name__)

class GraphBuilderV2:
    """
    简化的LangGraph图构建器 (V2)
    """

    @staticmethod
    def build(node_handlers):
        """
        构建一个简化的LangGraph工作流，其中SQL执行是通过工具调用处理的。
        """
        logger.info("Building Simplified LangGraph Workflow (V2)...")
        workflow = StateGraph(AgentState)

        # 只保留必要的节点
        workflow.add_node("generate_sql", node_handlers["generate_sql"])
        workflow.add_node("generate_answer", node_handlers["generate_answer"])

        workflow.set_entry_point("generate_sql")
        workflow.add_edge("generate_sql", "generate_answer")
        workflow.add_edge("generate_answer", END)

        compiled_graph = workflow.compile()
        logger.info("✓ Simplified LangGraph workflow built and compiled.")
        return compiled_graph
