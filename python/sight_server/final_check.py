"""
最终完整性检查
"""

import sys
import io

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("\n========== 最终完整性检查 ==========\n")

# 1. 导入测试
print("1. 导入测试")
try:
    from core.prompts import (
        PromptManager,
        PromptType,
        QueryIntentType,
        SPATIAL_KEYWORDS,
        SUMMARY_KEYWORDS
    )
    print("  ✓ 所有模块导入成功")
except Exception as e:
    print(f"  ✗ 导入失败: {e}")
    sys.exit(1)

# 2. 枚举测试
print("\n2. 枚举测试")
print(f"  PromptType: {[e.value for e in PromptType]}")
print(f"  QueryIntentType: {[e.value for e in QueryIntentType]}")

# 3. 关键词库测试
print("\n3. 关键词库测试")
print(f"  SPATIAL_KEYWORDS 数量: {len(SPATIAL_KEYWORDS)}")
print(f"  SUMMARY_KEYWORDS 数量: {len(SUMMARY_KEYWORDS)}")
print(f"  SPATIAL_KEYWORDS 示例: {SPATIAL_KEYWORDS[:5]}")
print(f"  SUMMARY_KEYWORDS 示例: {SUMMARY_KEYWORDS[:5]}")

# 4. 提示词获取测试
print("\n4. 提示词获取测试")
try:
    scenic_prompt = PromptManager.get_scenic_query_prompt()
    spatial_prompt = PromptManager.get_spatial_enhancement_prompt()
    general_prompt = PromptManager.get_general_query_prompt()
    print(f"  ✓ SCENIC_QUERY_PROMPT 长度: {len(scenic_prompt)}")
    print(f"  ✓ SPATIAL_ENHANCEMENT_PROMPT 长度: {len(spatial_prompt)}")
    print(f"  ✓ GENERAL_QUERY_PROMPT 长度: {len(general_prompt)}")
except Exception as e:
    print(f"  ✗ 获取提示词失败: {e}")
    sys.exit(1)

# 5. analyze_query_intent 测试
print("\n5. analyze_query_intent 方法测试")
test_cases = [
    ("查询浙江省的5A景区", "query", False),
    ("统计浙江省有多少个5A景区", "summary", False),
    ("查找距离杭州10公里内的景区", "query", True),
    ("统计西湖周围5公里的景点数量", "summary", True)
]

all_passed = True
for query, expected_intent, expected_spatial in test_cases:
    try:
        result = PromptManager.analyze_query_intent(query)
        intent_ok = result["intent_type"] == expected_intent
        spatial_ok = result["is_spatial"] == expected_spatial

        if intent_ok and spatial_ok:
            print(f"  ✓ '{query[:20]}...'")
        else:
            print(f"  ✗ '{query[:20]}...' (intent: {result['intent_type']}/{expected_intent}, spatial: {result['is_spatial']}/{expected_spatial})")
            all_passed = False
    except Exception as e:
        print(f"  ✗ '{query[:20]}...' 异常: {e}")
        all_passed = False

# 6. detect_query_type 测试
print("\n6. detect_query_type 方法测试")
detection_tests = [
    ("查询浙江省的5A景区", PromptType.SCENIC_QUERY),
    ("查找距离杭州10公里内的景点", PromptType.SPATIAL_QUERY),
    ("统计所有表的记录数", PromptType.GENERAL_QUERY)
]

for query, expected_type in detection_tests:
    try:
        detected_type = PromptManager.detect_query_type(query)
        if detected_type == expected_type:
            print(f"  ✓ '{query[:20]}...' -> {detected_type.value}")
        else:
            print(f"  ✗ '{query[:20]}...' -> {detected_type.value} (预期: {expected_type.value})")
            all_passed = False
    except Exception as e:
        print(f"  ✗ '{query[:20]}...' 异常: {e}")
        all_passed = False

# 7. build_enhanced_query 测试
print("\n7. build_enhanced_query 方法测试")
try:
    enhanced = PromptManager.build_enhanced_query(
        "查询杭州市的景区",
        add_spatial_hint=True,
        custom_instructions="请返回前5条记录"
    )
    if "查询杭州市的景区" in enhanced and "PostGIS" in enhanced and "请返回前5条记录" in enhanced:
        print("  ✓ build_enhanced_query 正常工作")
    else:
        print("  ✗ build_enhanced_query 返回内容不完整")
        all_passed = False
except Exception as e:
    print(f"  ✗ build_enhanced_query 异常: {e}")
    all_passed = False

# 8. 提示词内容检查
print("\n8. 提示词内容关键检查")
content_checks = {
    "FULL OUTER JOIN": scenic_prompt.count("FULL OUTER JOIN") >= 15,
    "LEFT JOIN": scenic_prompt.count("LEFT JOIN") >= 10,
    "COALESCE": scenic_prompt.count("COALESCE") >= 5,
    "_dataSource": scenic_prompt.count("_dataSource") >= 3,
    "UNION ALL": scenic_prompt.count("UNION ALL") >= 3,
    "禁止json_agg": "绝对禁止使用 json_agg" in scenic_prompt,
    "空间查询说明": "特殊场景 - 空间查询" in scenic_prompt
}

for check_name, passed in content_checks.items():
    if passed:
        print(f"  ✓ {check_name}")
    else:
        print(f"  ✗ {check_name}")
        all_passed = False

# 最终结果
print("\n" + "=" * 50)
if all_passed:
    print("✅ 所有检查通过！prompts.py 完整且正确")
    print("\n更新内容：")
    print("  - FULL OUTER JOIN 策略已应用")
    print("  - analyze_query_intent 方法完整实现")
    print("  - Summary 查询禁止 json_agg")
    print("  - COALESCE 和 _dataSource 已添加")
    print("  - 正则表达式错误已修复")
    sys.exit(0)
else:
    print("❌ 部分检查失败，请检查错误信息")
    sys.exit(1)
