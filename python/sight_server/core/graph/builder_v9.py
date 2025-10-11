
import logging
from langgraph.graph import StateGraph, END
from ..schemas_v9 import AgentStateV9
from typing import Literal

logger = logging.getLogger(__name__)

# 定义条件边的逻辑函数
def should_continue(state: AgentStateV9) -> Literal["execute_tools", "__end__"]:
    """
    根据模型的响应决定是执行工具还是结束流程。
    """
    llm_response = state.get("llm_response")
    if llm_response and llm_response.tool_calls:
        # 如果有工具调用，则转向工具执行节点
        logger.info("Decision: Continue to execute tools.")
        return "execute_tools"
    else:
        # 如果没有工具调用，说明已生成最终答案，结束流程
        logger.info("Decision: End of workflow.")
        return "__end__"

class GraphBuilderV9:
    """
    V9版本的图构建器，用于构建混合状态/工具调用工作流。
    """

    @staticmethod
    def build(node_handlers):
        """
        构建LangGraph工作流。
        """
        workflow = StateGraph(AgentStateV9)

        # 添加节点
        workflow.add_node("manage_state", node_handlers["manage_state"])
        workflow.add_node("call_model", node_handlers["call_model"])
        workflow.add_node("execute_tools", node_handlers["execute_tools"])

        # 设置入口点
        workflow.set_entry_point("manage_state")

        # 定义边的连接
        workflow.add_edge("manage_state", "call_model")
        
        # 添加条件边
        workflow.add_conditional_edges(
            "call_model",          # 源节点
            should_continue,       # 判断函数
            {
                "execute_tools": "execute_tools", # 如果判断为 'execute_tools', 则去 execute_tools 节点
                "__end__": END               # 如果判断为 '__end__', 则结束
            }
        )

        # 添加循环边
        workflow.add_edge("execute_tools", "call_model")

        logger.info("✓ V9 graph built successfully.")
        # 编译图
        compiled_graph = workflow.compile()
        logger.info("✓ V9 graph compiled successfully.")
        return compiled_graph
