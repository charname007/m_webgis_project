"""
数据模型模块 - Sight Server
定义Agent和LangGraph使用的数据结构
"""

from typing import TypedDict, Optional, List, Dict, Any
from typing_extensions import Annotated
from operator import add
from pydantic import BaseModel, Field
from enum import Enum


# ==================== Pydantic 输出模型 ====================

class IntentType(str, Enum):
    """查询意图类型枚举"""
    QUERY = "query"       # 用户需要具体数据列表
    SUMMARY = "summary"   # 用户需要统计汇总


class QueryIntentAnalysis(BaseModel):
    """LLM 查询意图分析结果（结构化输出）"""

    intent_type: IntentType = Field(
        description="查询意图类型：query=需要具体数据列表，summary=需要统计汇总结果"
    )

    is_spatial: bool = Field(
        description="是否涉及空间查询（距离、附近、周边等空间概念）"
    )

    confidence: float = Field(
        ge=0.0, le=1.0,
        description="分析置信度（0-1之间的浮点数）"
    )

    reasoning: str = Field(
        description="分析推理过程的详细说明"
    )

    keywords_matched: List[str] = Field(
        default_factory=list,
        description="识别到的关键词列表"
    )


class QueryResult(BaseModel):
    """SQL查询结果的标准输出格式"""
    status: str = Field(
        description="查询状态: success（成功）或 error（失败）"
    )
    answer: str = Field(
        default="",
        description="Agent 生成的自然语言回答"
    )
    data: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="查询结果数据，JSON数组格式，来自 json_agg 的结果"
    )
    count: int = Field(
        default=0,
        description="结果数量"
    )
    message: str = Field(
        default="",
        description="查询说明信息或错误信息"
    )
    sql: Optional[str] = Field(
        default=None,
        description="执行的SQL语句（可选）"
    )
    intent_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="查询意图分析信息，包含 intent_type, is_spatial, keywords_matched 等"
    )


# ==================== LangGraph 状态模型 ====================

