
from typing import TypedDict, List, Optional, Any
from langchain_core.messages import BaseMessage

class AgentStateV9(TypedDict):
    """
    V9版本的状态定义，融合了历史记录和工具调用。
    """
    # 输入字段
    query: str                   # 当前轮次用户的原始查询
    conversation_id: str         # 整个对话的唯一ID

    # 状态管理字段
    session_history: List[BaseMessage] # 从MemoryManager加载的对话历史
    contextual_prompt: str             # 结合了历史和当前查询，真正喂给LLM的提示

    # LLM交互字段
    llm_response: Optional[BaseMessage] # LLM的直接响应（可能包含工具调用）
    
    # 工具执行结果
    tool_outputs: List[Dict[str, Any]] # 存储工具执行的结果

    # 输出字段
    final_answer: str            # 最终生成的、面向用户的自然语言答案
    
    # 错误处理
    error: Optional[str]         # 记录错误信息

