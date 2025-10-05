"""
验证prompts.py中FULL OUTER JOIN和LEFT JOIN的使用
"""

import sys
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from core.prompts import PromptManager

print("\n========== 验证 Prompts.py 内容 ==========\n")

prompt = PromptManager.get_scenic_query_prompt()

print(f"✓ 提示词总长度: {len(prompt)} 字符\n")

# 统计JOIN使用情况
full_outer_count = prompt.count("FULL OUTER JOIN")
left_join_count = prompt.count("LEFT JOIN")
right_join_count = prompt.count("RIGHT JOIN")

print("=== JOIN 使用统计 ===")
print(f"FULL OUTER JOIN 出现次数: {full_outer_count}")
print(f"LEFT JOIN 出现次数: {left_join_count}")
print(f"RIGHT JOIN 出现次数: {right_join_count}\n")

# 检查关键内容
print("=== 关键内容检查 ===")
checks = {
    "通用查询使用FULL OUTER JOIN": "FULL OUTER JOIN tourist_spot" in prompt,
    "空间查询使用LEFT JOIN": "特殊场景 - 空间查询" in prompt or "必须有坐标" in prompt,
    "禁止Summary使用json_agg": "绝对禁止使用 json_agg" in prompt,
    "COALESCE处理NULL": "COALESCE" in prompt,
    "_dataSource字段": "_dataSource" in prompt,
    "UNION ALL策略": "UNION ALL" in prompt
}

all_passed = True
for check_name, result in checks.items():
    status = "✓" if result else "✗"
    print(f"{status} {check_name}: {result}")
    if not result:
        all_passed = False

print()

# 验证analyze_query_intent方法
print("=== analyze_query_intent 方法验证 ===")
test_queries = [
    ("查询浙江省的5A景区", "query", False),
    ("统计浙江省有多少个5A景区", "summary", False),
    ("查找距离杭州10公里内的景区", "query", True)
]

for query, expected_intent, expected_spatial in test_queries:
    intent_info = PromptManager.analyze_query_intent(query)
    intent_match = intent_info["intent_type"] == expected_intent
    spatial_match = intent_info["is_spatial"] == expected_spatial

    status = "✓" if (intent_match and spatial_match) else "✗"
    print(f"{status} '{query}'")
    print(f"  intent: {intent_info['intent_type']} (预期: {expected_intent}) {'✓' if intent_match else '✗'}")
    print(f"  spatial: {intent_info['is_spatial']} (预期: {expected_spatial}) {'✓' if spatial_match else '✗'}")

    if not (intent_match and spatial_match):
        all_passed = False

print()
print("=" * 50)
if all_passed:
    print("✅ 所有验证通过！prompts.py 已正确更新")
    sys.exit(0)
else:
    print("❌ 部分验证失败")
    sys.exit(1)