class AgentState(TypedDict):
    """
    LangGraph Agent 状态定义

    支持多步迭代查询：
    - 使用 Annotated[List, add] 累积查询历史
    - 记录每一步的 SQL 和执行结果
    - 支持条件循环直到获取完整数据
    - 支持 Memory 和 Checkpoint 机制
    """

    # ==================== 输入查询 ====================
    query: str  # 原始用户查询
    enhanced_query: str  # 增强后的查询（添加空间提示等）
    query_intent: Optional[str]  # 查询意图类型 (query/summary)
    requires_spatial: bool  # 是否需要空间查询
    intent_info: Optional[Dict[str, Any]]  # 完整的查询意图分析信息

    # ==================== 数据库Schema ====================
    database_schema: Optional[Dict[str, Any]]  # 数据库schema信息（表结构、字段等）
    schema_fetched: bool  # schema是否已获取

    # ==================== 多步查询累积 ====================
    # 使用 Annotated[List, add] 实现历史累加
    sql_history: Annotated[List[str], add]  # 所有执行过的 SQL
    execution_results: Annotated[List[Dict[str, Any]], add]  # 所有执行结果
    thought_chain: Annotated[List[Dict[str, Any]], add]  # 思维链步骤

    # ==================== 当前步骤状态 ====================
    current_step: int  # 当前迭代步数（从0开始）
    current_sql: Optional[str]  # 当前步骤生成的 SQL
    current_result: Optional[Dict[str, Any]]  # 当前步骤的执行结果

    # ==================== 控制流程 ====================
    should_continue: bool  # 是否继续查询（用于条件边判断）
    max_iterations: int  # 最大迭代次数（默认10）
    error: Optional[str]  # 错误信息（如果有）

    # ==================== Fallback 重试机制 ====================
    retry_count: int  # 当前错误的重试次数（默认0）
    max_retries: int  # 最大重试次数（默认3）
    last_error: Optional[str]  # 最后一次错误信息
    error_history: Annotated[List[Dict[str, Any]], add]  # 错误历史记录
    fallback_strategy: Optional[str]  # 回退策略: retry_sql/simplify_query/retry_execution/fail
    error_type: Optional[str]  # 错误类型分类

    # ✅ 增强错误上下文（新增字段）
    error_context: Optional[Dict[str, Any]]  # 完整错误上下文信息
    """
    错误上下文结构（用于精准SQL修复）：
    {
        "failed_sql": str,              # 出错的SQL语句
        "error_message": str,           # 完整错误信息
        "error_code": str,              # PostgreSQL错误码（如 "42P01"）
        "error_position": int,          # 错误位置（字符偏移）
        "failed_at_step": int,          # 出错步骤
        "query_context": {...},         # 查询上下文（query, intent等）
        "database_context": {...},      # 数据库上下文（schema, tables等）
        "execution_context": {...}      # 执行上下文（耗时, 时间戳等）
    }
    """

    # ==================== 日志追踪（新增字段）====================
    query_id: str  # ✅ 唯一查询ID（UUID，用于日志追踪）
    query_start_time: str  # ✅ 查询开始时间（ISO格式）
    node_execution_logs: Annotated[List[Dict[str, Any]], add]  # ✅ 节点执行日志

    # ==================== Memory 机制 ====================
    # 短期记忆：当前会话的查询历史
    session_history: Annotated[List[Dict[str, Any]], add]  # 会话历史
    conversation_id: Optional[str]  # 会话ID（用于关联多轮对话）
    
    # ✅ 新增：对话总结机制
    conversation_summary: str  # 对话历史总结
    summary_trigger_count: int  # 触发总结的消息数量阈值
    last_summary_step: int  # 上次总结的步骤数

    # 长期记忆：跨会话的知识积累
    knowledge_base: Optional[Dict[str, Any]]  # 知识库（常见查询模式、优化建议等）
    learned_patterns: Annotated[List[Dict[str, Any]], add]  # 学习到的查询模式

    # ==================== Checkpoint 机制 ====================
    # 注意: checkpoint_id 是 LangGraph 的保留字段，使用 saved_checkpoint_id 代替
    saved_checkpoint_id: Optional[str]  # 已保存的Checkpoint标识符
    saved_checkpoint_step: Optional[int]  # Checkpoint保存的步骤
    is_resumed_from_checkpoint: bool  # 是否从Checkpoint恢复
    last_checkpoint_time: Optional[str]  # 最后Checkpoint时间

    # ==================== 结果验证 ====================
    validation_history: Annotated[List[Dict[str, Any]], add]  # 验证历史记录
    validation_retry_count: int  # 验证重试次数（默认0）
    max_validation_retries: int  # 最大验证重试次数（默认3）
    validation_feedback: Optional[str]  # 验证反馈信息
    is_validation_enabled: bool  # 是否启用验证（默认True）
    should_return_data: bool  # 是否返回完整数据（summary类型可能为False）

    # ==================== 深度分析 ====================
    analysis: Optional[str]  # 深度分析内容
    insights: Optional[List[str]]  # 关键洞察列表
    suggestions: Optional[List[str]]  # 相关建议列表
    analysis_type: Optional[str]  # 分析类型（statistical/spatial/trend）

    # ==================== 最终输出 ====================
    final_data: Optional[List[Dict[str, Any]]]  # 最终合并的数据
    answer: str  # 最终自然语言回答
    status: str  # 最终状态 (success/error)
    message: str  # 最终消息


# ==================== 辅助数据模型 ====================

class ThoughtChainStep(BaseModel):
    """思维链单步记录"""
    step: int = Field(description="步骤编号")
    type: str = Field(description="步骤类型")
    action: Optional[str] = Field(default=None, description="执行动作")
    input: Optional[str] = Field(default=None, description="输入内容")
    output: Optional[Any] = Field(default=None, description="输出内容")
    status: str = Field(description="状态: completed/failed")
    error: Optional[str] = Field(default=None, description="错误信息")


class SQLQueryRecord(BaseModel):
    """SQL查询记录"""
    sql: str = Field(description="SQL语句")
    result: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="查询结果"
    )
    count: int = Field(default=0, description="结果数量")
    step: int = Field(description="执行步骤")
    status: str = Field(description="执行状态")
    error: Optional[str] = Field(default=None, description="错误信息")


