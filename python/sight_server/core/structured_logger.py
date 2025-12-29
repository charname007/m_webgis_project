"""
结构化日志器模块 - Sight Server
提供增强的日志记录和查询功能
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class StructuredLogger:
    """
    结构化日志器

    功能:
    - 记录查询执行过程
    - 记录SQL执行详情
    - 记录错误和重试信息
    - 提供日志查询API
    """

    def __init__(self, log_dir: Optional[str] = None):
        """
        初始化结构化日志器

        Args:
            log_dir: 日志目录路径（可选）
        """
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # 日志文件路径
        self.query_log_file = self.log_dir / "query_log.jsonl"
        self.error_log_file = self.log_dir / "error_log.jsonl"
        self.sql_log_file = self.log_dir / "sql_log.jsonl"
        
        self.logger = logger

    def log_query_start(self, query_id: str, query: str, user_context: Dict[str, Any] = None) -> None:
        """
        记录查询开始

        Args:
            query_id: 查询ID
            query: 用户查询
            user_context: 用户上下文信息
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_id": query_id,
            "event": "query_start",
            "query": query,
            "user_context": user_context or {},
            "status": "started"
        }
        
        self._write_log(self.query_log_file, log_entry)
        self.logger.info(f"[Query {query_id}] Query started: {query}")

    def log_query_end(self, query_id: str, status: str, result_count: int = 0, 
                     execution_time_ms: float = 0, error: str = None) -> None:
        """
        记录查询结束

        Args:
            query_id: 查询ID
            status: 查询状态 (success/error)
            result_count: 结果数量
            execution_time_ms: 执行时间（毫秒）
            error: 错误信息（如果有）
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_id": query_id,
            "event": "query_end",
            "status": status,
            "result_count": result_count,
            "execution_time_ms": execution_time_ms,
            "error": error
        }
        
        self._write_log(self.query_log_file, log_entry)
        self.logger.info(f"[Query {query_id}] Query ended: {status}, count={result_count}, time={execution_time_ms:.0f}ms")

    def log_sql_execution(self, query_id: str, sql: str, step: int, status: str,
                         duration_ms: float, rows_returned: int = 0, error: str = None) -> None:
        """
        记录SQL执行详情

        Args:
            query_id: 查询ID
            sql: SQL语句
            step: 执行步骤
            status: 执行状态 (success/error)
            duration_ms: 执行时间（毫秒）
            rows_returned: 返回行数
            error: 错误信息（如果有）
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_id": query_id,
            "event": "sql_execution",
            "step": step,
            "sql": sql,
            "status": status,
            "duration_ms": duration_ms,
            "rows_returned": rows_returned,
            "error": error
        }
        
        self._write_log(self.sql_log_file, log_entry)
        
        if status == "success":
            self.logger.info(f"[Query {query_id}] SQL step {step} executed: {rows_returned} rows, {duration_ms:.0f}ms")
        else:
            self.logger.error(f"[Query {query_id}] SQL step {step} failed: {error}")

    def log_error(self, query_id: str, error_type: str, error_message: str,
                 failed_sql: str = None, retry_count: int = 0, error_code: str = None) -> None:
        """
        记录错误信息

        Args:
            query_id: 查询ID
            error_type: 错误类型
            error_message: 错误信息
            failed_sql: 失败的SQL（可选）
            retry_count: 重试次数
            error_code: 错误码（可选）
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_id": query_id,
            "event": "error",
            "error_type": error_type,
            "error_message": error_message,
            "failed_sql": failed_sql,
            "retry_count": retry_count,
            "error_code": error_code
        }
        
        self._write_log(self.error_log_file, log_entry)
        self.logger.error(f"[Query {query_id}] Error ({error_type}): {error_message}")

    def log_intent_analysis(self, query_id: str, intent_info: Dict[str, Any]) -> None:
        """
        记录意图分析结果

        Args:
            query_id: 查询ID
            intent_info: 意图分析信息
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_id": query_id,
            "event": "intent_analysis",
            "intent_info": intent_info
        }
        
        self._write_log(self.query_log_file, log_entry)
        self.logger.info(f"[Query {query_id}] Intent analysis: {intent_info}")

    def log_cache_hit(self, query_id: str, cache_key: str, result_count: int) -> None:
        """
        记录缓存命中

        Args:
            query_id: 查询ID
            cache_key: 缓存键
            result_count: 结果数量
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_id": query_id,
            "event": "cache_hit",
            "cache_key": cache_key,
            "result_count": result_count
        }
        
        self._write_log(self.query_log_file, log_entry)
        self.logger.info(f"[Query {query_id}] Cache HIT: {result_count} results")

    def log_cache_save(self, query_id: str, cache_key: str, result_count: int) -> None:
        """
        记录缓存保存

        Args:
            query_id: 查询ID
            cache_key: 缓存键
            result_count: 结果数量
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_id": query_id,
            "event": "cache_save",
            "cache_key": cache_key,
            "result_count": result_count
        }
        
        self._write_log(self.query_log_file, log_entry)
        self.logger.info(f"[Query {query_id}] Cache SAVED: {result_count} results")

    def get_query_logs(self, query_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取查询日志

        Args:
            query_id: 查询ID（可选，用于过滤）
            limit: 返回记录数限制

        Returns:
            查询日志列表
        """
        return self._read_logs(self.query_log_file, query_id, limit)

    def get_sql_logs(self, query_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取SQL执行日志

        Args:
            query_id: 查询ID（可选，用于过滤）
            limit: 返回记录数限制

        Returns:
            SQL日志列表
        """
        return self._read_logs(self.sql_log_file, query_id, limit)

    def get_error_logs(self, query_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取错误日志

        Args:
            query_id: 查询ID（可选，用于过滤）
            limit: 返回记录数限制

        Returns:
            错误日志列表
        """
        return self._read_logs(self.error_log_file, query_id, limit)

    def get_query_statistics(self, query_id: str) -> Dict[str, Any]:
        """
        获取查询统计信息

        Args:
            query_id: 查询ID

        Returns:
            查询统计信息
        """
        query_logs = self.get_query_logs(query_id)
        sql_logs = self.get_sql_logs(query_id)
        error_logs = self.get_error_logs(query_id)

        # 提取查询开始和结束信息
        start_event = next((log for log in query_logs if log.get("event") == "query_start"), None)
        end_event = next((log for log in query_logs if log.get("event") == "query_end"), None)

        # 统计SQL执行情况
        sql_executions = [log for log in sql_logs if log.get("event") == "sql_execution"]
        successful_sql = [log for log in sql_executions if log.get("status") == "success"]
        failed_sql = [log for log in sql_executions if log.get("status") == "error"]

        # 计算总执行时间
        total_duration = sum(log.get("duration_ms", 0) for log in sql_executions)

        return {
            "query_id": query_id,
            "query": start_event.get("query") if start_event else None,
            "status": end_event.get("status") if end_event else "unknown",
            "total_sql_executions": len(sql_executions),
            "successful_sql": len(successful_sql),
            "failed_sql": len(failed_sql),
            "total_duration_ms": total_duration,
            "result_count": end_event.get("result_count", 0) if end_event else 0,
            "errors": len(error_logs),
            "start_time": start_event.get("timestamp") if start_event else None,
            "end_time": end_event.get("timestamp") if end_event else None
        }

    def _write_log(self, log_file: Path, log_entry: Dict[str, Any]) -> None:
        """
        写入日志条目

        Args:
            log_file: 日志文件路径
            log_entry: 日志条目
        """
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write log to {log_file}: {e}")

    def _read_logs(self, log_file: Path, query_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        读取日志文件

        Args:
            log_file: 日志文件路径
            query_id: 查询ID过滤（可选）
            limit: 返回记录数限制

        Returns:
            日志条目列表
        """
        logs = []
        try:
            if not log_file.exists():
                return logs

            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        # 过滤查询ID
                        if query_id and log_entry.get("query_id") != query_id:
                            continue
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue

            # 按时间戳排序（最新的在前）
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # 限制返回数量
            return logs[:limit]

        except Exception as e:
            self.logger.error(f"Failed to read logs from {log_file}: {e}")
            return []

    def cleanup_old_logs(self, days: int = 30) -> None:
        """
        清理旧日志

        Args:
            days: 保留天数
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for log_file in [self.query_log_file, self.sql_log_file, self.error_log_file]:
                if not log_file.exists():
                    continue
                    
                temp_file = log_file.with_suffix(".tmp")
                with open(log_file, "r", encoding="utf-8") as f_in, \
                     open(temp_file, "w", encoding="utf-8") as f_out:
                    
                    for line in f_in:
                        try:
                            log_entry = json.loads(line.strip())
                            timestamp = log_entry.get("timestamp")
                            if timestamp:
                                log_time = datetime.fromisoformat(timestamp).timestamp()
                                if log_time >= cutoff_time:
                                    f_out.write(line)
                        except (json.JSONDecodeError, ValueError):
                            continue
                
                # 替换原文件
                temp_file.replace(log_file)
                
            self.logger.info(f"Cleaned up logs older than {days} days")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== StructuredLogger 测试 ===\n")

    # 创建日志器实例
    slog = StructuredLogger()

    # 测试查询日志
    test_query_id = "test_query_001"
    slog.log_query_start(test_query_id, "查询浙江省的5A景区")
    slog.log_intent_analysis(test_query_id, {
        "intent_type": "query",
        "is_spatial": False,
        "confidence": 0.85
    })
    slog.log_sql_execution(test_query_id, "SELECT * FROM a_sight WHERE level = '5A'", 0, "success", 150, 10)
    slog.log_query_end(test_query_id, "success", 10, 200)

    # 测试错误日志
    slog.log_error(test_query_id, "sql_syntax_error", "语法错误: 缺少FROM子句", "SELECT name FROM", 1, "42601")

    # 测试缓存日志
    slog.log_cache_hit(test_query_id, "cache_key_123", 5)
    slog.log_cache_save(test_query_id, "cache_key_456", 8)

    # 测试查询统计
    stats = slog.get_query_statistics(test_query_id)
    print(f"查询统计: {stats}")

    print("\n=== 测试完成 ===")
