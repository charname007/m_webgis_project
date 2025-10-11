
import logging
import uuid
from typing import Optional, Dict

from langchain_core.messages import HumanMessage, ToolMessage, AIMessage

from .llm import BaseLLM
from .tools_v7 import execute_sql_tool, get_database_schema # 使用 v7 的安全工具
from .prompts_v9 import PromptManagerV9
from .optimized_memory_manager import OptimizedMemoryManager
from .graph.builder_v9 import GraphBuilderV9
from .schemas_v9 import AgentStateV9

logger = logging.getLogger(__name__)

class SQLQueryAgentV9:
    """
    终极版SQL查询Agent (V9)，融合了状态管理和高效工具调用。
    """

    def __init__(self, system_prompt: Optional[str] = None, temperature: Optional[float] = None):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV9 (Hybrid Stateful/Tool-Calling)...")

        # 1. 初始化核心组件
        self.llm = BaseLLM(temperature=temperature)
        self.llm.bind_tools([execute_sql_tool, get_database_schema])
        self.memory_manager = OptimizedMemoryManager()
        self.base_prompt = system_prompt or PromptManagerV9.get_prompt()

        # 2. 定义节点处理函数
        node_handlers = {
            "manage_state": self._manage_state,
            "call_model": self._call_model,
            "execute_tools": self._execute_tools,
        }

        # 3. 构建并编译图
        self.graph = GraphBuilderV9.build(node_handlers)

    def _manage_state(self, state: AgentStateV9) -> Dict:
        """节点1: 管理状态，加载历史记录，构建上下文提示。"""
        self.logger.info(f"Node: manage_state for conversation {state['conversation_id']}")
        memory_data = self.memory_manager.start_session(state['conversation_id'])
        session_history = memory_data.get("session_history", [])
        
        # 构建上下文提示
        contextual_prompt = self.base_prompt
        # 可以将 session_history 格式化后加入提示

        state["session_history"] = session_history
        state["contextual_prompt"] = contextual_prompt
        state["session_history"].append(HumanMessage(content=state['query']))
        return state

    def _call_model(self, state: AgentStateV9) -> Dict:
        """节点2: 调用LLM获取决策。"""
        self.logger.info("Node: call_model")
        messages = state["session_history"]
        response = self.llm.invoke(messages)
        state["llm_response"] = response
        state["session_history"].append(response)
        return state

    def _execute_tools(self, state: AgentStateV9) -> Dict:
        """节点3: 执行LLM决策的工具。"""
        self.logger.info("Node: execute_tools")
        llm_response = state["llm_response"]
        if not llm_response or not llm_response.tool_calls:
            return state # 没有工具调用，直接返回

        tool_outputs = []
        for tool_call in llm_response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            self.logger.info(f"Executing tool: {tool_name} with args {tool_args}")
            if tool_name == "execute_sql_tool":
                output = execute_sql_tool(**tool_args)
            elif tool_name == "get_database_schema":
                output = get_database_schema()
            else:
                output = {"status": "error", "message": f"Unknown tool: {tool_name}"}
            
            tool_outputs.append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))

        state["session_history"].extend(tool_outputs)
        return state

    def run(self, query: str, conversation_id: Optional[str] = None) -> Dict:
        """
        启动V9工作流。
        """
        if not conversation_id:
            conversation_id = f"session_{uuid.uuid4().hex[:8]}"
            self.logger.info(f"New conversation started: {conversation_id}")

        initial_state: AgentStateV9 = {
            "query": query,
            "conversation_id": conversation_id,
            # 其他字段会被节点填充
            "session_history": [],
            "contextual_prompt": "",
            "llm_response": None,
            "tool_outputs": [],
            "final_answer": "",
            "error": None
        }

        # 启动图执行
        final_state = self.graph.invoke(initial_state)

        # 提取最终答案并保存记忆
        final_answer = final_state.get("llm_response").content if final_state.get("llm_response") else "No answer generated."
        self.memory_manager.add_query_to_session(query=query, result=final_answer, sql="N/A in V9", success=True)

        return {"final_answer": final_answer, "conversation_id": conversation_id}

