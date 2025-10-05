"""
核心模块 - Sight Server
提供Agent、LLM、数据库连接、提示词管理等组件
支持Memory和Checkpoint功能
"""

# LLM 相关
from .llm import BaseLLM
from .database import DatabaseConnector
from .prompts import PromptManager, PromptType, QueryIntentType

# 数据模型
from .schemas import QueryResult, AgentState, ThoughtChainStep, SQLQueryRecord

# 处理器组件
from .processors import SQLGenerator, SQLExecutor, ResultParser, AnswerGenerator

# LangGraph 组件
from .graph import (
    AgentNodes,
    LegacyAgentNodes,
    GraphBuilder,
    build_legacy_nodes,
    build_node_mapping,
    should_continue_querying,
)

# Memory 和 Checkpoint
from .memory import MemoryManager
from .checkpoint import CheckpointManager

# 主 Agent
from .agent import SQLQueryAgent

__all__ = [
    # LLM 相关
    "BaseLLM",
    "DatabaseConnector",
    "PromptManager",
    "PromptType",
    "QueryIntentType",

    # 数据模型
    "QueryResult",
    "AgentState",
    "ThoughtChainStep",
    "SQLQueryRecord",

    # 处理器组件
    "SQLGenerator",
    "SQLExecutor",
    "ResultParser",
    "AnswerGenerator",

    # LangGraph 组件
    "AgentNodes",
    "LegacyAgentNodes",
    "GraphBuilder",
    "build_legacy_nodes",
    "build_node_mapping",
    "should_continue_querying",

    # Memory 和 Checkpoint
    "MemoryManager",
    "CheckpointManager",

    # 主 Agent
    "SQLQueryAgent",
]
