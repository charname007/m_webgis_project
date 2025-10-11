
import logging
from langgraph.graph import StateGraph, END
from ..schemas_v10 import AgentStateV10 # 使用 V10 的 schema
from typing import Literal

logger = logging.getLogger(__name__)

# V10的条件边逻辑与V9相同
def should_continue(state: AgentStateV10) -> Literal["execute_tools", "__end__"]:
    llm_response = state.get("llm_response")
    if llm_response and llm_response.tool_calls:
        logger.info("Decision: Continue to execute tools.")
        return "execute_tools"
    else:
        logger.info("Decision: End of workflow.")
        # 在结束前，确保final_answer字段已被填充
        state["final_answer"] = llm_response.content if llm_response else "I am sorry, I could not process your request."
        state["status"] = "success"
        state["message"] = "查询成功"
        return "__end__"

class GraphBuilderV10:
    """
    V10版本的图构建器，其节点将负责填充V10的状态字段。
    """

    @staticmethod
    def build(node_handlers):
        workflow = StateGraph(AgentStateV10)

        workflow.add_node("manage_state", node_handlers["manage_state"])
        workflow.add_node("call_model", node_handlers["call_model"])
        workflow.add_node("execute_tools", node_handlers["execute_tools"])

        workflow.set_entry_point("manage_state")
        workflow.add_edge("manage_state", "call_model")
        workflow.add_conditional_edges(
            "call_model",
            should_continue,
            {
                "execute_tools": "execute_tools",
                "__end__": END
            }
        )
        workflow.add_edge("execute_tools", "call_model")

        logger.info("✓ V10 graph built and compiled successfully.")
        return workflow.compile()
