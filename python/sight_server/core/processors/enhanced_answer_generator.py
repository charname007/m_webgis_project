"""
增强答案生成器模块 - Sight Server
提供深度分析和智能解读功能，结合SQL执行结果和用户问题进行智能分析
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class EnhancedAnswerGenerator:
    """
    增强答案生成器

    功能:
    - 结合SQL执行结果和用户问题进行深度分析
    - 提供数据洞察、统计解读和业务建议
    - 支持不同查询类型的智能分析
    - 使用LLM进行语义分析和解释
    """

    def __init__(self, llm):
        """
        初始化增强答案生成器

        Args:
            llm: LLM实例
        """
        self.llm = llm
        self.logger = logger

        # 深度分析提示词模板
        self.deep_analysis_prompt = PromptTemplate(
            template="""你是一个精通数据分析和业务洞察的专家。请根据用户查询和查询结果，提供深度分析和智能解读。

## 用户查询
{query}

## 查询结果
- 结果数量: {count}
- 查询意图: {intent_type}
- 是否空间查询: {is_spatial}

## 结果数据
{data_preview}

## 分析要求
请基于以上信息，提供以下分析：

### 1. 数据洞察
- 结果是否回答了用户的问题？
- 数据中有什么有趣的模式或趋势？
- 是否有异常值或值得注意的地方？

### 2. 统计解读（如果适用）
- 对于统计查询，解释统计结果的意义
- 提供业务角度的解读
- 指出数据中的关键发现

### 3. 业务建议
- 基于查询结果提供相关建议
- 指出可能的后续查询方向
- 提供实用的行动建议

### 4. 结果验证
- 确认结果是否完整和准确
- 指出可能的数据局限性
- 如果需要更多数据，说明原因

请生成一个自然、友好且专业的回答，包含以上分析要点。

回答:""",
            input_variables=["query", "count", "intent_type", "is_spatial", "data_preview"]
        )

        # 统计查询分析提示词
        self.statistical_analysis_prompt = PromptTemplate(
            template="""你是一个统计分析和数据解读专家。请对以下统计查询结果进行深度分析。

## 用户查询
{query}

## 统计结果
- 结果数量: {count}
- 查询类型: {intent_type}

## 结果数据
{data_preview}

## 分析要求
请提供以下分析：

### 统计意义解读
- 解释统计结果的含义
- 指出数据中的关键发现
- 分析数据分布和模式

### 业务洞察
- 从业务角度解读统计结果
- 指出潜在的机会或问题
- 提供基于数据的建议

### 数据质量评估
- 评估结果的完整性和准确性
- 指出可能的局限性
- 建议是否需要补充数据

请生成专业的统计解读回答。

