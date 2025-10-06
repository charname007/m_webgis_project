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
        timeout: int = 90,  # 默认超时时间从30秒增加到90秒
        max_rows: int = 1000,
        enable_optimization: bool = True,
        enable_timeout: bool = True,
        max_retries: int = 3  # 添加最大重试次数
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
        self.max_retries = max_retries  # 最大重试次数
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
        """Execute SQL with optional timeout and keep statistics."""
        return self._execute_with_retry(sql)

    def _execute_with_retry(self, sql: str) -> Dict[str, Any]:
        """
        带智能重试机制的SQL执行
        
        新策略:
        - 超时错误: 立即返回完整错误上下文，不重试
        - 其他错误: 按原策略重试
        
        Args:
            sql: SQL语句
            
        Returns:
            执行结果
        """
        retry_count = 0
        last_error = None
        last_error_type = None
        
        while retry_count <= self.max_retries:
            try:
                # 根据重试次数调整超时时间
                current_timeout = self._get_retry_timeout(retry_count)
                
                # 根据重试次数优化SQL
                current_sql = self._get_retry_sql(sql, retry_count)
                
                self.logger.info(f"执行 {retry_count}/{self.max_retries}: 超时={current_timeout}s, SQL={current_sql[:200]}...")
                
                # 执行查询
                result = self._execute_single_query(current_sql, current_timeout)
                
                if result["status"] == "success":
                    self.logger.info(f"执行成功: 第{retry_count}次执行")
                    return result
                else:
                    last_error = result.get("error")
                    last_error_type = result.get("error_type")
                    
                    # 如果是超时错误，立即返回完整错误上下文，不重试
                    if last_error_type == "TIMEOUT_ERROR":
                        self.logger.warning(f"查询超时，立即返回错误上下文: {last_error}")
                        return {
                            "status": "timeout_immediate_retry",
                            "data": None,
                            "count": 0,
                            "raw_result": None,
                            "error": last_error,
                            "error_type": last_error_type,
                            "failed_sql": current_sql,
                            "query_complexity": self._analyze_query_complexity(current_sql),
                            "optimization_suggestions": self._generate_optimization_suggestions(current_sql, last_error_type, "high")
                        }
                    else:
                        self.logger.warning(f"执行失败: 第{retry_count}次执行, 错误: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                last_error_type = self._classify_error(last_error)
                self.logger.warning(f"执行异常: 第{retry_count}次执行, 异常: {last_error}")
            
            retry_count += 1
            if retry_count <= self.max_retries:
                # 重试间隔
                time.sleep(2)
        
        # 所有重试都失败
        self.logger.error(f"所有重试都失败: {last_error}")
        return {
            "status": "error",
            "data": None,
            "count": 0,
            "raw_result": None,
            "error": f"查询失败，经过{self.max_retries}次重试: {last_error}",
            "error_type": "RETRY_EXHAUSTED"
        }

    def _get_retry_timeout(self, retry_count: int) -> int:
        """根据重试次数获取超时时间"""
        timeout_increments = [90, 120, 150, 180]  # 逐步增加超时时间
        if retry_count < len(timeout_increments):
            return timeout_increments[retry_count]
        return timeout_increments[-1]  # 使用最大超时时间

    def _get_retry_sql(self, original_sql: str, retry_count: int) -> str:
        """根据重试次数优化SQL"""
        if retry_count == 0:
            # 第一次重试: 保持原查询
            return original_sql
        elif retry_count == 1:
            # 第二次重试: 简化查询条件
            return self._simplify_query(original_sql)
        else:
            # 第三次及以后重试: 限制返回数据量
            return self._limit_query_results(original_sql)

    def _simplify_query(self, sql: str) -> str:
        """简化查询条件"""
        # 移除复杂的JOIN条件
        simplified_sql = re.sub(r'\bFULL\s+OUTER\s+JOIN\b', 'LEFT JOIN', sql, flags=re.IGNORECASE)
        simplified_sql = re.sub(r'\bCROSS\s+JOIN\b', 'INNER JOIN', simplified_sql, flags=re.IGNORECASE)
        
        # 移除复杂的子查询
        if self._has_complex_subquery(simplified_sql):
            simplified_sql = self._remove_complex_subqueries(simplified_sql)
            
        self.logger.info(f"简化查询: {simplified_sql[:200]}...")
        return simplified_sql

    def _limit_query_results(self, sql: str) -> str:
        """限制查询结果数量"""
        if self._is_select_query(sql) and not self._has_limit(sql):
            limited_sql = self._add_limit(sql, min(self.max_rows, 100))  # 限制为100条
            self.logger.info(f"限制结果数量: {limited_sql[:200]}...")
            return limited_sql
        return sql

    def _remove_complex_subqueries(self, sql: str) -> str:
        """移除复杂子查询"""
        # 这里可以实现具体的子查询移除逻辑
        # 目前返回原始SQL，后续可以扩展
        return sql

    def _execute_single_query(self, sql: str, timeout: int) -> Dict[str, Any]:
        """执行单次查询"""
        start_time = time.time()
        self.stats["total_queries"] += 1

        optimized_sql = sql
        optimized_applied = False

        try:
            if self.enable_optimization:
                candidate_sql = self._optimize_sql(sql)
                if candidate_sql != sql:
                    self.stats["optimized_queries"] += 1
                    self.logger.info(f"SQL optimized: {candidate_sql[:200]}...")
                    optimized_applied = True
                optimized_sql = candidate_sql

            # 临时设置超时时间
            original_timeout = self.timeout
            self.timeout = timeout
            
            if self.enable_timeout:
                result = self._execute_with_timeout(optimized_sql)
            else:
                result = self._execute_directly(optimized_sql)
                
            # 恢复原始超时时间
            self.timeout = original_timeout

            status = result.get("status", "success")
            if status == "timeout":
                raise TimeoutError(result.get("error") or f"Query timed out after {timeout}s")
            if status == "error":
                raise RuntimeError(result.get("error") or "SQL execution failed")

            execution_time = time.time() - start_time
            self.stats["total_execution_time"] += execution_time
            self.stats["successful_queries"] += 1
            self.stats["average_execution_time"] = (
                self.stats["total_execution_time"] / self.stats["successful_queries"]
            )

            result["execution_time"] = execution_time
            result["optimized"] = optimized_applied

            self.logger.info(
                f"SQL executed successfully: {execution_time:.2f}s, rows={result.get('count', 0)}"
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"SQL execution failed after {execution_time:.2f}s: {e}")
            self.stats["total_execution_time"] += execution_time
            self.stats["failed_queries"] += 1
            self.stats["average_execution_time"] = (
                self.stats["total_execution_time"] /
                max(self.stats["successful_queries"], 1)
            )

            return self._handle_execution_error(optimized_sql, e, execution_time)
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
        
        # 分析查询复杂度
        query_complexity = self._analyze_query_complexity(sql)
        
        return {
            "status": "error",
            "data": None,
            "count": 0,
            "raw_result": None,
            "error": error_message,
            "error_type": error_type,
            "execution_time": execution_time,
            "failed_sql": sql,  # 包含完整的SQL语句
            "query_complexity": query_complexity,  # 查询复杂度分析
            "optimization_suggestions": self._generate_optimization_suggestions(sql, error_type, query_complexity)
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

    def _analyze_query_complexity(self, sql: str) -> str:
        """
        分析查询复杂度
        
        Args:
            sql: SQL语句
            
        Returns:
            复杂度等级: "low", "medium", "high"
        """
        complexity_score = 0
        
        # 检查复杂JSON构建
        if re.search(r'json_agg\s*\(\s*json_build_object', sql, re.IGNORECASE):
            complexity_score += 3
        
        # 检查多表JOIN
        join_count = len(re.findall(r'\bJOIN\b', sql, re.IGNORECASE))
        complexity_score += min(join_count, 3)
        
        # 检查子查询
        subquery_count = len(re.findall(r'\(\s*SELECT', sql, re.IGNORECASE))
        complexity_score += min(subquery_count, 2)
        
        # 检查复杂函数
        if re.search(r'\bCOALESCE\b.*\bCOALESCE\b', sql, re.IGNORECASE):
            complexity_score += 1
        
        # 检查UNION/UNION ALL
        if re.search(r'\bUNION\s+ALL\b|\bUNION\b', sql, re.IGNORECASE):
            complexity_score += 2
        
        # 确定复杂度等级
        if complexity_score >= 5:
            return "high"
        elif complexity_score >= 3:
            return "medium"
        else:
            return "low"

    def _generate_optimization_suggestions(self, sql: str, error_type: str, complexity: str) -> List[str]:
        """
        生成优化建议
        
        Args:
            sql: SQL语句
            error_type: 错误类型
            complexity: 查询复杂度
            
        Returns:
            优化建议列表
        """
        suggestions = []
        
        # 基于错误类型的建议
        if error_type == "TIMEOUT_ERROR":
            suggestions.append("查询执行超时，建议简化查询结构")
            
            # 基于复杂度的具体建议
            if complexity == "high":
                suggestions.extend([
                    "简化复杂的JSON构建结构",
                    "减少JOIN表数量",
                    "添加LIMIT限制结果数量",
                    "考虑分步查询而不是单次复杂查询"
                ])
            elif complexity == "medium":
                suggestions.extend([
                    "优化JOIN条件",
                    "添加适当的索引",
                    "限制返回字段数量"
                ])
        
        # 基于SQL结构的建议
        if re.search(r'json_agg\s*\(\s*json_build_object', sql, re.IGNORECASE):
            suggestions.append("考虑使用简单的SELECT查询代替复杂的JSON构建")
        
        if len(re.findall(r'\bJOIN\b', sql, re.IGNORECASE)) > 2:
            suggestions.append("减少JOIN表数量或使用更简单的JOIN类型")
        
        if not re.search(r'\bLIMIT\s+\d+', sql, re.IGNORECASE):
            suggestions.append("添加LIMIT子句限制返回结果数量")
        
        # 移除重复建议
        return list(set(suggestions))

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
