"""
数据分析器模块 - Sight Server
使用 LLM 对查询结果进行深度分析，提供洞察和建议
"""

import json
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
import logging

# 设置日志
logger = logging.getLogger(__name__)


# ==================== 输出模型 ====================

class AnswerAnalysisResult(BaseModel):
    """答案分析结果模型（结构化输出）"""

    answer: str = Field(
        description="简洁的自然语言答案（1-3句话）"
    )

    analysis: str = Field(
        description="深度分析内容（2-4段，包含数据洞察、模式识别、趋势分析等）"
    )

    insights: List[str] = Field(
        default_factory=list,
        description="关键洞察列表（3-5条重要发现）"
    )

    suggestions: Optional[List[str]] = Field(
        default=None,
        description="相关建议列表（可选，基于数据提供的建议）"
    )

    analysis_type: Literal["statistical", "spatial", "trend", "general"] = Field(
        default="general",
        description="分析类型：statistical=统计分析，spatial=空间分析，trend=趋势分析，general=综合分析"
    )


# ==================== 分析器类 ====================

class DataAnalyzer:
    """
    数据分析器

    功能：
    - 生成简洁的自然语言答案
    - 进行深度数据分析
    - 识别数据模式和趋势
    - 提供关键洞察
    - 给出相关建议
    """

    def __init__(self, llm):
        """
        初始化分析器

        Args:
            llm: LLM 实例（支持结构化输出）
        """
        self.llm = llm
        self.logger = logging.getLogger(__name__)

    def analyze(
        self,
        query: str,
        final_data: List[Dict[str, Any]],
        intent_info: Optional[Dict[str, Any]] = None
    ) -> AnswerAnalysisResult:
        """
        分析查询结果并生成答案

        Args:
            query: 用户原始查询
            final_data: 最终查询结果数据
            intent_info: 查询意图信息

        Returns:
            AnswerAnalysisResult: 分析结果
        """
        # 提取意图信息
        intent_type = intent_info.get("intent_type", "query") if intent_info else "query"
        is_spatial = intent_info.get("is_spatial", False) if intent_info else False

        # 构建分析提示词
        analysis_prompt = self._build_analysis_prompt(
            query=query,
            intent_type=intent_type,
            is_spatial=is_spatial,
            final_data=final_data
        )

        self.logger.debug(f"分析提示词：\n{analysis_prompt}")

        try:
            # 调用 LLM 进行分析
            result = self.llm.invoke_with_structure(
                prompt=analysis_prompt,
                structure=AnswerAnalysisResult
            )

            self.logger.info(
                f"分析完成 - 类型: {result.analysis_type}, "
                f"洞察数: {len(result.insights)}, "
                f"建议数: {len(result.suggestions) if result.suggestions else 0}"
            )

            return result

        except Exception as e:
            self.logger.error(f"分析过程出错: {e}")
            # 出错时返回基础答案
            return self._generate_fallback_answer(query, final_data)

    def _build_analysis_prompt(
        self,
        query: str,
        intent_type: str,
        is_spatial: bool,
        final_data: List[Dict[str, Any]]
    ) -> str:
        """
        构建分析提示词

        Args:
            query: 用户查询
            intent_type: 查询意图类型（query/summary）
            is_spatial: 是否空间查询
            final_data: 最终数据

        Returns:
            str: 分析提示词
        """
        # 数据统计
        count = len(final_data) if final_data else 0

        # 获取数据样例（前5条）
        sample_data = final_data[:5] if final_data else []
        sample_json = json.dumps(sample_data, ensure_ascii=False, indent=2)

        # 构建基础提示
        prompt = f"""你是专业的数据分析师，负责分析查询结果并提供洞察。

**用户问题**: {query}

**查询意图**: {intent_type} (空间查询: {'是' if is_spatial else '否'})

**查询结果统计**:
- 结果数量: {count} 条
- 数据样例（前5条）:
```json
{sample_json}
```

**分析任务**:

1. **生成答案** (必需):
   - 用1-3句话简洁地回答用户的问题
   - 突出关键数字和重要信息
   - 语言自然、易懂

2. **深度分析** (必需):
   - 总结关键发现（2-4段文字）
   - 识别数据中的模式和规律
   """

        # 根据查询类型添加特定分析
        if intent_type == "summary":
            prompt += """   - 分析统计结果的含义
   - 解释数据分布特征
   - 对比不同维度的差异
"""
        else:  # query
            prompt += """   - 总结查询结果的特点
   - 分析数据的分布情况
   - 发现有价值的信息
"""

        # 空间查询特殊分析
        if is_spatial:
            prompt += """
   **空间分析重点**:
   - 分析地理分布特征（如集中在哪些区域）
   - 识别空间聚集模式
   - 解释空间关系（如距离、方位等）
"""

        # 洞察和建议
        prompt += """
3. **关键洞察** (必需):
   - 提取3-5条重要发现
   - 每条洞察要具体、有价值
   - 用数据支撑洞察

4. **相关建议** (可选):
   - 基于数据提供实用建议
   - 如果数据不支持建议，可以不提供
   - 建议要具体、可操作
"""

        # 空结果特殊处理
        if count == 0:
            prompt += """

**注意**: 查询结果为空！
- answer: 告知用户未找到符合条件的结果
- analysis: 解释可能的原因（查询条件严格、数据库中无此数据等）
- insights: 提供查询建议（如调整查询条件、扩大范围等）
- suggestions: 给出改进查询的具体建议
"""

        # 要求返回结构化输出
        prompt += """

**输出要求**:

请返回结构化的分析结果：
```json
{
  "answer": "简洁的答案（1-3句话）",
  "analysis": "深度分析内容（2-4段）\\n\\n每段之间用\\n\\n分隔",
  "insights": [
    "洞察1（具体数据支撑）",
    "洞察2（具体数据支撑）",
    "洞察3（具体数据支撑）"
  ],
  "suggestions": [  // 可选
    "建议1（具体可操作）",
    "建议2（具体可操作）"
  ],
  "analysis_type": "statistical/spatial/trend/general"
}
```

**分析类型判断**:
- statistical: 主要是统计、计数、汇总分析
- spatial: 主要是空间、地理、距离分析
- trend: 主要是趋势、变化、对比分析
- general: 综合分析或无明显类型

**质量要求**:
- answer: 直接回答用户问题，包含关键数字
- analysis: 有深度、有洞察，不要流水账
- insights: 具体、有价值，用数据说话
- suggestions: 实用、可操作（如果没有合适的建议可以不提供）

**示例**（仅供参考格式）:

用户问题: "武汉市景区的空间分布情况"

```json
{
  "answer": "武汉市共有56个景区，主要分布在武昌区、洪山区等中心城区，呈现东部密集、西部稀疏的空间格局。",
  "analysis": "根据查询结果，武汉市景区空间分布呈现以下特征：\\n\\n1. **区域分布不均**：武昌区景区数量最多（15个），占比26.8%，其次是洪山区（12个，21.4%），说明中心城区的旅游资源更为集中。\\n\\n2. **空间聚集特征**：主要景区集中在东部区域（经度114.3-114.4°），可能与长江沿线和东湖风景区有关。形成了以武昌-洪山为核心的旅游集聚区。\\n\\n3. **发展潜力**：西部地区景区较少（仅占15%），未来可考虑开发新的旅游资源以平衡区域发展。",
  "insights": [
    "武昌区景区数量最多，占全市的26.8%，是武汉旅游的核心区域",
    "景区主要集中在东部区域（经度114.3-114.4°），形成明显的空间聚集",
    "西部地区景区仅占15%，存在较大的开发空间",
    "中心城区（武昌、洪山、江汉）景区占比超过60%，资源分布集中",
    "长江沿线和东湖周边是景区密度最高的区域"
  ],
  "suggestions": [
    "可以考虑在西部地区开发新的旅游资源，平衡全市旅游发展",
    "加强中心城区景区的服务质量和基础设施建设，提升竞争力",
    "发掘长江、东湖等水系周边的旅游潜力，打造滨水旅游带"
  ],
  "analysis_type": "spatial"
}
```
"""

        return prompt

    def _generate_fallback_answer(
        self,
        query: str,
        final_data: List[Dict[str, Any]]
    ) -> AnswerAnalysisResult:
        """
        生成后备答案（当 LLM 调用失败时）

        Args:
            query: 用户查询
            final_data: 最终数据

        Returns:
            AnswerAnalysisResult: 基础答案
        """
        count = len(final_data) if final_data else 0

        if count == 0:
            return AnswerAnalysisResult(
                answer="未找到符合条件的结果。",
                analysis="查询未返回任何数据，可能是查询条件过于严格，或者数据库中确实没有符合条件的记录。",
                insights=["查询结果为空", "可能需要调整查询条件"],
                suggestions=["尝试放宽查询条件", "检查查询关键词是否正确"],
                analysis_type="general"
            )
        else:
            return AnswerAnalysisResult(
                answer=f"查询完成，共找到 {count} 条结果。",
                analysis=f"查询成功返回了 {count} 条记录，数据已按要求提取。",
                insights=[f"共找到 {count} 条符合条件的记录"],
                suggestions=None,
                analysis_type="general"
            )

    def should_analyze(
        self,
        intent_info: Optional[Dict[str, Any]],
        final_data: Optional[List[Dict[str, Any]]]
    ) -> bool:
        """
        判断是否需要深度分析

        Args:
            intent_info: 查询意图信息
            final_data: 最终数据

        Returns:
            bool: 是否需要深度分析
        """
        # 没有数据也需要分析（解释原因）
        if not final_data:
            return True

        # 数据量过大（>100条）且是query类型，可以简化分析
        if len(final_data) > 100:
            intent_type = intent_info.get("intent_type", "query") if intent_info else "query"
            if intent_type == "query":
                self.logger.info(f"数据量较大 ({len(final_data)}条)，建议简化分析")
                # 仍然需要分析，但可以采样
                return True

        return True


