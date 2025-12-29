"""
快速测试 intent_info 是否在返回结果中
"""

import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from core.agent import SQLQueryAgent
import json

print("\n========== 测试 intent_info 返回 ==========\n")

# 创建简单的 Agent 实例
agent = SQLQueryAgent()

# 测试查询
test_query = "浙江省有多少个5A景区"
print(f"查询: {test_query}\n")

try:
    result = agent.run(test_query)

    print("📋 返回结果:")
    print(f"  status: {result.status}")
    print(f"  count: {result.count}")
    print(f"  intent_info: {('✅ 存在' if result.intent_info else '❌ None')}")

    if result.intent_info:
        print("\n✅ intent_info 详情:")
        print(json.dumps(result.intent_info, indent=2, ensure_ascii=False))
    else:
        print("\n❌ 问题：intent_info 为 None！")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
