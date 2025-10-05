"""
测试 analyze_query_intent 方法（不运行Agent）
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

print("\n========== 测试 analyze_query_intent 方法 ==========\n")

test_cases = [
    {
        "query": "查询浙江省的5A景区",
        "expected_intent": "query",
        "expected_spatial": False
    },
    {
        "query": "统计浙江省有多少个5A景区",
        "expected_intent": "summary",
        "expected_spatial": False
    },
    {
        "query": "查找距离杭州10公里内的景区",
        "expected_intent": "query",
        "expected_spatial": True
    },
    {
        "query": "统计西湖周围5公里的景点数量",
        "expected_intent": "summary",
        "expected_spatial": True
    }
]

all_passed = True

for i, test_case in enumerate(test_cases, 1):
    print(f"测试 {i}: {test_case['query']}")
    print("-" * 50)

    try:
        intent_info = PromptManager.analyze_query_intent(test_case['query'])

        print(f"✓ 意图分析成功")
        print(f"  intent_type: {intent_info.get('intent_type')}")
        print(f"  is_spatial: {intent_info.get('is_spatial')}")
        print(f"  keywords_matched: {intent_info.get('keywords_matched')}")
        print(f"  description: {intent_info.get('description')}")
        print(f"  confidence: {intent_info.get('confidence', 0):.2f}")

        # 验证预期值
        actual_intent = intent_info.get('intent_type')
        actual_spatial = intent_info.get('is_spatial')

        if actual_intent == test_case['expected_intent']:
            print(f"✓ intent_type 正确: {actual_intent}")
        else:
            print(f"❌ intent_type 错误: 预期 {test_case['expected_intent']}, 实际 {actual_intent}")
            all_passed = False

        if actual_spatial == test_case['expected_spatial']:
            print(f"✓ is_spatial 正确: {actual_spatial}")
        else:
            print(f"❌ is_spatial 错误: 预期 {test_case['expected_spatial']}, 实际 {actual_spatial}")
            all_passed = False

        print()

    except Exception as e:
        print(f"❌ 异常: {e}\n")
        import traceback
        traceback.print_exc()
        all_passed = False

print("=" * 50)
if all_passed:
    print("✅ 所有测试通过")
    sys.exit(0)
else:
    print("❌ 部分测试失败")
    sys.exit(1)
