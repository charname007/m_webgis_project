"""
LLM + Pydantic 意图分析测试 - Sight Server
测试使用 LLM 进行查询意图分析的准确性和稳定性
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from typing import List, Dict, Any
from core.llm import BaseLLM
from core.processors.intent_analyzer import IntentAnalyzer
from core.prompts import PromptManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestCase:
    """测试用例定义"""

    def __init__(
        self,
        query: str,
        expected_intent_type: str,
        expected_is_spatial: bool,
        description: str = ""
    ):
        self.query = query
        self.expected_intent_type = expected_intent_type
        self.expected_is_spatial = expected_is_spatial
        self.description = description or query


def run_test_suite():
    """运行完整测试套件"""

    # ==================== 初始化 LLM 和分析器 ====================
    print("\n" + "=" * 80)
    print("LLM + Pydantic 意图分析测试")
    print("=" * 80)

    try:
        llm = BaseLLM(temperature=0.0)  # 使用温度0以确保稳定性
        analyzer = IntentAnalyzer(llm)
        print("✅ LLM 和 IntentAnalyzer 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # ==================== 定义测试用例 ====================

    test_cases: List[TestCase] = [
        # Summary 类型（统计、数量）
        TestCase("浙江省有多少个5A景区", "summary", False, "Summary - 数量统计"),
        TestCase("统计浙江省的5A景区数量", "summary", False, "Summary - 统计关键词"),
        TestCase("浙江省一共有几个5A景区", "summary", False, "Summary - 一共...几个"),
        TestCase("统计各省份的5A景区分布", "summary", False, "Summary - 分布统计"),
        TestCase("浙江省和江苏省景区数量对比", "summary", False, "Summary - 对比数量"),

        # Query 类型（列表、详情）
        TestCase("查询浙江省的5A景区", "query", False, "Query - 基础查询"),
        TestCase("列出杭州市的景区", "query", False, "Query - 列出"),
        TestCase("显示西湖的详细信息", "query", False, "Query - 显示详情"),
        TestCase("推荐几个杭州的景区", "query", False, "Query - 推荐"),
        TestCase("浙江省有哪些5A景区", "query", False, "Query - 哪些"),

        # Spatial 类型（空间查询）
        TestCase("杭州附近10公里的景区", "query", True, "Spatial Query - 附近+距离"),
        TestCase("西湖周边的景区", "query", True, "Spatial Query - 周边"),
        TestCase("距离杭州最近的5A景区", "query", True, "Spatial Query - 最近"),
        TestCase("查找临近西湖的景点", "query", True, "Spatial Query - 临近"),

        # Summary + Spatial 组合
        TestCase("统计杭州附近50公里内的景区数量", "summary", True, "Summary + Spatial"),
        TestCase("西湖周边有多少个景区", "summary", True, "Summary + Spatial - 周边数量"),

        # 边界 Case（容易误判）
        TestCase("这几个景区的详细信息", "query", False, "Edge - 这几个（排除）"),
        TestCase("前10个热门景区", "query", False, "Edge - 前10个（排序）"),
        TestCase("景区分布在哪些城市", "query", False, "Edge - 分布地点（非统计）"),
    ]

    # ==================== 执行测试 ====================

    passed = 0
    failed = 0
    results: List[Dict[str, Any]] = []

    print(f"\n开始测试 {len(test_cases)} 个用例...\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"测试 {i}/{len(test_cases)}: {test_case.description}")
        print(f"查询: \"{test_case.query}\"")
        print(f"预期: intent_type={test_case.expected_intent_type}, is_spatial={test_case.expected_is_spatial}")

        try:
            # 使用 LLM 分析意图
            result = analyzer.analyze_intent(test_case.query)

            # 检查结果
            intent_type = result["intent_type"]
            is_spatial = result["is_spatial"]
            confidence = result["confidence"]
            reasoning = result["reasoning"]

            # 判断是否通过
            intent_match = (intent_type == test_case.expected_intent_type)
            spatial_match = (is_spatial == test_case.expected_is_spatial)
            test_passed = intent_match and spatial_match

            # 记录结果
            results.append({
                "query": test_case.query,
                "description": test_case.description,
                "expected_intent": test_case.expected_intent_type,
                "actual_intent": intent_type,
                "expected_spatial": test_case.expected_is_spatial,
                "actual_spatial": is_spatial,
                "confidence": confidence,
                "reasoning": reasoning,
                "passed": test_passed
            })

            if test_passed:
                passed += 1
                print(f"✅ 通过")
            else:
                failed += 1
                print(f"❌ 失败")

            print(f"实际: intent_type={intent_type}, is_spatial={is_spatial}, confidence={confidence:.2f}")
            print(f"推理: {reasoning}")

        except Exception as e:
            failed += 1
            print(f"❌ 错误: {e}")
            results.append({
                "query": test_case.query,
                "description": test_case.description,
                "error": str(e),
                "passed": False
            })

    # ==================== 输出测试报告 ====================

    print(f"\n{'=' * 80}")
    print("测试报告")
    print(f"{'=' * 80}")
    print(f"\n总计: {len(test_cases)} 个测试")
    print(f"✅ 通过: {passed} ({passed/len(test_cases)*100:.1f}%)")
    print(f"❌ 失败: {failed} ({failed/len(test_cases)*100:.1f}%)")

    # 按类别统计
    print("\n按类别统计:")
    categories = {}
    for result in results:
        desc = result["description"]
        category = desc.split(" - ")[0]
        if category not in categories:
            categories[category] = {"passed": 0, "total": 0}
        categories[category]["total"] += 1
        if result.get("passed", False):
            categories[category]["passed"] += 1

    for category, stats in categories.items():
        total = stats["total"]
        passed_count = stats["passed"]
        rate = passed_count / total * 100 if total > 0 else 0
        print(f"  {category}: {passed_count}/{total} ({rate:.1f}%)")

    # 失败案例详情
    if failed > 0:
        print(f"\n{'─' * 80}")
        print("失败案例详情:")
        print(f"{'─' * 80}")
        for result in results:
            if not result.get("passed", False):
                print(f"\n❌ {result['description']}")
                print(f"   查询: {result['query']}")
                if "error" in result:
                    print(f"   错误: {result['error']}")
                else:
                    print(f"   预期: intent={result['expected_intent']}, spatial={result['expected_spatial']}")
                    print(f"   实际: intent={result['actual_intent']}, spatial={result['actual_spatial']}")
                    print(f"   推理: {result['reasoning']}")

    # ==================== 对比 LLM vs 关键词分析 ====================

    print(f"\n{'=' * 80}")
    print("LLM vs 关键词分析对比")
    print(f"{'=' * 80}")

    # 选择5个代表性案例进行对比
    compare_cases = [
        test_cases[0],  # "浙江省有多少个5A景区"
        test_cases[5],  # "查询浙江省的5A景区"
        test_cases[10],  # "杭州附近10公里的景区"
        test_cases[16],  # "这几个景区的详细信息"
        test_cases[18],  # "景区分布在哪些城市"
    ]

    print("\n对比案例（5个代表性查询）:\n")

    for test_case in compare_cases:
        print(f"{'─' * 80}")
        print(f"查询: \"{test_case.query}\"")
        print(f"预期: intent_type={test_case.expected_intent_type}, is_spatial={test_case.expected_is_spatial}")

        # LLM 分析
        llm_result = analyzer.analyze_intent(test_case.query)

        # 关键词分析
        keyword_result = PromptManager._analyze_intent_by_keywords(test_case.query)

        # LLM 结果
        print(f"\n📊 LLM 分析:")
        print(f"   intent_type={llm_result['intent_type']}, is_spatial={llm_result['is_spatial']}, confidence={llm_result['confidence']:.2f}")
        print(f"   推理: {llm_result['reasoning']}")

        # 关键词结果
        print(f"\n🔤 关键词分析:")
        print(f"   intent_type={keyword_result['intent_type']}, is_spatial={keyword_result['is_spatial']}, confidence={keyword_result['confidence']:.2f}")
        print(f"   推理: {keyword_result['reasoning']}")

        # 对比
        llm_correct = (
            llm_result['intent_type'] == test_case.expected_intent_type and
            llm_result['is_spatial'] == test_case.expected_is_spatial
        )
        keyword_correct = (
            keyword_result['intent_type'] == test_case.expected_intent_type and
            keyword_result['is_spatial'] == test_case.expected_is_spatial
        )

        print(f"\n✅ LLM: {'正确' if llm_correct else '错误'}")
        print(f"✅ 关键词: {'正确' if keyword_correct else '错误'}")

        if llm_correct and not keyword_correct:
            print("💡 LLM 优势: 语义理解更准确")
        elif keyword_correct and not llm_correct:
            print("⚠️ 关键词优势: LLM 判断有误")
        elif llm_correct and keyword_correct:
            print("👍 两者均正确")
        else:
            print("⚠️ 两者均错误")

    print(f"\n{'=' * 80}")
    print("测试完成")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    run_test_suite()