class ValidationResult(BaseModel):
    """LLM 验证结果（结构化输出）"""

    validation_passed: bool = Field(
        description="验证是否通过"
    )

    overall_confidence: float = Field(
        ge=0.0, le=1.0,
        description="整体置信度 (0-1之间的浮点数)"
    )

    dimension_scores: Dict[str, float] = Field(
        description="各维度评分",
        default_factory=lambda: {
            "relevance": 0.5,
            "completeness": 0.5,
            "accuracy": 0.5,
            "usefulness": 0.5
        }
    )

    detailed_analysis: Dict[str, str] = Field(
        description="各维度的详细分析",
        default_factory=dict
    )

    improvement_suggestions: List[str] = Field(
        description="改进建议列表",
        default_factory=list
    )

    summary_reason: str = Field(
        description="验证结果的总结原因"
    )

    def get_average_score(self) -> float:
        """计算维度评分的平均值"""
        if not self.dimension_scores:
            return 0.0
        return sum(self.dimension_scores.values()) / len(self.dimension_scores)

    def needs_improvement(self) -> bool:
        """判断是否需要改进"""
        return self.overall_confidence < 0.7 or any(
            score < 0.6 for score in self.dimension_scores.values()
        )


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=== 测试数据模型 ===\n")

    # 测试 QueryResult
    print("--- 测试 QueryResult ---")
    result = QueryResult(
        status="success",
        answer="找到3条记录",
        data=[{"name": "西湖", "level": "5A"}],
        count=1,
        message="查询成功",
        sql="SELECT * FROM a_sight LIMIT 1"
    )
    print(result.model_dump_json(indent=2))
    print()

    # 测试 AgentState (TypedDict)
    print("--- 测试 AgentState ---")
    state: AgentState = {
        "query": "查询浙江省的5A景区",
        "enhanced_query": "查询浙江省的5A景区",
        "query_intent": "query",
        "requires_spatial": False,
        # 数据库Schema字段
        "database_schema": None,
        "schema_fetched": False,
        "sql_history": [],
        "execution_results": [],
        "thought_chain": [],
        "current_step": 0,
        "current_sql": None,
        "current_result": None,
        "should_continue": True,
        "max_iterations": 10,
        "error": None,
        # Fallback 重试机制字段
        "retry_count": 0,
        "max_retries": 3,
        "last_error": None,
        "error_history": [],
        "fallback_strategy": None,
        "error_type": None,
        # ✅ 新增字段
        "error_context": None,
        "query_id": "test-query-123",
        "query_start_time": "2025-10-04T00:00:00",
        "node_execution_logs": [],
        "intent_info": None,
        # Memory 机制字段
        "session_history": [],
        "conversation_id": None,
        "knowledge_base": None,
        "learned_patterns": [],
        # Checkpoint 机制字段
        "saved_checkpoint_id": None,
        "saved_checkpoint_step": None,
        "is_resumed_from_checkpoint": False,
        "last_checkpoint_time": None,
        # ✅ 结果验证字段
        "validation_history": [],
        "validation_retry_count": 0,
        "max_validation_retries": 3,
        "validation_feedback": None,
        "is_validation_enabled": True,
        "should_return_data": True,
        # ✅ 深度分析字段
        "analysis": None,
        "insights": None,
        "suggestions": None,
        "analysis_type": None,
        # 最终输出字段
        "final_data": None,
        "answer": "",
        "status": "pending",
        "message": ""
    }
    print(f"State keys: {state.keys()}")
    print(f"Query: {state['query']}")
    print(f"Max iterations: {state['max_iterations']}")
    print()

    # 测试 ThoughtChainStep
    print("--- 测试 ThoughtChainStep ---")
    step = ThoughtChainStep(
        step=1,
        type="sql_generation",
        action="generate_sql",
        input="查询浙江省的5A景区",
        output="SELECT * FROM a_sight WHERE province='浙江省'",
        status="completed"
    )
    print(step.model_dump_json(indent=2))
    print()

    # 测试 SQLQueryRecord
    print("--- 测试 SQLQueryRecord ---")
    query_record = SQLQueryRecord(
        sql="SELECT * FROM a_sight LIMIT 1",
        result=[{"name": "西湖"}],
        count=1,
        step=1,
        status="completed"
    )
    print(query_record.model_dump_json(indent=2))

