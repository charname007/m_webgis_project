"""
查询继续决策Schema - 使用PydanticOutputParser结构化LLM输出
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class QueryContinuationDecision(BaseModel):
    """
    LLM查询继续决策结果
    
    基于用户需求评估是否需要继续查询，而不是基于技术字段完整度
    """
    should_continue: bool = Field(description="是否继续查询")
    confidence: float = Field(description="决策置信度(0-1)", ge=0, le=1)
    reasoning: str = Field(description="决策理由")
    
    # 基于用户需求的评估
    user_needs_satisfaction: float = Field(description="用户需求满足度(0-1)", ge=0, le=1)
    core_question_answered: bool = Field(description="核心问题是否已回答")
    missing_critical_info: List[str] = Field(description="缺失的关键信息")
    
    # 建议
    suggested_improvements: List[str] = Field(description="改进建议")
    query_refinement: Optional[str] = Field(description="查询优化建议")
    
    # 补充查询指导
    supplement_guidance: Optional[str] = Field(description="补充查询指导")


class UserNeedsAssessment(BaseModel):
    """
    用户需求满足度评估
    """
    core_question_answered: bool = Field(description="核心问题是否已回答")
    satisfaction_level: float = Field(description="需求满足度(0-1)", ge=0, le=1)
    missing_critical_info: List[str] = Field(description="缺失的关键信息")
    sufficient_for_decision: bool = Field(description="是否足够做出决策")
    improvement_suggestions: List[str] = Field(description="改进建议")
