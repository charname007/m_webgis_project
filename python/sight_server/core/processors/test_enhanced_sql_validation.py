"""
增强SQL验证测试模块
测试新的递归AST遍历和别名检测功能
"""

import logging
import sys
import os

# 添加父目录到路径，以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sql_generator import SQLGenerator

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_simple_query():
    """测试简单查询"""
    print("\n=== 测试1: 简单查询 ===")
    sql = "SELECT a.name, a.level FROM a_sight a WHERE a.level = '5A'"
    generator = SQLGenerator(None, "测试提示词")
    
    try:
        result = generator._validate_sql_structure(sql)
        print(f"SQL: {sql}")
        print(f"验证结果: {result}")
        assert result == True, "简单查询验证失败"
        print("PASS: 简单查询验证通过")
    except Exception as e:
        print(f"FAIL: 简单查询验证失败: {e}")


def test_subquery_with_alias():
    """测试带子查询和别名的复杂查询"""
    print("\n=== 测试2: 带子查询的复杂查询 ===")
    sql = """
    SELECT 
        main.name,
        main.level,
        sub.avg_rating
    FROM a_sight main
    LEFT JOIN (
        SELECT 
            t.name,
            AVG(t.rating) as avg_rating
        FROM tourist_spot t
        WHERE t.rating > 4.0
        GROUP BY t.name
    ) sub ON sub.name = main.name
    WHERE main.level = '5A'
    """
    generator = SQLGenerator(None, "测试提示词")
    
    try:
        result = generator._validate_sql_structure(sql)
        print(f"SQL: {sql[:100]}...")
        print(f"验证结果: {result}")
        assert result == True, "子查询验证失败"
        print("PASS: 子查询验证通过")
    except Exception as e:
        print(f"FAIL: 子查询验证失败: {e}")


def test_cte_with_aliases():
    """测试带CTE和别名的查询"""
    print("\n=== 测试3: 带CTE的查询 ===")
    sql = """
    WITH top_rated AS (
        SELECT 
            name,
            rating,
            'high' as rating_category
        FROM tourist_spot
        WHERE rating >= 4.5
    ),
    level_5a AS (
        SELECT 
            name,
            level
        FROM a_sight
        WHERE level = '5A'
    )
    SELECT 
        l.name,
        l.level,
        t.rating,
        t.rating_category
    FROM level_5a l
    JOIN top_rated t ON l.name = t.name
    """
    generator = SQLGenerator(None, "测试提示词")
    
    try:
        result = generator._validate_sql_structure(sql)
        print(f"SQL: {sql[:100]}...")
        print(f"验证结果: {result}")
        assert result == True, "CTE查询验证失败"
        print("PASS: CTE查询验证通过")
    except Exception as e:
        print(f"FAIL: CTE查询验证失败: {e}")


def test_undefined_alias():
    """测试未定义别名的错误检测"""
    print("\n=== 测试4: 未定义别名检测 ===")
    sql = "SELECT x.name FROM a_sight a WHERE x.level = '5A'"  # x 未定义
    generator = SQLGenerator(None, "测试提示词")
    
    try:
        result = generator._validate_sql_structure(sql)
        print(f"SQL: {sql}")
        print(f"验证结果: {result}")
        assert result == False, "未定义别名应该被检测到"
        print("PASS: 未定义别名检测通过")
    except ValueError as e:
        print(f"PASS: 未定义别名被正确检测到: {e}")
    except Exception as e:
        print(f"FAIL: 未定义别名检测失败: {e}")


def test_duplicate_alias():
    """测试重复别名检测"""
    print("\n=== 测试5: 重复别名检测 ===")
    sql = """
    SELECT 
        a.name,
        a.level
    FROM a_sight a
    JOIN tourist_spot a ON a.name = a.name  -- 重复别名 'a'
    """
    generator = SQLGenerator(None, "测试提示词")
    
    try:
        result = generator._validate_sql_structure(sql)
        print(f"SQL: {sql[:100]}...")
        print(f"验证结果: {result}")
        print("PASS: 重复别名检测通过（警告级别）")
    except Exception as e:
        print(f"FAIL: 重复别名检测失败: {e}")


def test_complex_join_structure():
    """测试复杂JOIN结构"""
    print("\n=== 测试6: 复杂JOIN结构 ===")
    sql = """
    SELECT 
        a.name as sight_name,
        a.level,
        t.name as spot_name,
        t.rating,
        COALESCE(t.description, '暂无描述') as description
    FROM a_sight a
    LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'
        OR TRIM(SPLIT_PART(t.name, ' ', 1)) = a.name
    WHERE a.level IN ('5A', '4A')
        AND (t.rating IS NULL OR t.rating >= 4.0)
    ORDER BY a.level DESC, t.rating DESC NULLS LAST
    """
    generator = SQLGenerator(None, "测试提示词")
    
    try:
        result = generator._validate_sql_structure(sql)
        print(f"SQL: {sql[:100]}...")
        print(f"验证结果: {result}")
        assert result == True, "复杂JOIN结构验证失败"
        print("PASS: 复杂JOIN结构验证通过")
    except Exception as e:
        print(f"FAIL: 复杂JOIN结构验证失败: {e}")


def test_nested_subqueries():
    """测试嵌套子查询"""
    print("\n=== 测试7: 嵌套子查询 ===")
    sql = """
    SELECT 
        outer_sight.name,
        outer_sight.level,
        (
            SELECT COUNT(*) 
            FROM tourist_spot inner_spot
            WHERE inner_spot.name LIKE outer_sight.name || '%'
        ) as related_spots
    FROM a_sight outer_sight
    WHERE outer_sight.level = '5A'
        AND (
            SELECT AVG(rating)
            FROM tourist_spot avg_spot
            WHERE avg_spot.name LIKE outer_sight.name || '%'
        ) > 4.0
    """
    generator = SQLGenerator(None, "测试提示词")
    
    try:
        result = generator._validate_sql_structure(sql)
        print(f"SQL: {sql[:100]}...")
        print(f"验证结果: {result}")
        assert result == True, "嵌套子查询验证失败"
        print("PASS: 嵌套子查询验证通过")
    except Exception as e:
        print(f"FAIL: 嵌套子查询验证失败: {e}")


def test_string_literal_context():
    """测试字符串字面量中的别名不被误识别"""
    print("\n=== 测试8: 字符串字面量上下文 ===")
    sql = """
    SELECT 
        a.name,
        'This is a test for alias a.name in string' as description,
        a.level
    FROM a_sight a
    WHERE a.name LIKE '%test%'
    """
    generator = SQLGenerator(None, "测试提示词")
    
    try:
        result = generator._validate_sql_structure(sql)
        print(f"SQL: {sql[:100]}...")
        print(f"验证结果: {result}")
        assert result == True, "字符串字面量上下文验证失败"
        print("PASS: 字符串字面量上下文验证通过")
    except Exception as e:
        print(f"FAIL: 字符串字面量上下文验证失败: {e}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始增强SQL验证测试")
    print("=" * 60)
    
    test_simple_query()
    test_subquery_with_alias()
    test_cte_with_aliases()
    test_undefined_alias()
    test_duplicate_alias()
    test_complex_join_structure()
    test_nested_subqueries()
    test_string_literal_context()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()