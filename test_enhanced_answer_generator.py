"""
测试增强答案生成器和结果验证功能
"""

import logging
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

from sight_server.core.processors.enhanced_answer_generator import EnhancedAnswerGenerator
from sight_server.core.graph.nodes import AgentNodes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_enhanced_answer_generator():
    """测试增强答案生成器"""
    print("=== 测试增强答案生成器 ===\n")
    
    # 模拟LLM
    class MockLLM:
        def __init__(self):
            self.llm = self

        def invoke(self, prompt):
            if "深度分析" in prompt:
                return "这是一个模拟的深度分析回答，包含数据洞察、统计解读和业务建议。"
            elif "统计" in prompt:
                return "这是一个模拟的统计分析回答，包含统计意义解读和业务洞察。"
            else:
                return "这是一个模拟的验证结果，结果质量良好。"

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

def test_validation_node():
    """测试结果验证节点"""
    print("=== 测试结果验证节点 ===\n")
    
    # 模拟组件
    class MockComponents:
        def __init__(self):
            self.llm = MockLLM()
            self.logger = logging.getLogger(__name__)

    # 创建节点
    nodes = AgentNodes(
        sql_generator=None,
        sql_executor=None,
        result_parser=None,
        answer_generator=None,
        schema_fetcher=None,
        llm=MockLLM()
    )

    # 测试状态
    test_state = {
        "query": "查询浙江省的5A景区",
        "final_data": [
            {"name": "西湖", "level": "5A", "评分": "4.8", "门票": "免费"},
            {"name": "千岛湖", "level": "5A", "评分": "4.6", "门票": "150元"}
        ],
        "query_intent": "query",
        "current_step": 0
    }

    # 测试验证方法
    print("--- 测试验证方法 ---")
    validation_result = nodes._validate_with_llm(
        query="查询浙江省的5A景区",
        data=test_state["final_data"],
        count=2,
        query_intent="query"
    )
    print(f"Validation Result: {validation_result}\n")

    # 测试验证节点
    print("--- 测试验证节点 ---")
    node_result = nodes.validate_results(test_state)
    print(f"Node Result: {node_result}\n")

def test_enhanced_answer_node():
    """测试增强答案节点"""
    print("=== 测试增强答案节点 ===\n")
    
    # 模拟组件
    class MockComponents:
        def __init__(self):
            self.llm = MockLLM()
            self.logger = logging.getLogger(__name__)

    # 创建节点
    nodes = AgentNodes(
        sql_generator=None,
        sql_executor=None,
        result_parser=None,
        answer_generator=None,
        schema_fetcher=None,
        llm=MockLLM()
    )

    # 测试状态
    test_state = {
        "query": "查询浙江省的5A景区",
        "final_data": [
            {"name": "西湖", "level": "5A", "评分": "4.8", "门票": "免费"},
            {"name": "千岛湖", "level": "5A", "评分": "4.6", "门票": "150元"}
        ],
        "query_intent": "query",
        "requires_spatial": False,
        "current_step": 0
    }

    # 测试增强答案节点
    print("--- 测试增强答案节点 ---")
    node_result = nodes.generate_answer(test_state)
    print(f"Node Result: {node_result}\n")

if __name__ == "__main__":
    print("开始测试增强答案生成器和结果验证功能...\n")
    
    try:
        test_enhanced_answer_generator()
        test_validation_node()
        test_enhanced_answer_node()
        
        print("✓ 所有测试完成！")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
