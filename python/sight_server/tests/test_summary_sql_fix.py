"""
测试 Summary SQL 自动修复功能
验证当 LLM 错误生成 json_agg 时能否自动修复为 COUNT
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from core.llm import BaseLLM
from core.processors.sql_generator import SQLGenerator
from core.prompts import PromptManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_summary_sql_auto_fix():
    """测试 Summary SQL 自动修复功能"""

    print("\n" + "=" * 80)
    print("Summary SQL 自动修复测试")
    print("=" * 80)

    # 初始化
    llm = BaseLLM(temperature=0.0)
    base_prompt = PromptManager.get_scenic_query_prompt()
    generator = SQLGenerator(llm, base_prompt)

    # 测试用例
    test_queries = [
        {
            "query": "浙江省有多少个5A景区",
            "expected_pattern": r"SELECT\s+COUNT\(\*\)\s+as\s+count",
            "should_not_contain": ["json_agg", "json_build_object"],
            "description": "基础统计查询"
        },
        {
            "query": "统计各省份的5A景区数量",
            "expected_pattern": r"GROUP\s+BY",
            "should_not_contain": ["json_agg", "json_build_object"],
            "description": "分组统计查询"
        },
        {
            "query": "杭州附近50公里内有多少个景区",
            "expected_pattern": r"SELECT\s+COUNT\(\*\)\s+as\s+count",
            "should_not_contain": ["json_agg"],
            "description": "空间统计查询"
        }
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'─' * 80}")
        print(f"测试 {i}/{len(test_queries)}: {test_case['description']}")
        print(f"查询: \"{test_case['query']}\"")

        try:
            # 1. 分析意图
            intent_info = PromptManager.analyze_query_intent(
                test_case['query'],
                llm=llm,
                use_llm_analysis=True
            )

            print(f"\n意图分析:")
            print(f"  - intent_type: {intent_info['intent_type']}")
            print(f"  - is_spatial: {intent_info['is_spatial']}")
            print(f"  - confidence: {intent_info['confidence']:.2f}")

            # 2. 生成 SQL
            sql = generator.generate_initial_sql(
                test_case['query'],
                intent_info=intent_info,
                database_schema="(测试模式，无Schema)"
            )

            print(f"\n生成的 SQL:")
            print(sql)

            # 3. 验证 SQL
            import re

            # 检查是否包含预期模式
            pattern_match = re.search(test_case['expected_pattern'], sql, re.IGNORECASE)

            # 检查是否包含禁止内容
            forbidden_found = []
            for forbidden in test_case['should_not_contain']:
                if forbidden.lower() in sql.lower():
                    forbidden_found.append(forbidden)

            # 判断测试是否通过
            test_passed = pattern_match and not forbidden_found

            if test_passed:
                passed += 1
                print(f"\n[PASS] Test passed")
            else:
                failed += 1
                print(f"\n[FAIL] Test failed")
                if not pattern_match:
                    print(f"  - Missing expected pattern: {test_case['expected_pattern']}")
                if forbidden_found:
                    print(f"  - Contains forbidden content: {forbidden_found}")

        except Exception as e:
            failed += 1
            print(f"\n[ERROR] Test error: {e}")
            import traceback
            traceback.print_exc()

    # 输出测试报告
    print(f"\n{'=' * 80}")
    print("Test Report")
    print(f"{'=' * 80}")
    print(f"\nTotal: {len(test_queries)} tests")
    print(f"[PASS] Passed: {passed} ({passed/len(test_queries)*100:.1f}%)")
    print(f"[FAIL] Failed: {failed} ({failed/len(test_queries)*100:.1f}%)")
    print()

    return passed == len(test_queries)


def test_manual_fix():
    """测试手动修复功能"""

    print("\n" + "=" * 80)
    print("手动修复测试（直接调用 _fix_summary_sql_if_needed）")
    print("=" * 80)

    llm = BaseLLM(temperature=0.0)
    base_prompt = PromptManager.get_scenic_query_prompt()
    generator = SQLGenerator(llm, base_prompt)

    # 测试用例：错误的 Summary SQL（包含 json_agg）
    wrong_sql = """
SELECT json_agg(json_build_object(
    'name', a.name,
    'level', a.level
)) as result
FROM a_sight a
WHERE a."所属省份" = '浙江省' AND a.level = '5A'
"""

    print("\n原始 SQL（错误）:")
    print(wrong_sql)

    # 调用修复方法
    fixed_sql = generator._fix_summary_sql_if_needed(wrong_sql, "summary")

    print("\n修复后的 SQL:")
    print(fixed_sql)

    # 验证
    if 'json_agg' not in fixed_sql.lower() and 'COUNT(*)' in fixed_sql:
        print("\n[PASS] Fix successful: json_agg removed, changed to COUNT(*)")
        return True
    else:
        print("\n[FAIL] Fix failed")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Summary SQL 自动修复测试套件")
    print("=" * 80)

    # 测试1：手动修复功能
    manual_fix_ok = test_manual_fix()

    # 测试2：完整流程（意图分析 + SQL 生成 + 自动修复）
    auto_fix_ok = test_summary_sql_auto_fix()

    # 总结
    print("\n" + "=" * 80)
    print("Overall Test Results")
    print("=" * 80)
    print(f"Manual fix test: {'[PASS]' if manual_fix_ok else '[FAIL]'}")
    print(f"Auto fix test: {'[PASS]' if auto_fix_ok else '[FAIL]'}")

    if manual_fix_ok and auto_fix_ok:
        print("\n[SUCCESS] All tests passed! Summary SQL auto-fix works correctly.")
    else:
        print("\n[WARNING] Some tests failed, please check logs.")