回答:""",
            input_variables=["query", "count", "intent_type", "data_preview"]
        )

    def generate_enhanced_answer(
        self,
        query: str,
        data: Optional[List[Dict[str, Any]]],
        count: int,
        intent_type: str = "query",
        is_spatial: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """
        生成增强的自然语言回答，包含深度分析

        Args:
            query: 原始查询
            data: 查询结果数据
            count: 结果数量
            intent_type: 查询意图类型
            is_spatial: 是否空间查询

        Returns:
            (answer, analysis_details): 增强回答和分析详情
        """
        try:
            # 无数据情况
            if count == 0 or not data:
                basic_answer = self._generate_no_data_answer(query)
                return basic_answer, {"analysis_type": "no_data", "confidence": 0.0}

            # 准备数据预览
            data_preview = self._prepare_data_preview(data, count)

            # 根据查询类型选择分析策略
            if intent_type == "summary":
                answer = self._generate_statistical_analysis(query, data, count, data_preview)
                analysis_details = {
                    "analysis_type": "statistical",
                    "confidence": 0.8,
                    "insights": ["统计结果分析", "业务解读"]
                }
            else:
                answer = self._generate_deep_analysis(query, data, count, intent_type, is_spatial, data_preview)
                analysis_details = {
                    "analysis_type": "deep_analysis",
                    "confidence": 0.7,
                    "insights": ["数据洞察", "业务建议"]
                }

            return answer, analysis_details

        except Exception as e:
            self.logger.error(f"Enhanced answer generation failed: {e}")
            # 回退到基本答案
            basic_answer = f"查询完成，共找到 {count} 条记录。"
            return basic_answer, {"analysis_type": "fallback", "confidence": 0.0}

    def _prepare_data_preview(self, data: List[Dict[str, Any]], count: int) -> str:
        """
        准备数据预览用于分析

        Args:
            data: 查询结果
            count: 结果数量

        Returns:
            数据预览字符串
        """
        if not data:
            return "无数据"

        # 限制预览记录数
        preview_count = min(15, len(data))
        preview_data = data[:preview_count]

        preview_lines = []
        for i, record in enumerate(preview_data):
            # preview_lines.append(f"记录 {i+1}: {self._format_record_preview(record)}")
            preview_lines.append(
                f"记录 {i+1}: {str(record)}")

        preview_text = "\n".join(preview_lines)

        if count > preview_count:
            preview_text += f"\n... 还有 {count - preview_count} 条记录"

        return preview_text

    def _format_record_preview(self, record: Dict[str, Any]) -> str:
        """
        格式化单条记录预览

        Args:
            record: 单条记录

        Returns:
            格式化后的预览字符串
        """
        # 提取关键字段
        key_fields = ['name', 'level', '评分', '门票', '所属省份', '所属城市']
        preview_parts = []

        for field in key_fields:
            if field in record and record[field]:
                value = record[field]
                if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip()):
                    preview_parts.append(f"{field}: {value}")

        return ", ".join(preview_parts) if preview_parts else str(record)

    def _generate_deep_analysis(
        self,
        query: str,
        data: List[Dict[str, Any]],
        count: int,
        intent_type: str,
        is_spatial: bool,
        data_preview: str
    ) -> str:
        """
        生成深度分析回答

        Args:
            query: 原始查询
            data: 查询结果
            count: 结果数量
            intent_type: 查询意图
            is_spatial: 是否空间查询
            data_preview: 数据预览

        Returns:
            深度分析回答
        """
        try:
            # 构建提示词
            prompt_text = self.deep_analysis_prompt.format(
                query=query,
                count=count,
                intent_type=intent_type,
                is_spatial=is_spatial,
                data_preview=data_preview
            )

            # 调用LLM
            response = self.llm.llm.invoke(prompt_text)

            if hasattr(response, 'content'):
                answer = response.content.strip()
            else:
                answer = str(response).strip()

            return answer

        except Exception as e:
            self.logger.error(f"Deep analysis generation failed: {e}")
            # 回退到基本分析
            return self._generate_basic_analysis(query, data, count)

    def _generate_statistical_analysis(
        self,
        query: str,
        data: List[Dict[str, Any]],
        count: int,
        data_preview: str
    ) -> str:
        """
        生成统计查询的深度分析

        Args:
            query: 原始查询
            data: 查询结果
            count: 结果数量
            data_preview: 数据预览

        Returns:
            统计分析回答
        """
        try:
            # 构建提示词
            prompt_text = self.statistical_analysis_prompt.format(
                query=query,
                count=count,
                intent_type="summary",
                data_preview=data_preview
            )

            # 调用LLM
            response = self.llm.llm.invoke(prompt_text)

            if hasattr(response, 'content'):
                answer = response.content.strip()
            else:
                answer = str(response).strip()

            return answer

        except Exception as e:
            self.logger.error(f"Statistical analysis generation failed: {e}")
            # 回退到基本统计答案
            return f"根据您的查询「{query}」，统计结果为 {count} 条记录。"

    def _generate_basic_analysis(
        self,
        query: str,
        data: List[Dict[str, Any]],
        count: int
    ) -> str:
        """
        生成基本分析回答（回退方法）

        Args:
            query: 原始查询
            data: 查询结果
            count: 结果数量

        Returns:
            基本分析回答
        """
        answer_parts = [f"根据您的查询「{query}」，共找到 {count} 条相关记录。"]

        # 添加基本统计信息
        if data and count > 0:
            # 检查是否有等级信息
            if 'level' in data[0]:
                levels = {}
                for record in data:
                    level = record.get('level')
                    if level:
                        levels[level] = levels.get(level, 0) + 1

                if levels:
                    level_text = "，其中" + "、".join(
                        f"{level}级{num}个" for level, num in sorted(levels.items())
                    )
                    answer_parts.append(level_text)

            # 检查是否有评分信息
            if '评分' in data[0]:
                valid_scores = [float(r['评分']) for r in data if r.get('评分') and self._is_numeric(r['评分'])]
                if valid_scores:
                    avg_score = sum(valid_scores) / len(valid_scores)
                    answer_parts.append(f"，平均评分 {avg_score:.1f}")

        return "".join(answer_parts) + "。"

    def _generate_no_data_answer(self, query: str) -> str:
        """
        生成无数据的回答

        Args:
            query: 原始查询

        Returns:
            无数据回答
        """
        return f"根据您的查询「{query}」，未找到匹配的数据。建议您调整查询条件或检查数据源。"

    def _is_numeric(self, value: Any) -> bool:
        """
        检查值是否为数字

        Args:
            value: 要检查的值

        Returns:
            是否为数字
        """
        try:
            float(str(value))
            return True
        except (ValueError, TypeError):
            return False


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== EnhancedAnswerGenerator 测试 ===\n")

    # 模拟LLM
    class MockLLM:
        def __init__(self):
            self.llm = self

        def invoke(self, prompt):
            return "这是一个模拟的深度分析回答，包含数据洞察、统计解读和业务建议。"

    # 创建生成器
    generator = EnhancedAnswerGenerator(MockLLM())

    # 测试数据
    test_data = [
        {"name": "西湖", "level": "5A", "评分": "4.8", "门票": "免费", "所属省份": "浙江省", "所属城市": "杭州市"},
        {"name": "千岛湖", "level": "5A", "评分": "4.6", "门票": "150元", "所属省份": "浙江省", "所属城市": "杭州市"},
        {"name": "灵隐寺", "level": "4A", "评分": "4.7", "门票": "75元", "所属省份": "浙江省", "所属城市": "杭州市"}
    ]

    # 测试1: 深度分析
    print("--- 测试1: 深度分析 ---")
    query1 = "查询浙江省的5A景区"
    answer1, analysis1 = generator.generate_enhanced_answer(query1, test_data, 3, "query", False)
    print(f"Query: {query1}")
    print(f"Answer: {answer1}")
    print(f"Analysis: {analysis1}\n")

    # 测试2: 统计分析
    print("--- 测试2: 统计分析 ---")
    query2 = "统计浙江省有多少个5A景区"
    answer2, analysis2 = generator.generate_enhanced_answer(query2, test_data[:2], 2, "summary", False)
    print(f"Query: {query2}")
    print(f"Answer: {answer2}")
    print(f"Analysis: {analysis2}\n")

    # 测试3: 无数据情况
    print("--- 测试3: 无数据情况 ---")
    query3 = "查询西藏的5A景区"
    answer3, analysis3 = generator.generate_enhanced_answer(query3, None, 0, "query", False)
    print(f"Query: {query3}")
    print(f"Answer: {answer3}")
    print(f"Analysis: {analysis3}\n")
