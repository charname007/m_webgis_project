
import logging
import uuid
import json
from typing import Optional, Dict

from langchain_core.messages import HumanMessage, ToolMessage
from .llm import BaseLLM
from .tools_v13 import execute_sql_tool, web_search_tool # 使用V13的工具集
from .prompts_v13 import PromptManagerV13
from .optimized_memory_manager import OptimizedMemoryManager
from .graph.builder_v12 import GraphBuilderV12 # 复用V12的图结构
from .schemas_v12 import AgentStateV12 # 复用V12的Schema
from .database import DatabaseConnector

logger = logging.getLogger(__name__)

class SQLQueryAgentV13:
    """
    知识增强型Agent (V13)，支持数据库查询和网络搜索。
    """

    def __init__(self, temperature: Optional[float] = None):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV13 (Know-it-all)...")

        db_connector = DatabaseConnector()
        try:
            schema_str = db_connector.get_schema()
        finally:
            db_connector.close()
        
        self.llm = BaseLLM(temperature=temperature)
        # 绑定两种工具
        self.llm.bind_tools([execute_sql_tool, web_search_tool])
        self.memory_manager = OptimizedMemoryManager()
        self.base_prompt = PromptManagerV13.get_prompt(schema_str)

        node_handlers = {
            "manage_state": self._manage_state,
            "call_model_and_execute": self._call_model_and_execute,
            "reflect": self._reflect,
        }
        self.graph = GraphBuilderV12.build(node_handlers)

    # manage_state 和 run 方法与 V12 相同
    def _manage_state(self, state: AgentStateV12) -> Dict:
        # ... 此节点逻辑与 V12 完全相同 ...
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
            state["is_finished"] = True
            state["final_answer"] = response.content
            return state

        # V13核心逻辑：智能工具分发
        tool_call = response.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        self.logger.info(f"Executing tool: {tool_name} with args {tool_args}")
        
        if tool_name == "execute_sql_tool":
            output = execute_sql_tool(**tool_args)
        elif tool_name == "web_search_tool":
            output = web_search_tool(**tool_args)
        else:
            output = {"status": "error", "message": f"Unknown tool: {tool_name}"}

        state["session_history"].append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))
        state["intermediate_steps"].append({"tool_call": tool_call, "tool_output": output})
        return state

    def _reflect(self, state: AgentStateV12) -> Dict:
        # ... 此节点逻辑与 V12 完全相同 ...
        self.logger.info("Node: reflect")
        last_step = state["intermediate_steps"][-1]
        if "error" in last_step["tool_output"]:
            state["is_finished"] = True 
            state["final_answer"] = f"I encountered an error: {last_step['tool_output']['error']}"
        elif len(state["intermediate_steps"]) >= 1: 
            state["is_finished"] = True
            final_thought = "I have gathered the necessary information. Now I will formulate the final answer."
            state["session_history"].append(HumanMessage(content=final_thought))
            final_response = self.llm.invoke(state["session_history"])
            state["final_answer"] = final_response.content
        return state

    def run(self, query: str, conversation_id: Optional[str] = None) -> Dict:
        # ... 此方法与 V12 完全相同 ...
        if not conversation_id:
            conversation_id = f"session_{uuid.uuid4().hex[:8]}"

        initial_state = {"query": query, "conversation_id": conversation_id}

        final_state = self.graph.invoke(initial_state)
        
        result = {
            "final_answer": final_state.get("final_answer", "No final answer generated."),
            "conversation_id": conversation_id,
            "intermediate_steps": final_state.get("intermediate_steps", [])
        }
        self.memory_manager.add_query_to_session(query=query, result=result, sql="N/A", success=True)
        return result
