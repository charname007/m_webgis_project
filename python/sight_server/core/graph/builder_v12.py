
import logging
from langgraph.graph import StateGraph, END
from ..schemas_v12 import AgentStateV12
from typing import Literal

logger = logging.getLogger(__name__)

def should_continue_or_finish(state: AgentStateV12) -> Literal["reflect", "__end__"]:
    """
    根据is_finished标志，决定是继续反思还是结束流程。
    """
    if state.get("is_finished"):
        logger.info("Decision: Task is finished.")
        return "__end__"
    else:
        logger.info("Decision: Continue to reflect on results.")
        return "reflect"

class GraphBuilderV12:
    """
    V12版本的图构建器，用于构建支持多步推理的分析图。
    """

    @staticmethod
    def build(node_handlers):
        workflow = StateGraph(AgentStateV12)

        # 添加所有节点
        workflow.add_node("manage_state", node_handlers["manage_state"])
        workflow.add_node("call_model_and_execute", node_handlers["call_model_and_execute"])
        workflow.add_node("reflect", node_handlers["reflect"])

        # 设置入口点
        workflow.set_entry_point("manage_state")

        # 定义边的连接
        workflow.add_edge("manage_state", "call_model_and_execute")
        
        # 添加反思循环
        workflow.add_conditional_edges(
            "call_model_and_execute",
            should_continue_or_finish,
            {
                "reflect": "reflect",
                "__end__": END
            }
        )
        workflow.add_edge("reflect", "call_model_and_execute")

        logger.info("✓ V12 Analyst graph built successfully.")
        return workflow.compile()
