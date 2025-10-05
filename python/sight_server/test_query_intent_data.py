"""
测试查询意图对返回数据的影响

测试场景：
1. query 类型：返回完整 data
2. summary 类型：data 字段为 null，仅返回 count 和 answer
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

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import SQLQueryAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_query_intent_data_handling():
    """测试不同查询意图对返回数据的影响"""

    print("\n" + "=" * 80)
    print("测试查询意图对返回数据的影响")
    print("=" * 80 + "\n")

    try:
        # 初始化 Agent
        print("初始化 SQLQueryAgent...")
        agent = SQLQueryAgent(
            enable_memory=False,
            enable_checkpoint=False
        )
        print("✓ Agent 初始化成功\n")

        # 测试用例
        test_cases = [
            {
                "name": "测试1: Query类型 - 应返回完整data",
                "query": "查询浙江省的5A景区",
                "expected_intent": "query",
                "expected_data": "not null"
            },
            {
                "name": "测试2: Summary类型 - 应仅返回count",
                "query": "统计浙江省有多少个5A景区",
                "expected_intent": "summary",
                "expected_data": "null"
            },
            {
                "name": "测试3: Query类型（空间查询）",
                "query": "查找距离杭州10公里内的景区",
                "expected_intent": "query",
                "expected_data": "not null"
            },
            {
                "name": "测试4: Summary类型（带关键词'数量'）",
                "query": "浙江省4A景区的数量",
                "expected_intent": "summary",
                "expected_data": "null"
            }
        ]

        results = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'─' * 80}")
            print(f"{test_case['name']}")
            print(f"{'─' * 80}")
            print(f"查询: {test_case['query']}")
            print(f"预期意图: {test_case['expected_intent']}")
            print(f"预期data: {test_case['expected_data']}")
            print()

            try:
                # 执行查询
                json_result = agent.run(test_case['query'])
                result = json.loads(json_result)

                # 检查结果
                has_data = result.get("data") is not None
                data_count = len(result.get("data", [])) if has_data else 0
                count_field = result.get("count", 0)

                print(f"✓ 查询执行成功")
                print(f"  状态: {result.get('status')}")
                print(f"  count 字段: {count_field}")
                print(f"  data 字段: {'存在' if has_data else 'null'}")
                if has_data:
                    print(f"  data 记录数: {data_count}")
                print(f"  answer: {result.get('answer', '')[:100]}...")

                # 验证预期
                expected_has_data = (test_case['expected_data'] == "not null")
                if has_data == expected_has_data:
                    print(f"\n✅ 测试通过: data字段符合预期")
                    test_result = "PASS"
                else:
                    print(f"\n❌ 测试失败: data字段不符合预期")
                    print(f"   预期: {test_case['expected_data']}")
                    print(f"   实际: {'not null' if has_data else 'null'}")
                    test_result = "FAIL"

                results.append({
                    "test": test_case['name'],
                    "query": test_case['query'],
                    "result": test_result,
                    "has_data": has_data,
                    "count": count_field
                })

            except Exception as e:
                print(f"❌ 查询执行失败: {e}")
                logger.exception("查询执行异常")
                results.append({
                    "test": test_case['name'],
                    "query": test_case['query'],
                    "result": "ERROR",
                    "error": str(e)
                })

        # 输出测试总结
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80 + "\n")

        passed = sum(1 for r in results if r.get("result") == "PASS")
        failed = sum(1 for r in results if r.get("result") == "FAIL")
        errors = sum(1 for r in results if r.get("result") == "ERROR")

        print(f"总计: {len(results)} 个测试")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"错误: {errors}")
        print()

        for r in results:
            status_icon = "✅" if r["result"] == "PASS" else "❌"
            print(f"{status_icon} {r['test']}")
            if r["result"] == "PASS":
                print(f"   查询: {r['query']}")
                print(f"   data字段: {'有数据' if r['has_data'] else 'null'}, count: {r['count']}")
            elif r["result"] == "ERROR":
                print(f"   错误: {r.get('error', 'Unknown')}")
            print()

        # 关闭 Agent
        agent.close()
        print("✓ Agent 已关闭")

        return passed == len(results)

    except Exception as e:
        print(f"\n❌ 测试过程出现异常: {e}")
        logger.exception("测试异常")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("查询意图数据返回测试")
    print("=" * 80)

    success = test_query_intent_data_handling()

    print("\n" + "=" * 80)
    if success:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败")
    print("=" * 80 + "\n")

    sys.exit(0 if success else 1)
