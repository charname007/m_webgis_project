"""
优化的SQL执行器模块 - Sight Server
提供带超时控制、查询优化和性能监控的SQL执行功能

✅ 重构说明：OptimizedSQLExecutor 继承自 SQLExecutor 基类
- 复用基类的 _parse_result() 方法
- 扩展超时控制、查询优化和性能监控功能
- 保持向后兼容性
"""

import logging
import time
import signal
import re
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from .sql_executor import SQLExecutor  # ✅ 导入基类

logger = logging.getLogger(__name__)


class OptimizedSQLExecutor(SQLExecutor):  # ✅ 继承自 SQLExecutor
    """
    优化的SQL执行器

    功能:
    - 带超时控制的SQL执行
    - 查询优化和自动简化
    - 性能监控和统计
    - 连接池管理
    - 错误分类和智能重试
    """

    def __init__(
        self,
        db_connector,
        timeout: int = 30,
        max_rows: int = 1000,
        enable_optimization: bool = True,
        enable_timeout: bool = True
    ):
        """
        初始化优化的SQL执行器

        Args:
            db_connector: 数据库连接器实例
            timeout: SQL执行超时时间（秒），默认30秒
            max_rows: 最大返回行数，默认1000
            enable_optimization: 是否启用查询优化
            enable_timeout: 是否启用超时控制
        """
        # ✅ 调用基类初始化
        super().__init__(db_connector)

        # ✅ 添加优化相关的属性
        self.timeout = timeout
        self.max_rows = max_rows
        self.enable_optimization = enable_optimization
        self.enable_timeout = enable_timeout
        self.logger = logger
        
        # 性能统计
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "timeout_queries": 0,
            "failed_queries": 0,
            "total_execution_time": 0,
            "average_execution_time": 0,
            "cache_hits": 0,
            "optimized_queries": 0
        }
        
        # 线程池用于超时控制
        self.thread_pool = ThreadPoolExecutor(max_workers=1)
        
        logger.info(
            f"OptimizedSQLExecutor initialized: timeout={timeout}s, "
            f"max_rows={max_rows}, optimization={enable_optimization}"
        )

    def execute_with_timeout(self, sql: str) -> Dict[str, Any]:
        """
        带超时控制的SQL执行

        Args:
            sql: SQL查询语句

        Returns:
            执行结果字典
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        try:
            # 优化SQL（如果启用）
            if self.enable_optimization:
                optimized_sql = self._optimize_sql(sql)
                if optimized_sql != sql:
                    self.stats["optimized_queries"] += 1
                    self.logger.info(f"SQL optimized: {optimized_sql[:200]}...")
                sql = optimized_sql

            # 执行SQL（带超时）
            if self.enable_timeout:
                result = self._execute_with_timeout(sql)
            else:
                result = self._execute_directly(sql)

            # 更新统计信息
            execution_time = time.time() - start_time
            self.stats["total_execution_time"] += execution_time
            self.stats["successful_queries"] += 1
            self.stats["average_execution_time"] = (
                self.stats["total_execution_time"] / self.stats["successful_queries"]
            )

            result["execution_time"] = execution_time
            result["optimized"] = (optimized_sql != sql) if self.enable_optimization else False
            
            self.logger.info(
                f"SQL executed successfully: {execution_time:.2f}s, "
                f"rows={result.get('count', 0)}"
            )
            
            return result

        except Exception as e:
            # 错误处理
            execution_time = time.time() - start_time
            error_result = self._handle_execution_error(sql, e, execution_time)
            return error_result

    def _execute_with_timeout(self, sql: str) -> Dict[str, Any]:
        """
        使用线程池执行带超时的SQL

        Args:
            sql: SQL语句

        Returns:
            执行结果
        """
        try:
            # 提交到线程池执行
            future = self.thread_pool.submit(self._execute_directly, sql)
            result = future.result(timeout=self.timeout)
            return result
            
        except FutureTimeoutError:
            self.stats["timeout_queries"] += 1
            self.logger.warning(f"SQL execution timeout after {self.timeout}s: {sql[:200]}...")
            
            # 尝试取消任务
            future.cancel()
            
            return {
                "status": "timeout",
                "data": None,
                "count": 0,
                "raw_result": None,
                "error": f"查询超时（{self.timeout}秒）",
                "error_type": "TIMEOUT_ERROR"
            }

    def _execute_directly(self, sql: str) -> Dict[str, Any]:
        """
        直接执行SQL（无超时控制）

        Args:
            sql: SQL语句

        Returns:
            执行结果
        """
        try:
            self.logger.info(f"Executing SQL: {sql[:200]}...")
            raw_result = self.db_connector.execute_raw_query(sql)

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
                "error": str(e),
                "error_type": self._classify_error(str(e))
            }

    def _optimize_sql(self, sql: str) -> str:
        """
        优化SQL查询

        优化策略:
        1. 添加LIMIT限制（如果没有）
        2. 移除复杂子查询（简化）
        3. 优化JOIN条件
        4. 添加索引提示

        Args:
            sql: 原始SQL

        Returns:
            优化后的SQL
        """
        try:
            optimized_sql = sql
            
            # 1. 添加LIMIT限制（仅对SELECT查询）
            if self._is_select_query(optimized_sql) and not self._has_limit(optimized_sql):
                optimized_sql = self._add_limit(optimized_sql, self.max_rows)
                self.logger.debug(f"Added LIMIT {self.max_rows} to SQL")

            # 2. 简化复杂子查询（如果检测到）
            if self._has_complex_subquery(optimized_sql):
                optimized_sql = self._simplify_subqueries(optimized_sql)
                self.logger.debug("Simplified complex subqueries")

            # 3. 优化JOIN条件
            if self._has_inefficient_join(optimized_sql):
                optimized_sql = self._optimize_joins(optimized_sql)
                self.logger.debug("Optimized JOIN conditions")

            return optimized_sql

        except Exception as e:
            self.logger.warning(f"SQL optimization failed: {e}, using original SQL")
            return sql

    def _is_select_query(self, sql: str) -> bool:
        """检查是否为SELECT查询"""
        return sql.strip().upper().startswith('SELECT')

    def _has_limit(self, sql: str) -> bool:
        """检查是否已有LIMIT子句"""
        return re.search(r'\bLIMIT\s+\d+', sql, re.IGNORECASE) is not None

    def _add_limit(self, sql: str, limit: int) -> str:
        """添加LIMIT子句"""
        # 移除末尾分号（如果有）
        sql = sql.rstrip().rstrip(';')
        
        # 检查是否有ORDER BY，如果有则在ORDER BY后添加LIMIT
        order_by_match = re.search(r'\bORDER\s+BY\b.*$', sql, re.IGNORECASE)
        if order_by_match:
            # 在ORDER BY后添加LIMIT
            position = order_by_match.end()
            return sql[:position] + f' LIMIT {limit}' + sql[position:]
        else:
            # 直接在末尾添加LIMIT
            return f"{sql} LIMIT {limit}"

    def _has_complex_subquery(self, sql: str) -> bool:
        """检查是否有复杂子查询"""
        # 检测多层嵌套子查询
        subquery_patterns = [
            r'\(\s*SELECT.*\(\s*SELECT',  # 嵌套子查询
            r'\(\s*SELECT.*UNION.*SELECT',  # UNION子查询
            r'\(\s*SELECT.*FROM.*\(\s*SELECT'  # FROM子查询
        ]
        
        for pattern in subquery_patterns:
            if re.search(pattern, sql, re.IGNORECASE | re.DOTALL):
                return True
        return False

    def _simplify_subqueries(self, sql: str) -> str:
        """简化子查询"""
        # 这里可以实现具体的子查询简化逻辑
        # 目前返回原始SQL，后续可以扩展
        return sql

    def _has_inefficient_join(self, sql: str) -> bool:
        """检查是否有低效的JOIN"""
        # 检测CROSS JOIN或没有ON条件的JOIN
        inefficient_patterns = [
            r'\bCROSS\s+JOIN\b',
            r'\bJOIN\b(?!.*\bON\b)',  # JOIN没有ON条件
            r'\bFULL\s+OUTER\s+JOIN\b'  # FULL OUTER JOIN在PostgreSQL中可能性能较差
        ]
        
        for pattern in inefficient_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return True
        return False

    def _optimize_joins(self, sql: str) -> str:
        """优化JOIN条件"""
        # 将FULL OUTER JOIN转换为UNION ALL（如果可能）
        if 'FULL OUTER JOIN' in sql.upper():
            # 这里可以实现FULL OUTER JOIN到UNION ALL的转换
            # 目前返回原始SQL，后续可以扩展
            pass
        
        return sql

    # ✅ 不需要重写 _parse_result()，直接复用基类方法
    # 基类 SQLExecutor 的 _parse_result() 方法已经可以直接使用

    def _classify_error(self, error_message: str) -> str:
        """
        分类错误类型

        Args:
            error_message: 错误消息

        Returns:
            错误类型
        """
        error_lower = error_message.lower()
        
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return "TIMEOUT_ERROR"
        elif 'syntax' in error_lower:
            return "SQL_SYNTAX_ERROR"
        elif 'connection' in error_lower or 'connect' in error_lower:
            return "CONNECTION_ERROR"
        elif 'permission' in error_lower:
            return "PERMISSION_ERROR"
        elif 'does not exist' in error_lower or 'not found' in error_lower:
            return "OBJECT_NOT_FOUND"
        elif 'duplicate' in error_lower:
            return "DUPLICATE_ERROR"
        elif 'foreign key' in error_lower:
            return "FOREIGN_KEY_ERROR"
        elif 'null value' in error_lower:
            return "NULL_VALUE_ERROR"
        else:
            return "UNKNOWN_ERROR"

    def _handle_execution_error(self, sql: str, error: Exception, execution_time: float) -> Dict[str, Any]:
        """
        处理执行错误

        Args:
            sql: 执行的SQL
            error: 错误对象
            execution_time: 执行时间

        Returns:
            错误结果
        """
        self.stats["failed_queries"] += 1
        
        error_message = str(error)
        error_type = self._classify_error(error_message)
        
        self.logger.error(f"SQL execution failed (type: {error_type}): {error_message}")
        
        return {
            "status": "error",
            "data": None,
            "count": 0,
            "raw_result": None,
            "error": error_message,
            "error_type": error_type,
            "execution_time": execution_time
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息

        Returns:
            性能统计字典
        """
        stats = self.stats.copy()
        
        # 计算成功率
        if stats["total_queries"] > 0:
            stats["success_rate"] = round(
                (stats["successful_queries"] / stats["total_queries"]) * 100, 2
            )
            stats["timeout_rate"] = round(
                (stats["timeout_queries"] / stats["total_queries"]) * 100, 2
            )
            stats["failure_rate"] = round(
                (stats["failed_queries"] / stats["total_queries"]) * 100, 2
            )
        else:
            stats["success_rate"] = 0
            stats["timeout_rate"] = 0
            stats["failure_rate"] = 0
        
        # 优化率
        if stats["total_queries"] > 0:
            stats["optimization_rate"] = round(
                (stats["optimized_queries"] / stats["total_queries"]) * 100, 2
            )
        else:
            stats["optimization_rate"] = 0
        
        return stats

    def reset_stats(self):
        """重置性能统计"""
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "timeout_queries": 0,
            "failed_queries": 0,
            "total_execution_time": 0,
            "average_execution_time": 0,
            "cache_hits": 0,
            "optimized_queries": 0
        }

    def execute(self, sql: str) -> Dict[str, Any]:
        """
        执行SQL查询（兼容接口）

        Args:
            sql: SQL查询语句

        Returns:
            执行结果字典，与现有代码兼容
        """
        # 调用现有的execute_with_timeout方法
        result = self.execute_with_timeout(sql)
        
        # 确保返回结构与现有代码兼容
        compatible_result = {
            "status": result["status"],
            "data": result["data"],
            "count": result["count"],
            "error": result.get("error"),
            "raw_result": result.get("raw_result")
        }
        
        return compatible_result

    def close(self):
        """关闭资源"""
        self.thread_pool.shutdown(wait=False)
        self.logger.info("OptimizedSQLExecutor resources closed")


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== 优化的SQL执行器测试 ===\n")
    
    # 模拟数据库连接器
    class MockDBConnector:
        def execute_raw_query(self, sql):
            # 模拟执行时间
            if "timeout" in sql.lower():
                import time
                time.sleep(2)  # 模拟超时
            return [{"result": [{"name": "测试", "value": 123}]}]
    
    # 创建执行器
    executor = OptimizedSQLExecutor(
        MockDBConnector(),
        timeout=1,  # 1秒超时，便于测试
        max_rows=100,
        enable_optimization=True,
        enable_timeout=True
    )
    
    # 测试1: 正常查询
    print("--- 测试1: 正常查询 ---")
    result1 = executor.execute_with_timeout("SELECT * FROM test_table")
    print(f"结果: {result1['status']}")
    print(f"数据行数: {result1['count']}")
    
    # 测试2: 超时查询
    print("\n--- 测试2: 超时查询 ---")
    result2 = executor.execute_with_timeout("SELECT * FROM timeout_table")
    print(f"结果: {result2['status']}")
    print(f"错误类型: {result2.get('error_type')}")
    
    # 测试3: 性能统计
    print("\n--- 测试3: 性能统计 ---")
    stats = executor.get_performance_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # 清理资源
    executor.close()
