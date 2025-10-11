
import logging
import uuid
import json
from typing import Optional, Dict

from langchain_core.messages import HumanMessage, ToolMessage, AIMessage

from .llm import BaseLLM
from .tools_v14 import execute_sql_tool, web_search_tool, generate_visualization_config
from .prompts_v14 import PromptManagerV14
from .db_memory_manager import DbMemoryManager # 使用新的DB Memory Manager
from .db_checkpoint_manager import DbCheckpointManager # 使用新的DB Checkpoint Manager
from .graph.builder_v12 import GraphBuilderV12 # 复用V12的图结构
from .schemas_v12 import AgentStateV12 # 复用V12的Schema
from .database import DatabaseConnector

logger = logging.getLogger(__name__)

class SQLQueryAgentV15:
    """
    终极持久化Agent (V15)，记忆和存档都存储在数据库中。
    """

    def __init__(self, temperature: Optional[float] = None):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV15 (The Persistent)...")

        db_connector = DatabaseConnector()
        try:
            schema_str = db_connector.get_schema()
        finally:
            db_connector.close()
        
        self.llm = BaseLLM(temperature=temperature)
        self.llm.bind_tools([execute_sql_tool, web_search_tool, generate_visualization_config])
        
        # 初始化基于DB的管理器
        self.memory_manager = DbMemoryManager()
        self.checkpoint_manager = DbCheckpointManager()
        
        self.base_prompt = PromptManagerV14.get_prompt(schema_str)

        node_handlers = {
            "manage_state": self._manage_state,
            "call_model_and_execute": self._call_model_and_execute,
            "reflect": self._reflect,
        }
        self.graph = GraphBuilderV12.build(node_handlers)

    def _manage_state(self, state: AgentStateV12) -> Dict:
        self.logger.info(f"Node: manage_state for conversation {state['conversation_id']}")
        latest_checkpoint = self.checkpoint_manager.get_latest_checkpoint(state['conversation_id'])
        
        if latest_checkpoint:
            self.logger.info("Resuming from latest checkpoint in DB.")
            # 这里需要反序列化消息
            history_dicts = latest_checkpoint['state_snapshot']['session_history']
            # A simplified deserialization. A real one would use a classmap.
            history = [AIMessage(**msg) if msg.get('type')=='ai' else HumanMessage(**msg) for msg in history_dicts]
            state["session_history"] = history + [HumanMessage(content=state['query'])]
        else:
            state["session_history"] = [HumanMessage(content=self.base_prompt), HumanMessage(content=state['query'])]
        
        state["is_finished"] = False
        state["intermediate_steps"] = []
        return state

    # _call_model_and_execute 和 _reflect 与 V14 逻辑保持一致
    def _call_model_and_execute(self, state: AgentStateV12) -> Dict:
        # ... (与 V14 逻辑相同) ...
        self.logger.info("Node: call_model_and_execute")
        response = self.llm.invoke(state["session_history"])
        state["session_history"].append(response)
        if not response.tool_calls:
            state["is_finished"] = True
            state["final_answer"] = response.content
            return state
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            if tool_name == "execute_sql_tool": output = execute_sql_tool(**tool_call["args"])
            elif tool_name == "web_search_tool": output = web_search_tool(**tool_call["args"])
            elif tool_name == "generate_visualization_config": output = generate_visualization_config(data=state["intermediate_steps"][-1]["tool_output"].get("data"))
            else: output = {"status": "error", "message": f"Unknown tool: {tool_name}"}
            state["session_history"].append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))
            state["intermediate_steps"].append({"tool_call": tool_call, "tool_output": output})
        return state

    def _reflect(self, state: AgentStateV12) -> Dict:
        # ... (与 V14 逻辑相同) ...
        self.logger.info("Node: reflect")
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
        
        # 组装最终结果 (与V14类似)
        final_answer = final_state.get("final_answer", "Error.")
        visualization_config = next((s["tool_output"].get("config") for s in final_state.get("intermediate_steps", []) if s["tool_call"]["name"] == "generate_visualization_config"), None)
        sql_query = next((s["tool_call"]["args"].get("sql") for s in final_state.get("intermediate_steps", []) if s["tool_call"]["name"] == "execute_sql_tool"), None)

        result = {
            "answer": final_answer,
            "visualization": visualization_config,
            "sql": sql_query,
            "conversation_id": conversation_id
        }

        # 持久化
        self.checkpoint_manager.save_checkpoint(final_state)
        self.memory_manager.learn_from_query(query=query, sql=sql_query, result=result, success=True)

        return result