# ==================== 测试代码 ====================

if __name__ == "__main__":
    from core.llm import LLMFactory

    print("=== 测试 DataAnalyzer ===\n")

    # 初始化 LLM
    llm = LLMFactory.create_llm()
    analyzer = DataAnalyzer(llm)

    # 测试案例 1: 统计查询
    print("--- 测试案例 1: 统计查询 ---")
    result1 = analyzer.analyze(
        query="武汉市各区景区数量统计",
        final_data=[
            {"district": "武昌区", "count": 15, "percentage": 26.8},
            {"district": "洪山区", "count": 12, "percentage": 21.4},
            {"district": "江汉区", "count": 8, "percentage": 14.3},
            {"district": "其他", "count": 21, "percentage": 37.5}
        ],
        intent_info={"intent_type": "summary", "is_spatial": False}
    )
    print(f"答案: {result1.answer}")
    print(f"分析类型: {result1.analysis_type}")
    print(f"洞察数量: {len(result1.insights)}")
    print(f"分析内容:\n{result1.analysis}")
    print()

    # 测试案例 2: 空间查询
    print("--- 测试案例 2: 空间查询 ---")
    result2 = analyzer.analyze(
        query="查询杭州西湖附近10公里的景区",
        final_data=[
            {
                "name": "灵隐寺",
                "distance": 5.2,
                "coordinates": [120.10, 30.24],
                "rating": 4.6
            },
            {
                "name": "雷峰塔",
                "distance": 1.8,
                "coordinates": [120.15, 30.23],
                "rating": 4.5
            }
        ],
        intent_info={"intent_type": "query", "is_spatial": True}
    )
    print(f"答案: {result2.answer}")
    print(f"分析类型: {result2.analysis_type}")
    print(f"洞察: {result2.insights}")
    print()

    # 测试案例 3: 空结果
    print("--- 测试案例 3: 空结果 ---")
    result3 = analyzer.analyze(
        query="查询火星上的景区",
        final_data=[],
        intent_info={"intent_type": "query", "is_spatial": False}
    )
    print(f"答案: {result3.answer}")
    print(f"分析: {result3.analysis}")
    print(f"建议: {result3.suggestions}")
