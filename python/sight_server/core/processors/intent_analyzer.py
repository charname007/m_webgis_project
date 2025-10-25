"""
意图分析器模块 - Sight Server
使用 LLM + Pydantic OutputParser 进行查询意图分析
"""

import logging
from typing import Dict, Any, Optional
from langchain_core.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from ..schemas import QueryIntentAnalysis, IntentType
from ..llm import BaseLLM
from ..prompts import PromptType

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """
    使用 LLM + Pydantic 进行查询意图分析

    功能:
    - 通过 LLM 语义理解分析查询意图
    - 使用 Pydantic OutputParser 确保结构化输出
    - 提供 Fallback 机制（失败时使用关键词分析）
    """

    def __init__(self, llm: BaseLLM):
        """
        初始化意图分析器

        Args:
            llm: BaseLLM 实例
        """
        self.llm = llm
        self.logger = logger

        # ✅ 创建 Pydantic OutputParser
        self.parser = PydanticOutputParser(pydantic_object=QueryIntentAnalysis)

        # ✅ 创建 Prompt 模板
        self.prompt = PromptTemplate(
            template="""你是一个查询意图分析专家。分析用户的查询意图并分类。

**用户查询**: {query}

**分析标准**:

1. **Intent Type 判断**:
   - **summary**: 用户需要统计数字（数量、平均值、总数、分布等），不需要详细记录
     * 关键词：统计、多少、数量、总数、一共、总共、平均、分布、汇总、计数
     * 示例："浙江省有多少个5A景区"（只需要数字19）
     * 示例："统计各省份景区数量"（需要分组统计）

   - **query**: 用户需要具体记录列表或详细信息
     * 关键词：查询、查找、列出、显示、详细信息、哪些、推荐
     * 示例："查询浙江省的5A景区"（需要景区列表）
     * 示例："推荐几个杭州的景区"（需要景区详情）

2. **Spatial 判断**:
   - **true**: 涉及距离、位置、附近、周边等空间概念
     * 关键词：距离、附近、周边、临近、周围、范围内、最近
     * 示例："杭州附近10公里的景区"

   - **false**: 普通数据查询，不涉及空间计算
     * 示例："浙江省的5A景区"

3. **Query Clarity 判断**:
   - **true**: 查询明确清晰，可以直接执行
     * 标准：查询包含具体信息（地点、类型、条件等）
     * 示例："查询浙江省的5A景区"（明确）
     * 示例："推荐几个杭州的景区"（明确）

   - **false**: 查询不明确，需要用户重新表述
     * 标准：查询过于模糊、缺少关键信息、有歧义
     * 示例："查询景区"（不明确，缺少地点）
     * 示例："推荐"（不明确，缺少类型）
     * 示例："附近有什么"（不明确，缺少参考点）

4. **Confidence 评估**:
   - 0.8-1.0: 意图非常明确（有明确的统计/查询关键词）
   - 0.5-0.8: 意图较明确（可以从上下文推断）
   - 0.0-0.5: 意图模糊（需要更多信息）

5. **Keywords Matched**:
   - 列出查询中识别到的关键词

6. **Reasoning**:
   - 详细说明你的分析推理过程

{format_instructions}

请仔细分析并返回 JSON 格式结果。""",
            input_variables=["query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

    def analyze_intent(self, query: str) -> Dict[str, Any]:
        """
        使用 LLM 分析查询意图

        Args:
            query: 用户查询文本

        Returns:
            意图分析结果字典，包含:
            - intent_type: "query" | "summary"
            - is_spatial: bool
            - confidence: float
            - reasoning: str
            - keywords_matched: List[str]
            - prompt_type: PromptType
            - description: str
            - analysis_details: Dict
            - semantic_enhanced: bool
        """
        try:
            # 生成 prompt
            prompt_text = self.prompt.format(query=query)

            # 调用 LLM
            self.logger.debug(f"Analyzing intent with LLM for: {query}")
            response = self.llm.llm.invoke(prompt_text)

            # 解析结构化输出
            result: QueryIntentAnalysis = self.parser.parse(response.content)

            self.logger.info(
                f"LLM intent analysis: type={result.intent_type.value}, "
                f"spatial={result.is_spatial}, confidence={result.confidence:.2f}"
            )

            # 转换为字典（兼容现有代码）
            return {
                "intent_type": result.intent_type.value,
                "is_spatial": result.is_spatial,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "keywords_matched": result.keywords_matched,
                "is_query_clear": result.is_query_clear,
                "prompt_type": self._infer_prompt_type(result.intent_type.value, result.is_spatial),
                "description": result.reasoning,  # 使用 reasoning 作为描述
                "analysis_details": {
                    "method": "llm_with_pydantic",
                    "model": self.llm.model,
                    "summary_score": 1.0 if result.intent_type == IntentType.SUMMARY else 0.0,
                    "spatial_score": 1.0 if result.is_spatial else 0.0,
                    "scenic_score": 0.5,  # LLM 分析不单独评分 scenic
                    "clarity_score": 1.0 if result.is_query_clear else 0.0
                },
                "semantic_enhanced": True  # LLM 分析即为语义增强
            }

        except Exception as e:
            self.logger.error(f"LLM intent analysis failed: {e}")
            self.logger.warning("Falling back to keyword-based analysis")
            # Fallback 到关键词分析
            return self._fallback_keyword_analysis(query)

    def _infer_prompt_type(self, intent_type: str, is_spatial: bool) -> PromptType:
        """
        推断 prompt 类型

        Args:
            intent_type: 意图类型
            is_spatial: 是否空间查询

        Returns:
            PromptType 枚举
        """
        if is_spatial:
            return PromptType.SPATIAL_QUERY
        return PromptType.SCENIC_QUERY

    def _fallback_keyword_analysis(self, query: str) -> Dict[str, Any]:
        """
        Fallback: 使用关键词分析（保持系统稳定）

        当 LLM 分析失败时，回退到原有的关键词分析方法

        Args:
            query: 查询文本

        Returns:
            意图分析结果
        """
        # 导入 PromptManager 的关键词分析方法
        from ..prompts import PromptManager

        self.logger.info("Using keyword-based fallback analysis")
        # 调用原有的关键词分析方法
        return PromptManager._analyze_intent_by_keywords(query)
