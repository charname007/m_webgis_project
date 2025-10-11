
from typing import TypedDict, List, Optional, Any, Dict
from langchain_core.messages import BaseMessage

class AgentStateV12(TypedDict):
    """
    V12版本的状态定义，增加了支持多步推理和反思的字段。
    """
    # 继承自V10的核心字段
    query: str
    conversation_id: str
    session_history: List[BaseMessage]
    llm_response: Optional[BaseMessage]
    status: str
    final_answer: str
    data: Optional[List[Dict]]
    count: int
    sql: Optional[str]
    message: str
    error: Optional[str]
    
    # V12 新增字段
    intermediate_steps: List[Dict[str, Any]] # 记录每一步的思考和工具调用结果
    is_finished: bool # 标记整个复杂问题是否已解决
