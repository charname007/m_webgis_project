"""
SQL FROM子句修复验证测试
测试增强的SQL验证和自动修复机制
"""

import logging
import re
from typing import Set

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MockSQLGenerator:
    """
    模拟SQL生成器，只包含验证和修复方法
    避免依赖项目配置
    """
    
    def __init__(self):
        self.logger = logger
    
    def _validate_sql_structure(self, sql: str) -> bool:
        """
        验证SQL是否包含必需的FROM子句和正确的别名定义

        Args:
            sql: SQL语句

        Returns:
            bool: SQL结构是否有效
        """
        sql_lower = sql.lower()

        # 检查是否包含FROM关键字
        if 'from' not in sql_lower:
            self.logger.warning("SQL missing FROM keyword")
            return False

        # 提取所有使用的表别名（模式：别名.字段名）
        alias_pattern = r'\b([a-z_][a-z0-9_]*)\.\w+'
        used_aliases = set(re.findall(alias_pattern, sql_lower))
        
        # 移除系统关键字和常见函数名
        system_keywords = {'select', 'from', 'where', 'group', 'order', 'having', 'limit', 'offset', 'join', 'on', 'as', 'and', 'or', 'not', 'in', 'is', 'null', 'true', 'false'}
        used_aliases = used_aliases - system_keywords

        if not used_aliases:
            # 如果没有使用任何别名，则只需检查FROM子句存在即可
            self.logger.debug("No table aliases used in SQL")
            return True

        # 提取FROM子句中定义的别名
        from_pattern = r'from\s+(\w+(?:\s+(?:as\s+)?(\w+))?(?:\s*,\s*\w+(?:\s+(?:as\s+)?(\w+))?)*)'
        from_match = re.search(from_pattern, sql_lower)
        
        if not from_match:
            self.logger.warning("FROM clause found but cannot parse table aliases")
            return False

        # 提取所有定义的别名
        defined_aliases = set()
        
        # 匹配简单的表定义：table alias 或 table AS alias
        simple_table_pattern = r'(\w+)(?:\s+(?:as\s+)?(\w+))?'
        from_content = from_match.group(1)
        
        # 分割多个表定义（处理逗号分隔）
        table_definitions = re.split(r'\s*,\s*', from_content)
        
        for table_def in table_definitions:
            table_match = re.match(simple_table_pattern, table_def.strip())
            if table_match:
                table_name = table_match.group(1)
                alias_name = table_match.group(2)
                
                # 如果没有显式别名，表名本身就是别名
                if alias_name:
                    defined_aliases.add(alias_name)
                else:
                    defined_aliases.add(table_name)

        # 检查JOIN子句中的别名定义
        join_pattern = r'(?:inner|left|right|full|cross)\s+join\s+(\w+)(?:\s+(?:as\s+)?(\w+))?'
        join_matches = re.finditer(join_pattern, sql_lower)
        
        for join_match in join_matches:
            table_name = join_match.group(1)
            alias_name = join_match.group(2)
            
            if alias_name:
                defined_aliases.add(alias_name)
            else:
                defined_aliases.add(table_name)

        # 检查所有使用的别名是否都已定义
        undefined_aliases = used_aliases - defined_aliases
        
        if undefined_aliases:
            self.logger.warning(f"SQL uses undefined table aliases: {undefined_aliases}")
            for alias in undefined_aliases:
                self.logger.warning(f"  - Alias '{alias}' is used but not defined in FROM clause")
            return False

        self.logger.debug(f"SQL validation passed. Used aliases: {used_aliases}, Defined aliases: {defined_aliases}")
        return True

    def _build_enhanced_from_clause(self, used_aliases: set) -> str:
        """
        根据使用的别名构建增强的FROM子句

        Args:
            used_aliases: 使用的表别名集合

        Returns:
            构建的FROM子句字符串
        """
        lines = []
        
        # 处理常见的表别名组合
        if 'a' in used_aliases and 't' in used_aliases:
            lines = [
                "FROM a_sight a",
                "LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'",
                "    OR TRIM(SPLIT_PART(t.name, ' ', 1)) = a.name"
            ]
        elif 'a' in used_aliases:
            lines = ["FROM a_sight a"]
        elif 't' in used_aliases:
            lines = ["FROM tourist_spot t"]
        else:
            # 默认使用a_sight表
            lines = ["FROM a_sight a"]
            
            # 如果使用了其他未知别名，尝试添加它们
            for alias in used_aliases:
                if alias not in ['a', 't']:
                    self.logger.warning(f"Unknown table alias '{alias}' used, cannot auto-resolve")
        
        return "\n".join(lines) + "\n"

    def _add_from_clause_if_missing(self, sql: str, query: str) -> str:
        """
        当SQL缺少FROM子句或别名定义时，自动补全。

        增强功能：
        - 支持任意表别名的检测和修复
        - 处理多表连接和子查询场景
        - 更智能的FROM子句重建

        Args:
            sql: 原始SQL
            query: 用户查询

        Returns:
            修正后的SQL
        """
        fixed_sql = sql
        newline = '\n'
        
        # 提取所有使用的表别名
        alias_pattern = r'\b([a-z_][a-z0-9_]*)\.\w+'
        used_aliases = set(re.findall(alias_pattern, sql.lower()))
        
        # 移除系统关键字
        system_keywords = {'select', 'from', 'where', 'group', 'order', 'having', 'limit', 'offset', 'join', 'on', 'as', 'and', 'or', 'not', 'in', 'is', 'null', 'true', 'false'}
        used_aliases = used_aliases - system_keywords
        
        # 特殊处理：检测常用的表别名模式
        uses_a = 'a' in used_aliases
        uses_t = 't' in used_aliases
        
        # 尝试自动修复表别名定义
        alias_adjusted = False
        
        # 修复 a_sight 表的别名定义
        if uses_a:
            fixed_sql, count_a = re.subn(
                r'\ba_sight\b(?!\s+(?:as\s+)?a\b)',
                'a_sight a',
                fixed_sql,
                count=1,
                flags=re.IGNORECASE
            )
            if count_a:
                alias_adjusted = True

        # 修复 tourist_spot 表的别名定义
        if uses_t:
            fixed_sql, count_t = re.subn(
                r'\btourist_spot\b(?!\s+(?:as\s+)?t\b)',
                'tourist_spot t',
                fixed_sql,
                count=1,
                flags=re.IGNORECASE
            )
            if count_t:
                alias_adjusted = True

        sql_lower = fixed_sql.lower()
        
        # 检查是否需要添加FROM子句
        needs_default_from = 'from' not in sql_lower
        
        # 检查别名是否已定义
        for alias in used_aliases:
            # 检查FROM子句中是否定义了该别名
            if not re.search(rf'\bfrom\s+.*\b(?:as\s+)?{alias}\b', sql_lower):
                needs_default_from = True
                break

        # 如果需要添加FROM子句，构建合适的FROM子句
        if needs_default_from:
            # 根据使用的别名构建FROM子句
            default_from = self._build_enhanced_from_clause(used_aliases)

            from_match = re.search(r'\bfrom\b', fixed_sql, re.IGNORECASE)
            if from_match:
                # 已有FROM子句但别名定义不完整，需要重建
                after_from = fixed_sql[from_match.end():]
                boundary_match = re.search(
                    r'\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|\bHAVING\b|\bUNION\b|\bEXCEPT\b|\bINTERSECT\b',
                    after_from,
                    re.IGNORECASE
                )
                if boundary_match:
                    end_index = from_match.end() + boundary_match.start()
                else:
                    end_index = len(fixed_sql)

                original_from_segment = fixed_sql[from_match.start():end_index]
                trailing_clause = fixed_sql[end_index:]

                # 保留原有的JOIN子句
                join_pattern = re.compile(
                    r'\b(?:INNER|LEFT|RIGHT|FULL|CROSS)\s+JOIN\b|\bJOIN\b',
                    re.IGNORECASE
                )
                join_match = join_pattern.search(original_from_segment)
                trailing_joins = ''
                if join_match:
                    trailing_joins = original_from_segment[join_match.start():].strip()

                # 重建FROM子句
                rebuilt_from = default_from.rstrip(newline)
                if trailing_joins:
                    rebuilt_from = f"{rebuilt_from}{newline}{trailing_joins.strip()}"
                rebuilt_from = f"{rebuilt_from}{newline}"

                prefix = fixed_sql[:from_match.start()].rstrip()
                if prefix and not prefix.endswith(newline):
                    prefix += newline
                suffix = trailing_clause.lstrip()
                fixed_sql = f"{prefix}{rebuilt_from}{suffix}"
            else:
                # 完全没有FROM子句，需要插入
                before_where = re.search(r'\bWHERE\b', fixed_sql, re.IGNORECASE)
                if before_where:
                    prefix = fixed_sql[:before_where.start()].rstrip()
                    if prefix and not prefix.endswith(newline):
                        prefix += newline
                    suffix = fixed_sql[before_where.start():]
                    fixed_sql = f"{prefix}{default_from}{suffix}"
                else:
                    trimmed = fixed_sql.rstrip()
                    if trimmed and not trimmed.endswith(newline):
                        trimmed += newline
                    fixed_sql = f"{trimmed}{default_from}"

            self.logger.info(f"Auto-rebuilt FROM clause for aliases: {used_aliases}")
        else:
            if alias_adjusted:
                self.logger.info("Auto-added missing table aliases in FROM clause")
            else:
                self.logger.info("SQL structure appears valid, no changes needed")

        # 最终验证修复后的SQL
        if not self._validate_sql_structure(fixed_sql):
            self.logger.warning("Auto-repair failed, SQL structure still invalid")
            # 如果自动修复失败，记录详细信息用于调试
            self.logger.debug(f"Failed to repair SQL: {fixed_sql}")

        return fixed_sql


