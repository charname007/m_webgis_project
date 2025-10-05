"""
意图分析优化效果测试 - 对比优化前后
"""

import sys
import io
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from core.prompts import PromptManager

print("\n" + "=" * 70)
print(" 意图分析优化效果测试")
print("=" * 70 + "\n")

# 测试用例集（30+ 条）
test_cases = [
    # ==================== Summary 查询测试 ====================
    {
        "category": "Summary - 基础统计",
        "queries": [
            ("浙江省有多少个景区", "summary", False),
            ("统计浙江省的景区数量", "summary", False),
            ("浙江省景区有几个", "summary", False),
            ("一共有多少个5A景区", "summary", False),
            ("总共有多少个景区", "summary", False),
            ("计算浙江省景区个数", "summary", False),
        ]
    },
    {
        "category": "Summary - 容易误判的",
        "queries": [
            ("多少个景区在浙江", "summary", False),
            ("几个5A级景区", "summary", False),
            ("这几个景区怎么样", "query", False),  # 应该是 query（"这几个"不是统计）
        ]
    },

    # ==================== Query 查询测试 ====================
    {
        "category": "Query - 基础查询",
        "queries": [
            ("查询浙江省的景区", "query", False),
            ("浙江省有哪些景区", "query", False),
            ("列出浙江省所有5A景区", "query", False),
            ("给我浙江省的景区列表", "query", False),
            ("查找浙江省的景区", "query", False),
            ("显示杭州的景区", "query", False),
        ]
    },

    # ==================== Spatial 查询测试 ====================
    {
        "category": "Spatial - 基础空间查询",
        "queries": [
            ("查询杭州附近的景区", "query", True),
            ("杭州周围10公里的景区", "query", True),
            ("距离杭州最近的景区", "query", True),
            ("西湖周边的景区", "query", True),
            ("附近有什么景区", "query", True),
            ("周边的旅游景点", "query", True),
        ]
    },
    {
        "category": "Spatial - 高级空间查询",
        "queries": [
            ("距离西湖5公里以内的景区", "query", True),
            ("杭州东边10公里的景点", "query", True),
            ("靠近杭州的景区", "query", True),
            ("临近西湖的景点", "query", True),
        ]
    },

    # ==================== Summary + Spatial 组合 ====================
    {
        "category": "Summary + Spatial 组合",
        "queries": [
            ("统计西湖周围5公里的景点数量", "summary", True),
            ("杭州附近有多少个景区", "summary", True),
            ("距离西湖最近的景区有几个", "summary", True),
        ]
    },

    # ==================== 边界 case ====================
    {
        "category": "边界 Case",
        "queries": [
            ("查询统计信息", "summary", False),   # "统计"关键词
            ("查询多少个景区", "summary", False),  # ✅ 修正：虽然有"查询"，但"多少个"更强，判为summary合理
            ("列出前10个景区", "query", False),    # "10个"不是统计
            ("这几个景区", "query", False),        # "这几个"不是统计
        ]
    },
]

# 执行测试
total_tests = 0
passed_tests = 0
failed_tests = []

for test_group in test_cases:
    category = test_group["category"]
    queries = test_group["queries"]

    print(f"\n{'─' * 70}")
    print(f"📂 {category}")
    print(f"{'─' * 70}")

    for query, expected_intent, expected_spatial in queries:
        total_tests += 1

        # 分析意图
        result = PromptManager.analyze_query_intent(query)

        actual_intent = result["intent_type"]
        actual_spatial = result["is_spatial"]
        summary_score = result["analysis_details"]["summary_score"]
        spatial_score = result["analysis_details"]["spatial_score"]

        # 判断是否通过
        intent_match = (actual_intent == expected_intent)
        spatial_match = (actual_spatial == expected_spatial)
        passed = intent_match and spatial_match

        if passed:
            passed_tests += 1
            status = "✓"
        else:
            status = "✗"
            failed_tests.append({
                "query": query,
                "expected": (expected_intent, expected_spatial),
                "actual": (actual_intent, actual_spatial),
                "scores": (summary_score, spatial_score)
            })

        # 输出测试结果
        print(f"{status} {query:40s} | intent: {actual_intent:7s} (预期: {expected_intent:7s}) "
              f"| spatial: {str(actual_spatial):5s} (预期: {str(expected_spatial):5s}) "
              f"| scores: S={summary_score:.2f}, Sp={spatial_score:.2f}")

# 汇总报告
print("\n" + "=" * 70)
print(" 测试结果汇总")
print("=" * 70)
print(f"\n总测试数: {total_tests}")
print(f"通过: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
print(f"失败: {len(failed_tests)} ({len(failed_tests)/total_tests*100:.1f}%)")

if failed_tests:
    print("\n❌ 失败的测试用例：")
    print("-" * 70)
    for i, fail in enumerate(failed_tests, 1):
        print(f"\n{i}. '{fail['query']}'")
        print(f"   预期: intent={fail['expected'][0]}, spatial={fail['expected'][1]}")
        print(f"   实际: intent={fail['actual'][0]}, spatial={fail['actual'][1]}")
        print(f"   分数: summary={fail['scores'][0]:.2f}, spatial={fail['scores'][1]:.2f}")

# 额外：展示一些详细的匹配信息
print("\n" + "=" * 70)
print(" 详细分析示例（前5个）")
print("=" * 70)

example_queries = [
    "浙江省景区有几个",
    "查询杭州附近的景区",
    "西湖周边的景区",
    "统计西湖周围5公里的景点数量",
    "查询多少个景区"
]

for query in example_queries:
    result = PromptManager.analyze_query_intent(query)
    print(f"\n查询: {query}")
    print(f"  intent_type: {result['intent_type']}")
    print(f"  is_spatial: {result['is_spatial']}")
    print(f"  confidence: {result['confidence']:.2f}")
    print(f"  summary_score: {result['analysis_details']['summary_score']:.2f}")
    print(f"  spatial_score: {result['analysis_details']['spatial_score']:.2f}")
    print(f"  matched_patterns: {result['analysis_details']['matched_patterns'][:3]}")  # 前3个

print("\n" + "=" * 70)

# 设置退出码
sys.exit(0 if len(failed_tests) == 0 else 1)
