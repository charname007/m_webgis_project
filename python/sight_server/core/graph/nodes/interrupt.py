"""
Interrupt节点模块 - Sight Server
用于在查询不明确时中断工作流并请求新的查询
"""

from typing import Dict
from langgraph.types import interrupt, Command

from ...schemas import AgentState
from .base import NodeBase
from .memory_decorators import with_memory_tracking


class InterruptCheckNode(NodeBase):
    """
    Interrupt检查节点

    功能:
    - 当查询不明确时，使用LangGraph interrupt功能暂停工作流
    - 向用户请求更清晰的查询表述
    - 获取新的查询后重新执行工作流
    """

    @with_memory_tracking("interrupt_check")
    def __call__(self, state: AgentState) -> Dict[str, object]:
        """
        处理interrupt逻辑

        Args:
            state: Agent状态

        Returns:
            包含interrupt状态的字典
        """
        # try:
        query = state["query"]
        intent_info = state.get("intent_info", {})

        self.logger.info(
             f"[Node: interrupt_check] Processing interrupt for query: {query}"
             )

         # 获取query明确性信息
        is_query_clear = intent_info.get("is_query_clear", True)
        clarity_reason = intent_info.get("reasoning", "")

        if not is_query_clear:
                # 查询不明确，使用LangGraph interrupt功能
                self.logger.warning(
                    f"[Node: interrupt_check] Query is unclear, requesting clarification: {query}"
                )

                # 使用interrupt功能暂停工作流，等待用户输入新的查询
                new_query = interrupt(
                    {
                        'status': 'interrupt',
                        "reason": "query_not_clear",
                        "original_query": query,
                        "message": "您的查询不够明确，请提供更具体的信息",
                        "suggestion": "请说明：1) 地点（如城市、省份）2) 查询类型（如统计、列表）3) 具体条件（如景区等级、时间范围）",
                        "clarity_reason": clarity_reason
                    }
                )

                thought_step = {
                    "step": state.get("current_step", 0) + 1,
                    "type": "interrupt_check",
                    "action": "request_query_clarification",
                    "input": query,
                    "output": {
                        "status": "waiting_for_clarification",
                        "new_query": new_query,
                        "reason": "query_not_clear"
                    },
                    "status": "completed"
                }

                return {
                    "query": new_query,  # 使用新的查询替换原始查询
                    "interrupt_info": {
                        "interrupted": True,
                        "reason": "query_clarified",
                        "original_query": query,
                        "new_query": new_query
                    },
                    "should_continue": True,  # 继续执行，但是用新查询
                    "thought_chain": [thought_step],
                    "message": f"原始查询已更新: '{new_query}'"
                }
        else:
                # 查询明确，正常继续
                self.logger.info(
                    f"[Node: interrupt_check] Query is clear, continuing: {query}"
                )

                thought_step = {
                    "step": state.get("current_step", 0) + 1,
                    "type": "interrupt_check",
                    "action": "query_clear_continue",
                    "input": query,
                    "output": {"query_clear": True},
                    "status": "completed"
                }

                return {
                    "interrupt_info": {"interrupted": False, "reason": "query_clear"},
                    "should_continue": True,
                    "thought_chain": [thought_step]
                }

        # except Exception as exc:
            # self.logger.error(
            #     f"[Node: interrupt_check] Error: {exc}", exc_info=True)

            # # 出错时记录并继续执行，避免阻塞
            # return {
            #     "interrupt_info": {
            #         "interrupted": False,
            #         "reason": "error_in_interrupt_check",
            #         "message": f"Interrupt检查出错: {str(exc)}"
            #     },
            #     "should_continue": True,
            #     "thought_chain": [
            #         {
            #             "step": state.get("current_step", 0) + 1,
            #             "type": "interrupt_check",
            #             "action": "continue_due_to_error",
            #             "error": str(exc),
            #             "status": "failed"
            #         }
            #     ]
            # }
