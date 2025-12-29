"""
LangGraph ContextSchema 定义模块 - Sight Server
定义运行时配置的 ContextSchema 类，用于 LangGraph v0.6+ 版本
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AgentContextSchema:
    """
    LangGraph 代理工作流的运行时上下文配置
    
    用于 LangGraph v0.6+ 版本，替代旧的 config['configurable'] 模式
    """
    thread_id: str = "default"
    # 注意：checkpointer 不应该在这里定义，它是在 compile() 时设置的


@dataclass
class LLMContextSchema:
    """
    LLM 链的运行时上下文配置
    
    用于 LangChain 链的运行时配置
    """
    session_id: str = "default"


@dataclass
class SpatialQueryContextSchema:
    """
    空间查询工作流的运行时上下文配置
    
    用于处理地理空间查询的特殊配置
    """
    thread_id: str = "default"
    spatial_analysis_level: str = "basic"  # basic, intermediate, advanced
    coordinate_system: str = "WGS84"  # WGS84, UTM, etc.


@dataclass
class ConversationContextSchema:
    """
    对话管理工作流的运行时上下文配置
    
    用于管理多轮对话的上下文
    """
    thread_id: str = "default"
    user_id: Optional[str] = None
    conversation_type: str = "general"  # general, spatial, analysis, etc.