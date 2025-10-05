#!/usr/bin/env python3
"""
独立测试查询意图分析系统
避免依赖问题，直接测试核心功能
"""

import re
from typing import Dict, Any, List

# 复制核心分析逻辑到独立脚本中
class SimpleIntentAnalyzer:
    """简化的意图分析器"""
    
    def __init__(self):
        # 空间查询关键词
        self.spatial_keywords = [
            '距离', '附近', '周围', '范围内', '最近', '路径', '路线',
            '相交', '包含', '在内', '边界', '缓冲', '缓冲区',
            'distance', 'near', 'nearby', 'around', 'within',
            'route', 'path', 'nearest', 'proximity', 'intersect',
            'contain', 'buffer', 'st_', 'dwithin'
        ]
        
        # 总结/统计类查询关键词
        self.summary_keywords = [
            '统计', '总结', '汇总', '多少', '数量', '分布',
            '平均', '最多', '最少', '排名', '总数', '计数',
            '有几个', '有多少', '几个', '分析',
            'count', 'sum', 'average', 'max', 'min', 'total',
            'statistics', 'summary', 'analyze', 'how many'
        ]

    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        智能分析查询意图（基于多维度特征分析）
        """
        query_lower = query.lower()
        
        # 初始化分析结果
        analysis_details = {
            "summary_score": 0.0,
            "spatial_score": 0.0,
            "scenic_score": 0.0,
            "matched_patterns": []
        }

        # ==================== 统计意图分析 ====================
        summary_score = 0.0
        
        # 强统计关键词（权重高）
        strong_summary_keywords = ['统计', '计数', '数量', '多少个', 'count', 'how many', '总数', '总计']
        for keyword in strong_summary_keywords:
            if keyword in query_lower:
                summary_score += 0.3
                analysis_details["matched_patterns"].append(f"强统计关键词: {keyword}")
        
        # 弱统计关键词（权重中）
        weak_summary_keywords = ['汇总', '总结', '分布', '平均', '最多', '最少', 'sum', 'average', 'max', 'min']
        for keyword in weak_summary_keywords:
            if keyword in query_lower:
                summary_score += 0.15
                analysis_details["matched_patterns"].append(f"弱统计关键词: {keyword}")
        
        # 统计模式识别
        summary_patterns = [
            (r'有多少个?', 0.4),
            (r'几个', 0.3),
            (r'(\d+)个', 0.2),
            (r'排名', 0.25),
            (r'分布情况', 0.3)
        ]
        
        for pattern, weight in summary_patterns:
            if re.search(pattern, query_lower):
                summary_score += weight
                analysis_details["matched_patterns"].append(f"统计模式: {pattern}")
        
        analysis_details["summary_score"] = min(summary_score, 1.0)

        # ==================== 空间意图分析 ====================
        spatial_score = 0.0
        
        # 强空间关键词（权重高）
        strong_spatial_keywords = ['距离', '附近', '周围', '范围内', '最近', 'dwithin', 'st_', 'buffer']
        for keyword in strong_spatial_keywords:
            if keyword in query_lower:
                spatial_score += 0.25
                analysis_details["matched_patterns"].append(f"强空间关键词: {keyword}")
        
        # 弱空间关键词（权重中）
        weak_spatial_keywords = ['路径', '路线', '相交', '包含', '边界', '缓冲', 'near', 'around', 'within']
        for keyword in weak_spatial_keywords:
            if keyword in query_lower:
                spatial_score += 0.1
                analysis_details["matched_patterns"].append(f"弱空间关键词: {keyword}")
        
        # 空间模式识别
        spatial_patterns = [
            (r'距离.*[公里|千米|米]', 0.4),
            (r'附近.*[公里|千米|米]', 0.35),
            (r'周围.*[公里|千米|米]', 0.35),
            (r'范围内.*[公里|千米|米]', 0.3),
            (r'经纬度', 0.25),
            (r'坐标', 0.2)
        ]
        
        for pattern, weight in spatial_patterns:
            if re.search(pattern, query_lower):
                spatial_score += weight
                analysis_details["matched_patterns"].append(f"空间模式: {pattern}")
        
        analysis_details["spatial_score"] = min(spatial_score, 1.0)

        # ==================== 景区意图分析 ====================
        scenic_score = 0.0
        
        # 景区相关关键词
        scenic_keywords = ['景区', '景点', '旅游', '5a', '4a', '3a', '2a', '1a', 'scenic', 'tourist', 'spot']
        for keyword in scenic_keywords:
            if keyword in query_lower:
                scenic_score += 0.1
                analysis_details["matched_patterns"].append(f"景区关键词: {keyword}")
        
        # 景区等级模式
        level_patterns = [
            (r'[54321]a景区', 0.3),
            (r'[54321]a级', 0.3),
            (r'[54321]a景点', 0.3)
        ]
        
        for pattern, weight in level_patterns:
            if re.search(pattern, query_lower):
                scenic_score += weight
                analysis_details["matched_patterns"].append(f"景区等级模式: {pattern}")
        
        analysis_details["scenic_score"] = min(scenic_score, 1.0)

        # ==================== 意图决策 ====================
        
        # 确定意图类型（基于分数阈值）
        is_summary = analysis_details["summary_score"] >= 0.4
        is_spatial = analysis_details["spatial_score"] >= 0.3
        
        # 确定意图类型
        intent_type = "summary" if is_summary else "query"
        
        # 计算总体置信度
        confidence = max(
            analysis_details["summary_score"],
            analysis_details["spatial_score"],
            analysis_details["scenic_score"]
        )
        
        # 构建描述
        description_parts = []
        if is_summary:
            description_parts.append(f"统计汇总查询(置信度:{analysis_details['summary_score']:.2f})")
        else:
            description_parts.append(f"数据查询")
        
        if is_spatial:
            description_parts.append(f"空间查询(置信度:{analysis_details['spatial_score']:.2f})")
        
        if scenic_score > 0.2:
            description_parts.append(f"景区查询(置信度:{analysis_details['scenic_score']:.2f})")
        
        description = " - ".join(description_parts)

        # 收集匹配的关键词
        spatial_matched = [kw for kw in self.spatial_keywords if kw in query_lower]
        summary_matched = [kw for kw in self.summary_keywords if kw in query_lower]

        return {
            "intent_type": intent_type,
            "is_spatial": is_spatial,
            "keywords_matched": spatial_matched + summary_matched,
            "description": description,
            "confidence": confidence,
            "analysis_details": analysis_details
        }

def test_intent_analysis():
    """测试意图分析系统"""
    print("=== 查询意图分析系统测试 ===\n")
    
    analyzer = SimpleIntentAnalyzer()
    
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
        result = analyzer.analyze_query_intent(query)
        
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

if __name__ == "__main__":
    # 运行测试
    success = test_intent_analysis()
    
    exit(0 if success else 1)
