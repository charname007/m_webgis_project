#!/usr/bin/env python3
"""
测试查询意图分析系统的准确度
验证新的多维度特征分析算法
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

from sight_server.core.prompts import PromptManager

def test_intent_analysis():
    """测试意图分析系统"""
    print("=== 查询意图分析系统测试 ===\n")
    
    # 测试用例集合
    test_cases = [
        # 统计查询测试
        {
            "query": "统计浙江省有多少个5A景区",
            "expected_intent": "summary",
            "expected_spatial": False,
            "description": "明确统计查询"
        },
        {
            "query": "查询浙江省5A景区的数量",
            "expected_intent": "summary", 
            "expected_spatial": False,
            "description": "数量查询"
        },
        {
            "query": "浙江省4A景区有多少个",
            "expected_intent": "summary",
            "expected_spatial": False,
            "description": "有多少个模式"
        },
        {
            "query": "统计西湖周围5公里的景点分布",
            "expected_intent": "summary",
            "expected_spatial": True,
            "description": "空间统计查询"
        },
        
        # 空间查询测试
        {
            "query": "查找距离杭州10公里内的景点",
            "expected_intent": "query",
            "expected_spatial": True,
            "description": "距离查询"
        },
        {
            "query": "查询西湖附近的景区",
            "expected_intent": "query",
            "expected_spatial": True,
            "description": "附近查询"
        },
        {
            "query": "查找杭州市周围的5A景区",
            "expected_intent": "query",
            "expected_spatial": True,
            "description": "周围查询"
        },
        {
            "query": "查询经纬度120.15,30.28周围5公里的景点",
            "expected_intent": "query",
            "expected_spatial": True,
            "description": "坐标距离查询"
        },
        
        # 普通查询测试
        {
            "query": "查询浙江省的5A景区",
            "expected_intent": "query",
            "expected_spatial": False,
            "description": "普通景区查询"
        },
        {
            "query": "列出杭州市的所有景区",
            "expected_intent": "query",
            "expected_spatial": False,
            "description": "列表查询"
        },
        {
            "query": "查找西湖的详细信息",
            "expected_intent": "query",
            "expected_spatial": False,
            "description": "详情查询"
        },
        
        # 边界情况测试
        {
            "query": "浙江省景区",
            "expected_intent": "query",
            "expected_spatial": False,
            "description": "简单查询"
        },
        {
            "query": "有多少个",
            "expected_intent": "summary",
            "expected_spatial": False,
            "description": "模糊统计查询"
        },
        {
            "query": "附近景点",
            "expected_intent": "query",
            "expected_spatial": True,
            "description": "模糊空间查询"
        }
    ]
    
    # 运行测试
    total_cases = len(test_cases)
    correct_intent = 0
    correct_spatial = 0
    
    print("测试结果:\n")
    print("=" * 120)
    print(f"{'查询':<30} {'预期意图':<12} {'实际意图':<12} {'意图正确':<8} {'预期空间':<10} {'实际空间':<10} {'空间正确':<8} {'置信度':<8} {'描述':<20}")
    print("=" * 120)
    
    for test_case in test_cases:
        query = test_case["query"]
        expected_intent = test_case["expected_intent"]
        expected_spatial = test_case["expected_spatial"]
        
        # 分析意图
        result = PromptManager.analyze_query_intent(query)
        
        actual_intent = result["intent_type"]
        actual_spatial = result["is_spatial"]
        confidence = result["confidence"]
        
        # 检查正确性
        intent_correct = (actual_intent == expected_intent)
        spatial_correct = (actual_spatial == expected_spatial)
        
        if intent_correct:
            correct_intent += 1
        if spatial_correct:
            correct_spatial += 1
        
        # 输出结果
        print(f"{query:<30} {expected_intent:<12} {actual_intent:<12} {str(intent_correct):<8} {str(expected_spatial):<10} {str(actual_spatial):<10} {str(spatial_correct):<8} {confidence:.2f}     {test_case['description']:<20}")
        
        # 如果分析错误，显示详细分析信息
        if not intent_correct or not spatial_correct:
            print(f"  ⚠️ 详细分析: {result['description']}")
            print(f"  📊 分析详情: {result['analysis_details']}")
    
    print("=" * 120)
    
    # 计算准确率
    intent_accuracy = correct_intent / total_cases * 100
    spatial_accuracy = correct_spatial / total_cases * 100
    overall_accuracy = (correct_intent + correct_spatial) / (total_cases * 2) * 100
    
    print(f"\n测试总结:")
    print(f"总测试用例: {total_cases}")
    print(f"意图分析准确率: {intent_accuracy:.1f}% ({correct_intent}/{total_cases})")
    print(f"空间分析准确率: {spatial_accuracy:.1f}% ({correct_spatial}/{total_cases})")
    print(f"总体准确率: {overall_accuracy:.1f}%")
    
    # 性能评估
    if overall_accuracy >= 90:
        print("✅ 意图分析系统性能优秀！")
    elif overall_accuracy >= 80:
        print("✅ 意图分析系统性能良好！")
    elif overall_accuracy >= 70:
        print("⚠️ 意图分析系统性能一般，需要优化")
    else:
        print("❌ 意图分析系统性能较差，需要大幅优化")
    
    return overall_accuracy >= 80

def test_analysis_details():
    """测试详细分析功能"""
    print("\n=== 详细分析功能测试 ===\n")
    
    complex_queries = [
        "统计浙江省5A景区数量并分析分布情况",
        "查找距离西湖5公里内评分4.5以上的景点",
        "查询杭州市4A景区的平均门票价格",
        "统计西湖周围10公里内景点的数量分布"
    ]
    
    for query in complex_queries:
        print(f"查询: {query}")
        result = PromptManager.analyze_query_intent(query)
        
        print(f"  意图类型: {result['intent_type']}")
        print(f"  空间查询: {result['is_spatial']}")
        print(f"  置信度: {result['confidence']:.2f}")
        print(f"  描述: {result['description']}")
        
        details = result['analysis_details']
        print(f"  分析详情:")
        print(f"    - 统计分数: {details['summary_score']:.2f}")
        print(f"    - 空间分数: {details['spatial_score']:.2f}")
        print(f"    - 景区分数: {details['scenic_score']:.2f}")
        print(f"    - 匹配模式: {details['matched_patterns'][:3]}")  # 只显示前3个
        print()

if __name__ == "__main__":
    # 运行主要测试
    success = test_intent_analysis()
    
    # 运行详细分析测试
    test_analysis_details()
    
    sys.exit(0 if success else 1)
