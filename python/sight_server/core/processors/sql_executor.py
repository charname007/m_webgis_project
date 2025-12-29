"""
SQL执行器模块 - Sight Server
负责执行SQL查询并格式化结果
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SQLExecutor:
    """
    SQL执行器

    功能:
    - 执行SQL查询
    - 格式化查询结果
    - 处理执行错误
    """

    def __init__(self, db_connector):
        """
        初始化SQL执行器

        Args:
            db_connector: 数据库连接器实例
        """
        self.db_connector = db_connector
        self.logger = logger

    def execute(self, sql: str) -> Dict[str, Any]:
        """
        执行SQL查询并返回格式化结果

        Args:
            sql: SQL查询语句

        Returns:
            执行结果字典:
            {
                "status": "success" | "error",
                "data": List[Dict] | None,
                "count": int,
                "raw_result": Any,
                "error": str | None
            }
        """
        try:
            # 执行SQL
            self.logger.info(f"Executing SQL: {sql[:200]}...")
            # ✅ 修复：使用execute_raw_query()获取字典列表，而非execute_query()返回的字符串
            raw_result = self.db_connector.execute_raw_query(sql)

            # ✅ 添加详细日志：查看原始结果
            self.logger.info(f"Raw result type: {type(raw_result).__name__}")
            if raw_result:
                self.logger.info(f"Raw result length: {len(raw_result) if hasattr(raw_result, '__len__') else 'N/A'}")
                if isinstance(raw_result, (list, tuple)) and len(raw_result) > 0:
                    self.logger.info(f"First row: {raw_result[0]}")

            # 解析结果
            data = self._parse_result(raw_result)

            return {
                "status": "success",
                "data": data,
                "count": len(data) if data else 0,
                "raw_result": raw_result,
                "error": None
            }

        except Exception as e:
            self.logger.error(f"SQL execution failed: {e}")
            return {
                "status": "error",
                "data": None,
                "count": 0,
                "raw_result": None,
                "error": str(e)
            }

    def _parse_result(self, raw_result: Any) -> Optional[List[Dict[str, Any]]]:
        """
        解析原始SQL执行结果

        处理多种结果格式:
        1. json_agg 返回的 JSON 数组（推荐格式）
        2. 普通行记录列表
        3. 空结果

        Args:
            raw_result: 原始查询结果

        Returns:
            解析后的数据列表，如果无数据则返回None
        """
        # 情况1: 空结果
        if not raw_result:
            self.logger.debug("Parse result: empty result")
            return None

        # ✅ 添加调试日志：查看原始结果类型和值
        self.logger.info(f"Parse result: raw_result type={type(raw_result).__name__}, len={len(raw_result) if hasattr(raw_result, '__len__') else 'N/A'}")
        if isinstance(raw_result, (list, tuple)) and len(raw_result) > 0:
            self.logger.info(f"  First element type: {type(raw_result[0]).__name__}")
            if isinstance(raw_result[0], (list, tuple)) and len(raw_result[0]) > 0:
                self.logger.info(f"  First element[0] type: {type(raw_result[0][0]).__name__}")

        # 情况2: 结果是列表
        if isinstance(raw_result, list) and len(raw_result) > 0:
            first_row = raw_result[0]

            # 情况2a: 第一行是字典（来自 json_agg）
            if isinstance(first_row, dict):
                # 检查是否有 'result' 键（来自 json_agg(...) as result）
                if 'result' in first_row:
                    data = first_row['result']
                    # ✅ 修复：当 json_agg 没有匹配记录时，返回 NULL 而不是空数组
                    if data is None:
                        self.logger.info("Parse result: json_agg returned NULL (no matching records)")
                        return None  # 返回None表示无数据，而不是[None]
                    self.logger.debug(f"Parse result: json_agg with 'result' key, {len(data) if data else 0} records")
                    return data if isinstance(data, list) else [data]
                else:
                    # 整行就是数据
                    self.logger.debug(f"Parse result: dict list, {len(raw_result)} records")
                    return raw_result

            # 情况2b: 第一行是元组/列表（第一列是 json_agg 的结果）
            elif isinstance(first_row, (list, tuple)) and len(first_row) > 0:
                data = first_row[0]
                self.logger.debug(f"Parse result: tuple/list format, extracted from first column, type={type(data).__name__}")

                # ✅ 改进：正确处理 json_agg 结果
                if isinstance(data, list):
                    # 已经是列表，直接返回
                    self.logger.debug(f"  -> Extracted list with {len(data)} records")
                    return data
                elif isinstance(data, dict):
                    # 单个对象，包装成列表
                    self.logger.debug("  -> Extracted single dict, wrapping in list")
                    return [data]
                elif isinstance(data, str):
                    # ✅ 新增：处理JSON字符串（某些驱动返回JSON字符串而非对象）
                    import json
                    try:
                        parsed_data = json.loads(data)
                        if isinstance(parsed_data, list):
                            self.logger.debug(f"  -> Parsed JSON string to list with {len(parsed_data)} records")
                            return parsed_data
                        elif isinstance(parsed_data, dict):
                            self.logger.debug("  -> Parsed JSON string to dict, wrapping in list")
                            return [parsed_data]
                        else:
                            self.logger.warning(f"Unexpected JSON parsed type: {type(parsed_data).__name__}")
                            return None
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse JSON string: {e}, value: {data[:200]}")
                        return None
                else:
                    # ✅ 改进：其他类型（数字、None等）
                    # 可能是统计查询返回的标量值（虽然应该包装为字典）
                    # 或者是格式错误的结果
                    if data is None:
                        self.logger.warning("First column is None, returning empty result")
                        return None
                    else:
                        # 非None标量值：可能是COUNT等聚合函数的直接返回
                        # 包装为标准字典格式
                        self.logger.info(f"Scalar value detected (type={type(data).__name__}, value={data}), wrapping as dict")
                        return [{"result": data}]

            # 情况2c: 其他格式
            else:
                self.logger.debug(f"Parse result: raw list format, {len(raw_result)} records")
                return raw_result

        # 情况3: 单个对象（非列表）
        elif raw_result is not None:
            if isinstance(raw_result, dict):
                self.logger.debug("Parse result: single dict wrapped in list")
                return [raw_result]
            else:
                # 非dict非list对象，记录警告
                self.logger.warning(f"Unexpected result type: {type(raw_result).__name__}")
                return None

        # 情况4: 完全无数据
        self.logger.debug("Parse result: no data")
        return None

    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        验证SQL语法（不执行）

        Args:
            sql: SQL语句

        Returns:
            验证结果:
            {
                "valid": bool,
                "error": str | None,
                "warning": str | None
            }
        """
        result = {
            "valid": True,
            "error": None,
            "warning": None
        }

        # 基本语法检查
        sql_upper = sql.upper()

        # 检查危险操作
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'UPDATE']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                result["valid"] = False
                result["error"] = f"SQL包含危险操作: {keyword}"
                return result

        # 检查是否缺少 SELECT
        if 'SELECT' not in sql_upper:
            result["valid"] = False
            result["error"] = "SQL缺少SELECT语句"
            return result

        # 警告：建议使用 json_agg
        if 'JSON_AGG' not in sql_upper:
            result["warning"] = "建议使用 json_agg 返回 JSON 格式"

        return result


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== SQLExecutor 测试 ===\n")

    # 测试1: 解析 json_agg 结果
    print("--- 测试1: 解析 json_agg 结果 ---")
    executor = SQLExecutor(None)

    test_raw_result = [
        {
            "result": [
                {"name": "西湖", "level": "5A"},
                {"name": "千岛湖", "level": "5A"}
            ]
        }
    ]

    parsed = executor._parse_result(test_raw_result)
    if parsed:
        print(f"Parsed {len(parsed)} records:")
        for record in parsed:
            print(f"  - {record}")
    else:
        print("No records parsed")
    print()

    # 测试2: SQL验证
    print("--- 测试2: SQL验证 ---")

    test_sqls = [
        "SELECT * FROM a_sight LIMIT 10",
        "DROP TABLE a_sight",
        "UPDATE a_sight SET level='5A'",
        "SELECT json_agg(json_build_object('name', name)) FROM a_sight"
    ]

    for sql in test_sqls:
        validation = executor.validate_sql(sql)
        print(f"SQL: {sql[:50]}...")
        print(f"  Valid: {validation['valid']}")
        if validation['error']:
            print(f"  Error: {validation['error']}")
        if validation['warning']:
            print(f"  Warning: {validation['warning']}")
        print()
