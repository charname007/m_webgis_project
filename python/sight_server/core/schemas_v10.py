
from typing import TypedDict, List, Optional, Any, Dict
from langchain_core.messages import BaseMessage

class AgentStateV10(TypedDict):
    """
    V10版本的状态定义，增加了与V1兼容的输出字段。
    """
    # 输入字段
    query: str
    conversation_id: str

    # 状态管理字段
    session_history: List[BaseMessage]

    # LLM交互字段
    llm_response: Optional[BaseMessage]
    
    # V10 新增的、用于最终输出的字段
    status: str                  # 执行状态: 'success' or 'error'
    final_answer: str            # LLM 生成的自然语言总结 (对应 V1 的 answer)
    data: Optional[List[Dict]]   # SQL查询返回的结构化数据
    count: int                   # 数据条数
    sql: Optional[str]           # 执行的最终SQL语句
    message: str                 # 执行消息，如 '查询成功'
    error: Optional[str]
    
