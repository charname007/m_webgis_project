
import logging
import uuid
import json
from typing import Optional, Dict

from langchain_core.messages import HumanMessage, ToolMessage
from .llm import BaseLLM
from .tools_v7 import execute_sql_tool, get_database_schema
from .prompts_v9 import PromptManagerV9
from .optimized_memory_manager import OptimizedMemoryManager
from .graph.builder_v10 import GraphBuilderV10
from .schemas_v10 import AgentStateV10

logger = logging.getLogger(__name__)

class SQLQueryAgentV10:
    """
    终极版Agent (V10)，融合了状态管理、高效工具调用和V1兼容的输出格式。
    """

    def __init__(self, system_prompt: Optional[str] = None, temperature: Optional[float] = None):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV10 (Final Version)...")

        self.llm = BaseLLM(temperature=temperature)
        self.llm.bind_tools([execute_sql_tool, get_database_schema])
        self.memory_manager = OptimizedMemoryManager()
        self.base_prompt = system_prompt or PromptManagerV9.get_prompt()

        node_handlers = {
            "manage_state": self._manage_state,
            "call_model": self._call_model,
            "execute_tools": self._execute_tools,
        }
        self.graph = GraphBuilderV10.build(node_handlers)

    # --- Node Handlers ---
    def _manage_state(self, state: AgentStateV10) -> Dict:
        self.logger.info(f"Node: manage_state for conversation {state['conversation_id']}")
        memory_data = self.memory_manager.start_session(state['conversation_id'])
        session_history = memory_data.get("session_history", [])
        state["session_history"] = session_history + [HumanMessage(content=state['query'])]
        return state

    def _call_model(self, state: AgentStateV10) -> Dict:
        self.logger.info("Node: call_model")
        response = self.llm.invoke(state["session_history"])
        state["session_history"].append(response)
        state["llm_response"] = response
        return state

    def _execute_tools(self, state: AgentStateV10) -> Dict:
        self.logger.info("Node: execute_tools")
        llm_response = state["llm_response"]
        if not llm_response or not llm_response.tool_calls:
            return state

        for tool_call in llm_response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            self.logger.info(f"Executing tool: {tool_name} with args {tool_args}")

            if tool_name == "execute_sql_tool":
                output = execute_sql_tool(**tool_args)
                # V10核心逻辑：填充状态字段
                state["sql"] = tool_args.get('sql') # 记录SQL
                if output.get('status') == 'success':
                    state["data"] = output.get('data')
                    state["count"] = len(output.get('data', []))
                else:
                    state["error"] = output.get('message')
            elif tool_name == "get_database_schema":
                output = get_database_schema()
            else:
                output = {"status": "error", "message": f"Unknown tool: {tool_name}"}
            
            state["session_history"].append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))
        return state

    # --- Final Result Builder ---
    def _build_final_result(self, state: AgentStateV10) -> Dict:
        """将最终状态组装成与V1兼容的字典。"""
        # 尝试从最终的LLM响应中解析澄清问题
        final_llm_response_content = state.get("llm_response", {}).content
        try:
            if isinstance(final_llm_response_content, str):
                potential_json = json.loads(final_llm_response_content)
                if isinstance(potential_json, dict) and potential_json.get('action') == 'clarify':
                    return potential_json # 如果是澄清，直接返回
        except (json.JSONDecodeError, TypeError):
            pass # 正常流程
        
        return {
            "status": state.get("status", "error"),
            "answer": state.get("final_answer", ""),
            "data": state.get("data"),
            "count": state.get("count", 0),
            "sql": state.get("sql"),
            "message": state.get("message", "查询失败"),
        }

    # --- Main Runner ---
    def run(self, query: str, conversation_id: Optional[str] = None) -> Dict:
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

        # 启动图执行
        final_state = self.graph.invoke(initial_state)

        # 构建并返回V1兼容的结果
        result = self._build_final_result(final_state)

        # 保存记忆
        self.memory_manager.add_query_to_session(query=query, result=result, sql=result.get("sql"), success=result.get("status")=="success")

        return result
