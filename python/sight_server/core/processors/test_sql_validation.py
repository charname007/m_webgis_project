"""
SQL验证修复测试
测试修复后的 _extract_aliases_via_sqlparse 和 _validate_sql_structure 方法
"""

import logging
import sys
import os

# 添加项目路径到sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_generator import SQLGenerator

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_sql_validation():
    """测试SQL验证功能"""
    print("=== SQL验证修复测试 ===\n")

    # 创建SQLGenerator实例
    generator = SQLGenerator(None, "测试提示词")

    # 测试用例
    test_cases = [
        {
            "name": "简单查询 - 有效",
            "sql": "SELECT COUNT(*) as count FROM a_sight WHERE level = '5A'",
            "expected": True
        },
        {
            "name": "带别名查询 - 有效",
            "sql": "SELECT COUNT(*) as count FROM a_sight a WHERE a.level = '5A'",
            "expected": True
        },
        {
            "name": "双表查询 - 有效",
            "sql": "SELECT COUNT(*) as count FROM a_sight a LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'",
            "expected": True
        },
        {
            "name": "JSON聚合查询 - 有效",
            "sql": "SELECT json_agg(json_build_object('name', a.name, 'level', a.level)) as result FROM a_sight a",
            "expected": True
        },
        {
            "name": "空间查询 - 有效",
            "sql": "SELECT json_agg(json_build_object('name', a.name, 'coordinates', json_build_array(a.lng_wgs84, a.lat_wgs84))) as result FROM a_sight a WHERE a.lng_wgs84 IS NOT NULL",
            "expected": True
        },
        {
            "name": "GROUP BY查询 - 有效",
            "sql": "SELECT level, COUNT(*) as count FROM a_sight GROUP BY level",
            "expected": True
        },
        {
            "name": "缺少FROM子句 - 无效",
            "sql": "SELECT COUNT(*) as count WHERE level = '5A'",
            "expected": False
        },
        {
            "name": "未定义别名 - 无效",
            "sql": "SELECT a.name FROM a_sight WHERE a.level = '5A'",
            "expected": False
        },
        {
            "name": "复杂子查询 - 边界情况",
            "sql": "SELECT (SELECT COUNT(*) FROM tourist_spot t WHERE t.name LIKE a.name || '%') as spot_count FROM a_sight a",
            "expected": True
        }
    ]

    results = []
    for test_case in test_cases:
        print(f"测试: {test_case['name']}")
        print(f"SQL: {test_case['sql']}")

        try:
            result = generator.validate(test_case['sql'])
            status = "PASS" if result == test_case['expected'] else "FAIL"
            print(f"结果: {result} (预期: {test_case['expected']}) - {status}")

            results.append({
                "name": test_case['name'],
                "result": result,
                "expected": test_case['expected'],
                "status": "PASS" if result == test_case['expected'] else "FAIL"
            })

        except Exception as e:
            print(f"错误: {e}")
            results.append({
                "name": test_case['name'],
                "result": None,
                "expected": test_case['expected'],
                "status": "ERROR"
            })

        print("-" * 50)

    # 统计结果
    print("\n=== 测试结果统计 ===")
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] == 'ERROR')

    print(f"总计: {len(results)} 个测试用例")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"错误: {errors}")
    print(f"成功率: {passed/len(results)*100:.1f}%")

    # 显示失败详情
    if failed > 0 or errors > 0:
        print("\n=== 失败详情 ===")
        for result in results:
            if result['status'] != 'PASS':
                print(f"- {result['name']}: {result['status']}")

if __name__ == "__main__":
    test_sql_validation()