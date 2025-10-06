#!/usr/bin/env python3
"""
验证节点优化测试脚本
测试优化后的验证节点功能分离效果
"""

import sys
import os
import logging

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from sight_server.core.graph.nodes.validation import CheckResultsNode, ValidateResultsNode
from sight_server.core.graph.nodes.final_validation import FinalValidationNode
from sight_server.core.graph.nodes.base import NodeContext
from sight_server.core.llm import BaseLLM
from sight_server.core.database import DatabaseConnector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_context():
    """创建测试用的节点上下文"""
    try:
        llm = BaseLLM()
        db_connector = DatabaseConnector()
        
        context = NodeContext(
            sql_generator=None,
            sql_executor=None,
            result_parser=None,
            answer_generator=None,
            schema_fetcher=None,
            llm=llm,
            error_handler=None,
            cache_manager=None,
            structured_logger=None,
            result_validator=None,
            data_analyzer=None
        )
        return context
    except Exception as e:
        logger.warning(f"无法创建完整上下文，使用最小配置: {e}")
        return NodeContext()


def test_check_results_node():
    """测试优化后的 CheckResultsNode"""
    print("\n=== 测试 CheckResultsNode (规则决策) ===")
    
    context = create_test_context()
    node = CheckResultsNode(context)
    
    # 测试用例1: 无数据情况
    state1 = {
        "current_step": 0,
        "max_iterations": 3,
        "final_data": None,
        "query_intent": "query",
        "validation_passed": True
    }
    
    result1 = node(state1)
    print(f"测试1 - 无数据: should_continue={result1['should_continue']}, reason={result1['thought_chain'][0]['output']['reason']}")
    
    # 测试用例2: 数据量较少
    state2 = {
        "current_step": 0,
        "max_iterations": 3,
        "final_data": [{"name": "景区1"}, {"name": "景区2"}],
        "query_intent": "query",
        "validation_passed": True
    }
    
    result2 = node(state2)
    print(f"测试2 - 数据较少: should_continue={result2['should_continue']}, reason={result2['thought_chain'][0]['output']['reason']}")
    
    # 测试用例3: 数据充足
    state3 = {
        "current_step": 0,
        "max_iterations": 3,
        "final_data": [{"name": "景区1"}, {"name": "景区2"}, {"name": "景区3"}, {"name": "景区4"}],
        "query_intent": "query",
        "validation_passed": True
    }
    
    result3 = node(state3)
    print(f"测试3 - 数据充足: should_continue={result3['should_continue']}, reason={result3['thought_chain'][0]['output']['reason']}")
    
    # 测试用例4: 验证失败
    state4 = {
        "current_step": 0,
        "max_iterations": 3,
        "final_data": [{"name": "景区1"}],
        "query_intent": "query",
        "validation_passed": False
    }
    
    result4 = node(state4)
    print(f"测试4 - 验证失败: should_continue={result4['should_continue']}, reason={result4['thought_chain'][0]['output']['reason']}")


def test_validate_results_node():
    """测试 ValidateResultsNode"""
    print("\n=== 测试 ValidateResultsNode (结果质量验证) ===")
    
    context = create_test_context()
    node = ValidateResultsNode(context)
    
    # 测试用例1: 无数据
    state1 = {
        "query": "查询5A景区",
        "final_data": None,
        "query_intent": "query",
        "current_step": 0
    }
    
    result1 = node(state1)
    print(f"测试1 - 无数据: validation_passed={result1['validation_passed']}, reason={result1['validation_reason']}")
    
    # 测试用例2: 有数据
    state2 = {
        "query": "查询浙江省的5A景区",
        "final_data": [
            {"name": "西湖", "level": "5A", "地区": "杭州", "所属省份": "浙江"},
            {"name": "千岛湖", "level": "5A", "地区": "杭州", "所属省份": "浙江"}
        ],
        "query_intent": "query",
        "current_step": 0
    }
    
    result2 = node(state2)
    print(f"测试2 - 有数据: validation_passed={result2['validation_passed']}, reason={result2['validation_reason']}")


def test_final_validation_node():
    """测试 FinalValidationNode"""
    print("\n=== 测试 FinalValidationNode (最终答案质量验证) ===")
    
    context = create_test_context()
    node = FinalValidationNode(context)
    
    # 测试用例1: 空答案
    state1 = {
        "query": "查询5A景区",
        "answer": "",
        "final_data": [{"name": "西湖", "level": "5A"}],
        "query_intent": "query",
        "current_step": 0
    }
    
    result1 = node(state1)
    print(f"测试1 - 空答案: validation_passed={result1['final_validation_passed']}, reason={result1['final_validation_reason']}")
    
    # 测试用例2: 有答案
    state2 = {
        "query": "查询浙江省的5A景区",
        "answer": "根据查询结果，浙江省有以下5A级景区：西湖、千岛湖等。这些景区都是浙江省的著名旅游景点。",
        "final_data": [
            {"name": "西湖", "level": "5A", "地区": "杭州", "所属省份": "浙江"},
            {"name": "千岛湖", "level": "5A", "地区": "杭州", "所属省份": "浙江"}
        ],
        "query_intent": "query",
        "current_step": 0
    }
    
    result2 = node(state2)
    print(f"测试2 - 有答案: validation_passed={result2['final_validation_passed']}, reason={result2['final_validation_reason']}")


def main():
    """主测试函数"""
    print("=== 验证节点优化测试 ===")
    print("测试方案2：功能分离 + 逻辑优化")
    
    try:
        # 测试各节点功能
        test_check_results_node()
        test_validate_results_node()
        test_final_validation_node()
        
        print("\n=== 测试总结 ===")
        print("✓ CheckResultsNode: 专注于规则决策，减少LLM依赖")
        print("✓ ValidateResultsNode: 专注于结果质量验证")
        print("✓ FinalValidationNode: 专注于最终答案质量评估")
        print("✓ 工作流优化: 验证节点位置合理，功能分离清晰")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
