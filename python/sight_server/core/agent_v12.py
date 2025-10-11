
import logging
import uuid
import json
from typing import Optional, Dict

from langchain_core.messages import HumanMessage, ToolMessage, AIMessage

from .llm import BaseLLM
from .tools_v11 import execute_sql_tool
from .prompts_v12 import PromptManagerV12
from .optimized_memory_manager import OptimizedMemoryManager
from .graph.builder_v12 import GraphBuilderV12
from .schemas_v12 import AgentStateV12
from .database import DatabaseConnector

logger = logging.getLogger(__name__)

class SQLQueryAgentV12:
    """
    分析师Agent (V12)，支持多步推理。
    """

    def __init__(self, temperature: Optional[float] = None):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV12 (Analyst)...")

        db_connector = DatabaseConnector()
        try:
            schema_str = db_connector.get_schema()
        finally:
            db_connector.close()
        
        self.llm = BaseLLM(temperature=temperature)
        self.llm.bind_tools([execute_sql_tool])
        self.memory_manager = OptimizedMemoryManager()
        self.base_prompt = PromptManagerV12.get_prompt(schema_str)

        node_handlers = {
            "manage_state": self._manage_state,
            "call_model_and_execute": self._call_model_and_execute,
            "reflect": self._reflect,
        }
        self.graph = GraphBuilderV12.build(node_handlers)

    def _manage_state(self, state: AgentStateV12) -> Dict:
        self.logger.info(f"Node: manage_state for conversation {state['conversation_id']}")
        memory_data = self.memory_manager.start_session(state['conversation_id'])
        history = memory_data.get("session_history", [])
        state["session_history"] = [HumanMessage(content=self.base_prompt), HumanMessage(content=state['query'])] + history
        state["is_finished"] = False
        state["intermediate_steps"] = []
        return state

    def _call_model_and_execute(self, state: AgentStateV12) -> Dict:
        self.logger.info("Node: call_model_and_execute")
        response = self.llm.invoke(state["session_history"])
        state["session_history"].append(response)

        if not response.tool_calls:
            self.logger.info("No tool calls from LLM, finishing.")
            state["is_finished"] = True
            state["final_answer"] = response.content
            return state

        tool_call = response.tool_calls[0]
        output = execute_sql_tool(**tool_call["args"])
        state["session_history"].append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))
        state["intermediate_steps"].append({"tool_call": tool_call, "tool_output": output})
        return state

    def _reflect(self, state: AgentStateV12) -> Dict:
        self.logger.info("Node: reflect")
        # 在这里，我们让LLM审视历史记录（包括最新的工具结果）并决定下一步
        reflection_prompt = "Based on the conversation history and the last tool output, have you fully answered the original question? If yes, provide the final answer. If not, state your next thought and continue."
        state["session_history"].append(HumanMessage(content=reflection_prompt))
        
        # 不直接调用LLM，而是让下一个循环的_call_model_and_execute来做
        # 这简化了逻辑，让模型在同一步骤中做决策和执行
        # 我们只需要准备好让它进行反思的提示即可

        # 检查是否应该结束
        # 这是一个简化的逻辑，真实的场景可能需要LLM来判断
        last_step = state["intermediate_steps"][-1]
        if "error" in last_step["tool_output"]:
             # 如果有错误，假设无法继续
            state["is_finished"] = True 
            state["final_answer"] = f"I encountered an error and cannot continue: {last_step['tool_output']['error']}"

        # 在这个简化版中，我们假设执行一步就结束
        # 在一个完整的实现中，会有一个更复杂的逻辑来决定是否 is_finished
        elif len(state["intermediate_steps"]) >= 1: 
            state["is_finished"] = True
            final_thought = "I have executed the query and a final answer should be formulated."
            state["session_history"].append(HumanMessage(content=final_thought))
            final_response = self.llm.invoke(state["session_history"])
            state["final_answer"] = final_response.content

        return state

    def run(self, query: str, conversation_id: Optional[str] = None) -> Dict:
        if not conversation_id:
            conversation_id = f"session_{uuid.uuid4().hex[:8]}"

        initial_state = {
            "query": query,
            "conversation_id": conversation_id,
        }

        final_state = self.graph.invoke(initial_state)
        
        result = {
            "final_answer": final_state.get("final_answer", "No final answer generated."),
            "conversation_id": conversation_id,
            "intermediate_steps": final_state.get("intermediate_steps", [])
        }
        self.memory_manager.add_query_to_session(query=query, result=result, sql="N/A", success=True)
        return result