def test_sql_validation():
    """测试SQL验证功能"""
    print("\n=== 测试SQL验证功能 ===\n")
    
    # 创建模拟SQL生成器
    generator = MockSQLGenerator()
    
    # 测试用例：有问题的SQL语句
    test_cases = [
        {
            "name": "缺少FROM子句",
            "sql": "SELECT a.name, a.level WHERE a.level = '5A'",
            "expected_valid": False
        },
        {
            "name": "使用别名但未定义",
            "sql": "SELECT a.name, t.评分 FROM a_sight",
            "expected_valid": False
        },
        {
            "name": "多表连接别名不完整",
            "sql": "SELECT a.name, t.评分 FROM a_sight a JOIN tourist_spot",
            "expected_valid": False
        },
        {
            "name": "正确的SQL",
            "sql": "SELECT a.name, a.level FROM a_sight a WHERE a.level = '5A'",
            "expected_valid": True
        },
        {
            "name": "多表连接正确的SQL",
            "sql": "SELECT a.name, t.评分 FROM a_sight a LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'",
            "expected_valid": True
        },
        {
            "name": "使用AS关键字的正确SQL",
            "sql": "SELECT a.name, t.评分 FROM a_sight AS a LEFT JOIN tourist_spot AS t ON t.name LIKE a.name || '%'",
            "expected_valid": True
        }
    ]
    
    for test_case in test_cases:
        print(f"测试: {test_case['name']}")
        print(f"SQL: {test_case['sql']}")
        
        is_valid = generator._validate_sql_structure(test_case['sql'])
        
        print(f"验证结果: {'通过' if is_valid else '失败'}")
        print(f"期望结果: {'通过' if test_case['expected_valid'] else '失败'}")
        
        if is_valid == test_case['expected_valid']:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
        
        print("-" * 50)


