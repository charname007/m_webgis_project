"""
测试 FROM 子句丢失问题的修复

测试场景：
1. 验证提示词是否包含 FROM 子句强调
2. 测试 SQL 生成器的验证功能
3. 测试自动修复功能
"""

import sys
import os
import io

# 设置标准输出为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.prompts import PromptManager
from core.processors.sql_generator import SQLGenerator
from core.llm import BaseLLM
from config import settings

print("=" * 80)
print("FROM 子句丢失问题修复测试")
print("=" * 80)

# 测试1：检查提示词是否包含 FROM 子句强调
print("\n【测试1】检查提示词是否包含 FROM 子句强调")
print("-" * 80)
scenic_prompt = PromptManager.get_scenic_query_prompt()

# 检查关键字
key_phrases = [
    "FROM 子句绝对不能缺失",
    "FROM a_sight a",
    "丢失FROM子句项",
    "必须先定义别名 a",
    "SELECT 后面必须紧跟 FROM 子句"
]

for phrase in key_phrases:
    if phrase in scenic_prompt:
        print(f"✅ 找到关键提示: '{phrase}'")
    else:
        print(f"❌ 缺少关键提示: '{phrase}'")

# 测试2：测试 SQL 验证功能
print("\n【测试2】测试 SQL 验证功能")
print("-" * 80)

# 初始化 SQL 生成器（不需要真实的 LLM）
class MockLLM:
    def __init__(self):
        self.llm = self

    def invoke(self, prompt):
        class Response:
            def __init__(self, content):
                self.content = content
        # 返回一个缺少 FROM 的 SQL
        return Response("""
        SELECT json_agg(
            json_build_object(
                'name', a.name,
                'level', a.level
            )
        )
        WHERE a.level = '5A'
        """)

sql_gen = SQLGenerator(MockLLM(), scenic_prompt)

# 测试缺少 FROM 的 SQL
invalid_sql = """
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.level
    )
)
WHERE a.level = '5A'
"""

print("测试 SQL (缺少 FROM):")
print(invalid_sql)
print()

is_valid = sql_gen._validate_sql_structure(invalid_sql.strip())
print(f"验证结果: {'✅ 通过' if is_valid else '❌ 失败（符合预期）'}")

# 测试完整的 SQL
valid_sql = """
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.level
    )
) as result
FROM a_sight a
WHERE a.level = '5A'
"""

print("\n测试 SQL (完整):")
print(valid_sql)
print()

is_valid = sql_gen._validate_sql_structure(valid_sql.strip())
print(f"验证结果: {'✅ 通过（符合预期）' if is_valid else '❌ 失败'}")

# 测试3：测试自动修复功能
print("\n【测试3】测试自动修复功能")
print("-" * 80)

print("原始 SQL (缺少 FROM):")
print(invalid_sql)
print()

fixed_sql = sql_gen._add_from_clause_if_missing(invalid_sql.strip(), "查询5A景区")
print("修复后的 SQL:")
print(fixed_sql)
print()

# 验证修复后的 SQL
is_valid_after_fix = sql_gen._validate_sql_structure(fixed_sql)
print(f"修复后验证: {'✅ 通过（修复成功）' if is_valid_after_fix else '❌ 失败（修复失败）'}")

# 测试4：检查修复后的 SQL 是否包含必要的 FROM 子句
print("\n【测试4】检查修复后的 SQL 结构")
print("-" * 80)

checks = {
    "包含 FROM 关键字": "from" in fixed_sql.lower(),
    "定义了别名 a": "a_sight a" in fixed_sql.lower() or "a_sight as a" in fixed_sql.lower(),
    "使用了别名 a": "a." in fixed_sql.lower(),
}

for check_name, result in checks.items():
    print(f"{'✅' if result else '❌'} {check_name}: {result}")

# 总结
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)

all_passed = (
    all(phrase in scenic_prompt for phrase in key_phrases[:3]) and  # 提示词包含关键短语
    not sql_gen._validate_sql_structure(invalid_sql.strip()) and    # 能识别错误 SQL
    sql_gen._validate_sql_structure(valid_sql.strip()) and          # 能识别正确 SQL
    is_valid_after_fix and                                           # 修复功能有效
    all(checks.values())                                             # 修复后结构正确
)

if all_passed:
    print("✅ 所有测试通过！FROM 子句丢失问题已修复")
else:
    print("❌ 部分测试未通过，请检查修复方案")

print("\n提示词前500字符预览：")
print("-" * 80)
print(scenic_prompt[:500])
print("...")
