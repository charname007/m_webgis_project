
import logging
import uuid
import json
from typing import Optional, Dict

from langchain_core.messages import HumanMessage, ToolMessage
from .llm import BaseLLM
from .tools_v11 import execute_sql_tool # 使用 V11 的精简工具集
from .prompts_v11 import PromptManagerV11
from .optimized_memory_manager import OptimizedMemoryManager
from .graph.builder_v10 import GraphBuilderV10 # 复用V10的图结构
from .schemas_v10 import AgentStateV10 # 复用V10的Schema
from .database import DatabaseConnector # 直接用于获取Schema

logger = logging.getLogger(__name__)

class SQLQueryAgentV11:
    """
    终极版Agent (V11)，将Schema作为先天知识注入。
    """

    def __init__(self, temperature: Optional[float] = None):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV11 (Schema as Innate Knowledge)...")

        # 1. 启动时获取Schema
        db_connector = DatabaseConnector()
        try:
            schema_str = db_connector.get_schema() 
            self.logger.info("✓ Database schema loaded at startup.")
        except Exception as e:
            self.logger.error(f"FATAL: Could not load database schema at startup: {e}", exc_info=True)
            schema_str = "Error: Could not load schema."
        finally:
            db_connector.close()

        # 2. 初始化核心组件
        self.llm = BaseLLM(temperature=temperature)
        self.llm.bind_tools([execute_sql_tool]) # 只绑定一个工具
        self.memory_manager = OptimizedMemoryManager()
        # 将获取到的 schema 注入提示
        self.base_prompt = PromptManagerV11.get_prompt(schema_str)

        # 3. 定义节点处理函数 (与V10基本相同)
        node_handlers = {
            "manage_state": self._manage_state,
            "call_model": self._call_model,
            "execute_tools": self._execute_tools,
        }

        # 4. 构建并编译图 (复用V10的结构)
        self.graph = GraphBuilderV10.build(node_handlers)

    def _manage_state(self, state: AgentStateV10) -> Dict:
        self.logger.info(f"Node: manage_state for conversation {state['conversation_id']}")
        memory_data = self.memory_manager.start_session(state['conversation_id'])
        session_history = memory_data.get("session_history", [])
        # 将格式化的基础提示和当前问题加入历史
        state["session_history"] = [HumanMessage(content=self.base_prompt), HumanMessage(content=state['query'])] + session_history
        return state

    def _call_model(self, state: AgentStateV10) -> Dict:
        # ... 此节点逻辑与 V10 完全相同 ...
        self.logger.info("Node: call_model")
        response = self.llm.invoke(state["session_history"])
        state["session_history"].append(response)
        state["llm_response"] = response
        return state

    def _execute_tools(self, state: AgentStateV10) -> Dict:
        # ... 此节点逻辑与 V10 基本相同，但更简单，因为只用处理一个工具 ...
        self.logger.info("Node: execute_tools")
        llm_response = state["llm_response"]
        if not llm_response or not llm_response.tool_calls:
            return state
        
        tool_call = llm_response.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        self.logger.info(f"Executing tool: {tool_name} with args {tool_args}")

        if tool_name == "execute_sql_tool":
            output = execute_sql_tool(**tool_args)
            state["sql"] = tool_args.get('sql')
            if output.get('status') == 'success':
                state["data"] = output.get('data')
                state["count"] = len(output.get('data', []))
            else:
                state["error"] = output.get('message')
        else:
            output = {"status": "error", "message": f"Unknown tool: {tool_name}"}
        
        state["session_history"].append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))
        return state

    def _build_final_result(self, state: AgentStateV10) -> Dict:
        # ... 此方法与 V10完全相同 ...
        final_llm_response_content = state.get("llm_response", {}).content
        try:
            if isinstance(final_llm_response_content, str):
                potential_json = json.loads(final_llm_response_content)
                if isinstance(potential_json, dict) and potential_json.get('action') == 'clarify':
                    return potential_json
        except (json.JSONDecodeError, TypeError):
            pass
        
        return {
            "status": state.get("status", "error"),
            "answer": state.get("final_answer", ""),
            "data": state.get("data"),
            "count": state.get("count", 0),
            "sql": state.get("sql"),
            "message": state.get("message", "查询失败"),
        }

    def run(self, query: str, conversation_id: Optional[str] = None) -> Dict:
        # ... 此方法与 V10 完全相同 ...
        if not conversation_id:
            conversation_id = f"session_{uuid.uuid4().hex[:8]}"
            self.logger.info(f"New conversation started: {conversation_id}")

        initial_state: AgentStateV10 = {
            "query": query,
            "conversation_id": conversation_id,
            "session_history": [],
            "llm_response": None,
            "status": "pending",
            "final_answer": "",
            "data": None,
            "count": 0,
            "sql": None,
            "message": "",
            "error": None
        }

        final_state = self.graph.invoke(initial_state)
        result = self._build_final_result(final_state)
        self.memory_manager.add_query_to_session(query=query, result=result, sql=result.get("sql"), success=result.get("status")=="success")
        return result