def test_sql_repair():
    """测试SQL自动修复功能"""
    print("\n=== 测试SQL自动修复功能 ===\n")
    
    # 创建模拟SQL生成器
    generator = MockSQLGenerator()
    
    # 测试用例：有问题的SQL语句和期望的修复
    test_cases = [
        {
            "name": "缺少FROM子句的简单查询",
            "sql": "SELECT a.name, a.level WHERE a.level = '5A'",
            "query": "查询5A景区"
        },
        {
            "name": "使用别名但未定义",
            "sql": "SELECT a.name, t.评分 FROM a_sight",
            "query": "查询景区评分"
        },
        {
            "name": "多表连接缺少别名定义",
            "sql": "SELECT a.name, t.评分 FROM a_sight JOIN tourist_spot",
            "query": "查询景区详细信息"
        },
        {
            "name": "复杂的多表查询",
            "sql": "SELECT a.name, a.level, t.评分, t.门票 FROM WHERE a.level = '5A' AND t.评分 > 4.0",
            "query": "查询高评分5A景区"
        }
    ]
    
    for test_case in test_cases:
        print(f"测试: {test_case['name']}")
        print(f"原始SQL: {test_case['sql']}")
        
        # 验证原始SQL（应该失败）
        original_valid = generator._validate_sql_structure(test_case['sql'])
        print(f"原始SQL验证: {'通过' if original_valid else '失败'}")
        
        # 尝试修复
        repaired_sql = generator._add_from_clause_if_missing(test_case['sql'], test_case['query'])
        print(f"修复后SQL: {repaired_sql}")
        
        # 验证修复后的SQL
        repaired_valid = generator._validate_sql_structure(repaired_sql)
        print(f"修复后验证: {'通过' if repaired_valid else '失败'}")
        
        if repaired_valid:
            print("✅ 修复成功")
        else:
            print("❌ 修复失败")
        
        print("-" * 50)


