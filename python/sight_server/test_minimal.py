"""最简测试：只测试一个Query类型查询"""
import logging
import json
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from core.agent import SQLQueryAgent

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

agent = SQLQueryAgent(enable_memory=False, enable_checkpoint=False)

print("\n测试: 查询浙江省的5A景区\n")

try:
    result_json = agent.run("查询浙江省的5A景区")
    result = json.loads(result_json)

    print(f"状态: {result['status']}")
    print(f"count: {result.get('count', 0)}")
    print(f"data字段: {'存在' if result.get('data') is not None else 'null'}")

    if result.get('data'):
        print(f"data记录数: {len(result['data'])}")
        if len(result['data']) > 0:
            print(f"第一条记录: {result['data'][0]}")

    if result['status'] == 'success' and result.get('data'):
        print("\n✅ 测试通过")
    else:
        print(f"\n❌ 测试失败: {result.get('message', '未知错误')}")

except Exception as e:
    print(f"❌ 异常: {e}")
    import traceback
    traceback.print_exc()
finally:
    agent.close()
