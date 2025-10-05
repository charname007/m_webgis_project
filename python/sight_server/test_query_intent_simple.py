"""
简化版查询意图测试
只测试核心功能，快速验证
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

def test_simple():
    print("\n========== 查询意图数据返回测试 ==========\n")

    agent = SQLQueryAgent(enable_memory=False, enable_checkpoint=False)

    # 测试1: Query类型
    print("测试1: Query类型 - '查询浙江省的5A景区'")
    print("-" * 50)
    result1 = json.loads(agent.run("查询浙江省的5A景区"))
    has_data1 = result1.get("data") is not None
    count1 = result1.get("count", 0)
    print(f"✓ 状态: {result1['status']}")
    print(f"✓ data字段: {'存在' if has_data1 else 'null'}")
    print(f"✓ count: {count1}")
    print(f"✓ 预期data=存在: {'通过' if has_data1 else '失败'}\n")

    # 测试2: Summary类型
    print("测试2: Summary类型 - '统计浙江省有多少个5A景区'")
    print("-" * 50)
    result2 = json.loads(agent.run("统计浙江省有多少个5A景区"))
    has_data2 = result2.get("data") is not None
    count2 = result2.get("count", 0)
    print(f"✓ 状态: {result2['status']}")
    print(f"✓ data字段: {'存在' if has_data2 else 'null'}")
    print(f"✓ count: {count2}")
    print(f"✓ 预期data=null: {'通过' if not has_data2 else '失败'}\n")

    agent.close()

    # 总结
    print("=" * 50)
    if has_data1 and not has_data2:
        print("✅ 所有测试通过")
        return True
    else:
        print("❌ 测试失败")
        return False

if __name__ == "__main__":
    try:
        success = test_simple()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