def test_error_scenarios():
    """测试特定错误场景"""
    print("\n=== 测试特定错误场景 ===\n")
    
    # 创建模拟SQL生成器
    generator = MockSQLGenerator()
    
    # 模拟用户报告的错误场景
    error_scenarios = [
        {
            "name": "用户报告的错误 - 丢失FROM子句项",
            "sql": "SELECT 'name', COALESCE(ts.name, a.name) FROM WHERE a.level = '5A'",
            "error": "对于表'a',丢失FROM子句项",
            "query": "查询景区名称"
        },
        {
            "name": "复杂查询中的别名问题",
            "sql": "SELECT a.name, t.评分, (SELECT COUNT(*) FROM tourist_spot WHERE level = a.level) as count FROM WHERE a.level = '5A'",
            "error": "对于表'a',丢失FROM子句项",
            "query": "查询各等级景区数量"
        }
    ]
    
    for scenario in error_scenarios:
        print(f"场景: {scenario['name']}")
        print(f"错误SQL: {scenario['sql']}")
        print(f"错误信息: {scenario['error']}")
        
        # 验证原始SQL
        original_valid = generator._validate_sql_structure(scenario['sql'])
        print(f"原始SQL验证: {'通过' if original_valid else '失败'}")
        
        if not original_valid:
            # 尝试自动修复
            repaired_sql = generator._add_from_clause_if_missing(scenario['sql'], scenario['query'])
            print(f"自动修复后SQL: {repaired_sql}")
            
            # 验证修复结果
            repaired_valid = generator._validate_sql_structure(repaired_sql)
            print(f"自动修复验证: {'通过' if repaired_valid else '失败'}")
            
            if repaired_valid:
                print("✅ 自动修复成功")
            else:
                print("❌ 自动修复失败 - 需要更复杂的修复机制")
        
        print("-" * 50)


def main():
    """主测试函数"""
    print("开始测试SQL FROM子句修复功能...")
    
    try:
        # 测试SQL验证功能
        test_sql_validation()
        
        # 测试SQL自动修复功能
        test_sql_repair()
        
        # 测试特定错误场景
        test_error_scenarios()
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
