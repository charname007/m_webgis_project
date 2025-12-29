"""
答案生成器模块 - Sight Server
负责根据查询结果生成自然语言回答
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """
    答案生成器

    功能:
    - 根据查询结果生成自然语言回答
    - 支持不同查询类型（列表查询、统计查询、详情查询）
    - 提供上下文相关的答案
    """

    def __init__(self, llm=None):
        """
        初始化答案生成器

        Args:
            llm: LLM实例（可选，用于高级答案生成）
        """
        self.llm = llm
        self.logger = logger

    def generate(
        self,
        query: str,
        data: Optional[List[Dict[str, Any]]],
        count: int
    ) -> str:
        """
        生成自然语言回答

        Args:
            query: 原始查询
            data: 查询结果数据
            count: 结果数量

        Returns:
            自然语言回答
        """
        try:
            # 无数据情况
            if count == 0 or not data:
                return self._generate_no_data_answer(query)

            # 检测查询类型
            query_type = self._detect_query_type(query)

            # 根据类型生成答案
            if query_type == "statistical":
                return self._generate_statistical_answer(query, data, count)
            elif query_type == "detail":
                return self._generate_detail_answer(query, data, count)
            else:
                return self._generate_list_answer(query, data, count)

        except Exception as e:
            self.logger.warning(f"Answer generation failed: {e}")
            return f"查询完成，共找到 {count} 条记录。"

    def _detect_query_type(self, query: str) -> str:
        """
        检测查询类型

        Args:
            query: 查询文本

        Returns:
            查询类型: "statistical" | "detail" | "list"
        """
        query_lower = query.lower()

        # 统计类查询关键词
        statistical_keywords = [
            '统计', '总结', '汇总', '多少', '数量', '分布',
            '平均', '最多', '最少', '排名', '总数', '计数',
            '有几个', '有多少', '几个'
        ]

        # 详情类查询关键词
        detail_keywords = [
            '介绍', '详细', '信息', '评分', '门票', '开放时间',
            '怎么样', '如何', '什么样'
        ]

        # 检测统计类
        if any(kw in query_lower for kw in statistical_keywords):
            return "statistical"

        # 检测详情类
        if any(kw in query_lower for kw in detail_keywords):
            return "detail"

        # 默认为列表类
        return "list"

    def _generate_no_data_answer(self, query: str) -> str:
        """
        生成无数据的回答

        Args:
            query: 原始查询

        Returns:
            无数据回答
        """
        return f"根据您的查询「{query}」，未找到匹配的数据。"

    def _generate_statistical_answer(
        self,
        query: str,
        data: List[Dict[str, Any]],
        count: int
    ) -> str:
        """
        生成统计类查询的回答

        Args:
            query: 原始查询
            data: 查询结果
            count: 结果数量

        Returns:
            统计类回答
        """
        # 基础统计答案
        answer = f"根据您的查询「{query}」，共找到 {count} 条相关记录。"

        # 尝试提供更多统计信息
        try:
            # 如果数据包含 level 字段，统计各等级数量
            if data and 'level' in data[0]:
                level_stats = {}
                for record in data:
                    level = record.get('level', '未知')
                    level_stats[level] = level_stats.get(level, 0) + 1

                if level_stats:
                    stats_text = "，其中" + "、".join(
                        f"{level}级{num}个"
                        for level, num in sorted(level_stats.items())
                    )
                    answer += stats_text + "。"

        except Exception as e:
            self.logger.debug(f"Failed to generate detailed statistics: {e}")

        return answer

    def _generate_detail_answer(
        self,
        query: str,
        data: List[Dict[str, Any]],
        count: int
    ) -> str:
        """
        生成详情类查询的回答

        Args:
            query: 原始查询
            data: 查询结果
            count: 结果数量

        Returns:
            详情类回答
        """
        if count == 1:
            # 单个结果，提供详细信息
            record = data[0]
            name = record.get('name', '该景区')

            answer_parts = [f"根据您的查询「{query}」，找到{name}的相关信息。"]

            # 添加评级信息
            if 'level' in record and record['level']:
                answer_parts.append(f"该景区评级为{record['level']}。")

            # 添加评分信息
            if '评分' in record and record['评分']:
                answer_parts.append(f"评分：{record['评分']}。")

            # 添加门票信息
            if '门票' in record and record['门票']:
                answer_parts.append(f"门票：{record['门票']}。")

            return " ".join(answer_parts)

        else:
            # 多个结果
            return f"根据您的查询「{query}」，找到 {count} 条相关记录的详细信息。"

    def _generate_list_answer(
        self,
        query: str,
        data: List[Dict[str, Any]],
        count: int
    ) -> str:
        """
        生成列表类查询的回答

        Args:
            query: 原始查询
            data: 查询结果
            count: 结果数量

        Returns:
            列表类回答
        """
        return f"根据您的查询「{query}」，找到 {count} 条相关记录。"

    def generate_with_llm(
        self,
        query: str,
        data: Optional[List[Dict[str, Any]]],
        count: int
    ) -> str:
        """
        使用LLM生成更智能的回答（可选功能）

        Args:
            query: 原始查询
            data: 查询结果
            count: 结果数量

        Returns:
            LLM生成的回答
        """
        if not self.llm:
            # 如果没有LLM，回退到规则生成
            return self.generate(query, data, count)

        try:
            # 构建提示词
            prompt = f"""根据用户查询和查询结果，生成自然、友好的回答。

