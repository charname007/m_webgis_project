"""
测试返回结果中的 intent_info 字段
"""

import logging
import json
import sys
import io
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from core.agent import SQLQueryAgent

logging.basicConfig(
    level=logging.WARNING,  # 减少日志输出
    format='%(levelname)s - %(message)s'
)

def test_intent_info():
    print("\n========== 测试 intent_info 字段返回 ==========\n")

    agent = SQLQueryAgent(enable_memory=False, enable_checkpoint=False)

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
        }
    ]

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}: {test_case['query']}")
        print("-" * 50)

        try:
            result_json = agent.run(test_case['query'])
            result = json.loads(result_json)

            # 检查是否有 intent_info 字段
            if 'intent_info' not in result:
                print(f"❌ 失败：结果中没有 intent_info 字段")
                all_passed = False
                continue

            intent_info = result['intent_info']

            if intent_info is None:
                print(f"❌ 失败：intent_info 为 null")
                all_passed = False
                continue

            print(f"✓ intent_info 存在")
            print(f"  intent_type: {intent_info.get('intent_type')}")
            print(f"  is_spatial: {intent_info.get('is_spatial')}")
            print(f"  keywords_matched: {intent_info.get('keywords_matched')}")
            print(f"  description: {intent_info.get('description')}")

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
            all_passed = False

    agent.close()

    print("=" * 50)
    if all_passed:
        print("✅ 所有测试通过")
        return True
    else:
        print("❌ 部分测试失败")
        return False

if __name__ == "__main__":
    try:
        success = test_intent_info()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
