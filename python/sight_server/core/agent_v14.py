
import logging
import uuid
import json
from typing import Optional, Dict

from langchain_core.messages import HumanMessage, ToolMessage
from .llm import BaseLLM
from .tools_v14 import execute_sql_tool, web_search_tool, generate_visualization_config
from .prompts_v14 import PromptManagerV14
from .optimized_memory_manager import OptimizedMemoryManager
from .graph.builder_v12 import GraphBuilderV12 # 依旧可以复用V12的图结构
from .schemas_v12 import AgentStateV12 # 复用V12的Schema
from .database import DatabaseConnector

logger = logging.getLogger(__name__)

class SQLQueryAgentV14:
    """
    艺术家Agent (V14)，支持数据可视化。
    """

    def __init__(self, temperature: Optional[float] = None):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV14 (The Visualizer)...")

        db_connector = DatabaseConnector()
        try:
            schema_str = db_connector.get_schema()
        finally:
            db_connector.close()
        
        self.llm = BaseLLM(temperature=temperature)
        # 绑定所有三个工具
        self.llm.bind_tools([execute_sql_tool, web_search_tool, generate_visualization_config])
        self.memory_manager = OptimizedMemoryManager()
        self.base_prompt = PromptManagerV14.get_prompt(schema_str)

        node_handlers = {
            "manage_state": self._manage_state,
            "call_model_and_execute": self._call_model_and_execute,
            "reflect": self._reflect,
        }
        self.graph = GraphBuilderV12.build(node_handlers)

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

        # V14核心逻辑：处理多个可能的工具调用
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            self.logger.info(f"Executing tool: {tool_name} with args {tool_args}")
            
            if tool_name == "execute_sql_tool":
                output = execute_sql_tool(**tool_args)
            elif tool_name == "web_search_tool":
                output = web_search_tool(**tool_args)
            elif tool_name == "generate_visualization_config":
                # 这个工具的输入是上一步骤的数据
                last_step_data = state["intermediate_steps"][-1]["tool_output"].get("data")
                output = generate_visualization_config(data=last_step_data)
            else:
                output = {"status": "error", "message": f"Unknown tool: {tool_name}"}

            state["session_history"].append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))
            state["intermediate_steps"].append({"tool_call": tool_call, "tool_output": output})
        
        return state

    def _reflect(self, state: AgentStateV12) -> Dict:
        # ... 此节点逻辑与 V12 类似，但更关注于最后的 finish 条件 ...
        self.logger.info("Node: reflect")
        
        # V14 的简化逻辑：只要LLM在最后一次调用没产生新工具，就认为结束
        # 真实的场景会让LLM在prompt的指导下自主决定是否finish
        last_response = state["session_history"][-1]
        if not isinstance(last_response, AIMessage) or not last_response.tool_calls:
            state["is_finished"] = True
            state["final_answer"] = last_response.content
        
        return state

    def run(self, query: str, conversation_id: Optional[str] = None) -> Dict:
        if not conversation_id:
            conversation_id = f"session_{uuid.uuid4().hex[:8]}"

        initial_state = {"query": query, "conversation_id": conversation_id}
        final_state = self.graph.invoke(initial_state)
        
        # V14 最终结果组装
        final_answer = final_state.get("final_answer", "No final answer generated.")
        visualization_config = None
        for step in final_state.get("intermediate_steps", []):
            if step["tool_call"]["name"] == "generate_visualization_config":
                visualization_config = step["tool_output"].get("config")
                break

        result = {
            "answer": final_answer,
            "visualization": visualization_config,
            "conversation_id": conversation_id,
        }
        self.memory_manager.add_query_to_session(query=query, result=result, sql="N/A", success=True)
        return result