用户查询: {query}

查询结果数量: {count}

请生成一个简洁的自然语言回答（1-2句话）。"""

            # 调用LLM
            response = self.llm.llm.invoke(prompt)

            if hasattr(response, 'content'):
                answer = response.content.strip()
            else:
                answer = str(response).strip()

            return answer

        except Exception as e:
            self.logger.error(f"LLM answer generation failed: {e}")
            # 回退到规则生成
            return self.generate(query, data, count)


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== AnswerGenerator 测试 ===\n")

    generator = AnswerGenerator()

    # 测试数据
    test_data = [
        {"name": "西湖", "level": "5A", "评分": "4.8", "门票": "免费"},
        {"name": "千岛湖", "level": "5A", "评分": "4.6", "门票": "150元"},
        {"name": "灵隐寺", "level": "4A", "评分": "4.7", "门票": "75元"}
    ]

    # 测试1: 统计类查询
    print("--- 测试1: 统计类查询 ---")
    query1 = "统计浙江省有多少个5A景区"
    answer1 = generator.generate(query1, test_data[:2], 2)
    print(f"Query: {query1}")
    print(f"Answer: {answer1}\n")

    # 测试2: 详情类查询（单个结果）
    print("--- 测试2: 详情类查询（单个结果）---")
    query2 = "西湖的详细信息"
    answer2 = generator.generate(query2, [test_data[0]], 1)
    print(f"Query: {query2}")
    print(f"Answer: {answer2}\n")

    # 测试3: 列表类查询
    print("--- 测试3: 列表类查询 ---")
    query3 = "查询浙江省的景区"
    answer3 = generator.generate(query3, test_data, 3)
    print(f"Query: {query3}")
    print(f"Answer: {answer3}\n")

    # 测试4: 无数据查询
    print("--- 测试4: 无数据查询 ---")
    query4 = "查询西藏的5A景区"
    answer4 = generator.generate(query4, None, 0)
    print(f"Query: {query4}")
    print(f"Answer: {answer4}\n")

    # 测试5: 查询类型检测
    print("--- 测试5: 查询类型检测 ---")
    test_queries = [
        "统计浙江省有多少个5A景区",
        "西湖的详细介绍",
        "查询杭州市的景区"
    ]
    for query in test_queries:
        qtype = generator._detect_query_type(query)
        print(f"Query: {query}")
        print(f"Type: {qtype}\n")
