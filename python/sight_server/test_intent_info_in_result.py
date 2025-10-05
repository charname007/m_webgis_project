"""
测试 API 返回是否包含 intent_info
"""

import sys
import io
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from core.agent import SQLQueryAgent
from config import settings
import json

print("\n========== 测试 API 返回中的 intent_info ==========\n")

# 创建 Agent 实例
agent = SQLQueryAgent(
    database_url=settings.DATABASE_URL
)

# 测试查询
test_query = "浙江省有多少个5A景区"
print(f"测试查询: {test_query}\n")

try:
    # 运行查询
    result = agent.run(test_query)

    # 检查返回结果
    print("返回结果结构:")
    print(f"  - status: {result.status}")
    print(f"  - answer: {result.answer[:50]}..." if len(result.answer) > 50 else f"  - answer: {result.answer}")
    print(f"  - data: {'存在' if result.data else 'None'}")
    print(f"  - count: {result.count}")
    print(f"  - sql: {'存在' if result.sql else 'None'}")
    print(f"  - intent_info: {'存在' if result.intent_info else '❌ None (缺失!)'}")

    if result.intent_info:
        print("\n✅ intent_info 内容:")
        print(json.dumps(result.intent_info, indent=2, ensure_ascii=False))
    else:
        print("\n❌ 错误：intent_info 字段为 None！")
        print("\n调试信息：检查 agent.run() 是否正确传递了 intent_info")

except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
