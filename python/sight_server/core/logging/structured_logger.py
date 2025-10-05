"""
结构化日志记录器 - Sight Server

提供JSON格式的结构化日志，方便后续分析和查询
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pathlib import Path


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogType(str, Enum):
    """日志类型枚举"""
    QUERY_START = "query_start"          # 查询开始
    QUERY_END = "query_end"              # 查询结束
    SQL_EXECUTION = "sql_execution"      # SQL执行
    ERROR_OCCURRED = "error_occurred"    # 错误发生
    ERROR_RETRY = "error_retry"          # 错误重试
    ERROR_RECOVERED = "error_recovered"  # 错误恢复
    NODE_EXECUTION = "node_execution"    # 节点执行
    PERFORMANCE = "performance"          # 性能记录


class StructuredLogger:
    """
    结构化日志记录器

    功能：
    - JSON格式日志输出
    - 支持日志级别和类型分类
    - 自动记录时间戳
    - 可配置日志文件路径
    """

    def __init__(
        self,
        log_file: str = "logs/sight_server.jsonl",
        enable_console: bool = True
    ):
        """
        初始化结构化日志记录器

        Args:
            log_file: 日志文件路径（JSONL格式）
            enable_console: 是否同时输出到控制台
        """
        self.log_file = log_file
        self.enable_console = enable_console

        # 确保日志目录存在
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 配置文件日志处理器
        self.file_logger = logging.getLogger(f"{__name__}.file")
        self.file_logger.setLevel(logging.INFO)

        # 清除现有处理器（避免重复）
        self.file_logger.handlers.clear()

        # 添加文件处理器（JSON行格式）
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        self.file_logger.addHandler(file_handler)

        # 配置控制台日志处理器（可选）
        if enable_console:
            self.console_logger = logging.getLogger(f"{__name__}.console")
            self.console_logger.setLevel(logging.INFO)
            self.console_logger.handlers.clear()

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
            )
            self.console_logger.addHandler(console_handler)

    def log(
        self,
        log_type: LogType,
        level: LogLevel = LogLevel.INFO,
        **kwargs
    ):
        """
        记录结构化日志

        Args:
            log_type: 日志类型
            level: 日志级别
            **kwargs: 额外的日志字段
        """
        # 构建日志条目
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": log_type.value,
            "level": level.value,
            **kwargs
        }

        # 写入文件（JSON行格式）
        json_line = json.dumps(log_entry, ensure_ascii=False)
        self.file_logger.info(json_line)

        # 可选：输出到控制台（格式化）
        if self.enable_console:
            console_msg = f"[{log_type.value}] {kwargs.get('message', json_line[:100])}"
            if level == LogLevel.ERROR or level == LogLevel.CRITICAL:
                self.console_logger.error(console_msg)
            elif level == LogLevel.WARNING:
                self.console_logger.warning(console_msg)
            else:
                self.console_logger.info(console_msg)

    # ==================== 快捷方法 ====================

    def log_query_start(self, query: str, query_id: str, **context):
        """记录查询开始"""
        self.log(
            LogType.QUERY_START,
            query=query,
            query_id=query_id,
            message=f"查询开始: {query[:50]}...",
            **context
        )

    def log_query_end(
        self,
        query_id: str,
        status: str,
        duration_ms: float,
        **result
    ):
        """记录查询结束"""
        self.log(
            LogType.QUERY_END,
            query_id=query_id,
            status=status,
            duration_ms=duration_ms,
            message=f"查询结束: {status} ({duration_ms:.2f}ms)",
            **result
        )

    def log_sql_execution(
        self,
        query_id: str,
        sql: str,
        step: int,
        status: str,
        duration_ms: float = 0,
        rows_returned: int = 0,
        error: Optional[str] = None
    ):
        """记录SQL执行"""
        self.log(
            LogType.SQL_EXECUTION,
            level=LogLevel.ERROR if error else LogLevel.INFO,
            query_id=query_id,
            sql=sql[:500],  # 截断过长SQL
            step=step,
            status=status,
            duration_ms=duration_ms,
            rows_returned=rows_returned,
            error=error,
            message=f"SQL执行[步骤{step}]: {status}"
        )

    def log_error(
        self,
        query_id: str,
        error_type: str,
        error_message: str,
        failed_sql: Optional[str] = None,
        retry_count: int = 0,
        recovery_strategy: Optional[str] = None,
        **context
    ):
        """记录错误"""
        self.log(
            LogType.ERROR_OCCURRED,
            level=LogLevel.ERROR,
            query_id=query_id,
            error_type=error_type,
            error_message=error_message,
            failed_sql=failed_sql[:300] if failed_sql else None,  # 截断SQL
            retry_count=retry_count,
            recovery_strategy=recovery_strategy,
            message=f"错误发生[{error_type}]: {error_message[:100]}...",
            **context
        )

    def log_error_retry(
        self,
        query_id: str,
        retry_count: int,
        strategy: str,
        **context
    ):
        """记录错误重试"""
        self.log(
            LogType.ERROR_RETRY,
            level=LogLevel.WARNING,
            query_id=query_id,
            retry_count=retry_count,
            strategy=strategy,
            message=f"错误重试[第{retry_count}次]: 策略={strategy}",
            **context
        )

    def log_error_recovered(
        self,
        query_id: str,
        retry_count: int,
        final_strategy: str,
        **context
    ):
        """记录错误恢复"""
        self.log(
            LogType.ERROR_RECOVERED,
            level=LogLevel.INFO,
            query_id=query_id,
            retry_count=retry_count,
            final_strategy=final_strategy,
            message=f"错误已恢复[经{retry_count}次重试]: 最终策略={final_strategy}",
            **context
        )

    def log_node_execution(
        self,
        query_id: str,
        node_name: str,
        step: int,
        duration_ms: float,
        status: str,
        **details
    ):
        """记录节点执行"""
        self.log(
            LogType.NODE_EXECUTION,
            query_id=query_id,
            node_name=node_name,
            step=step,
            duration_ms=duration_ms,
            status=status,
            message=f"节点执行[{node_name}]: {status} ({duration_ms:.2f}ms)",
            **details
        )

    def log_performance(
        self,
        query_id: str,
        operation: str,
        duration_ms: float,
        **metrics
    ):
        """记录性能指标"""
        self.log(
            LogType.PERFORMANCE,
            query_id=query_id,
            operation=operation,
            duration_ms=duration_ms,
            message=f"性能记录[{operation}]: {duration_ms:.2f}ms",
            **metrics
        )


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=== 测试结构化日志记录器 ===\n")

    # 创建日志记录器
    logger = StructuredLogger(
        log_file="logs/test_structured.jsonl",
        enable_console=True
    )

    query_id = "test-query-001"

    # 测试查询开始
    logger.log_query_start(
        query="查询浙江省的5A景区",
        query_id=query_id,
        user_id="test_user"
    )

    # 测试SQL执行
    logger.log_sql_execution(
        query_id=query_id,
        sql="SELECT * FROM a_sight WHERE province = '浙江省'",
        step=1,
        status="success",
        duration_ms=15.5,
        rows_returned=19
    )

    # 测试错误记录
    logger.log_error(
        query_id=query_id,
        error_type="sql_syntax_error",
        error_message='column "xxx" does not exist',
        failed_sql="SELECT xxx FROM a_sight",
        retry_count=1
    )

    # 测试错误重试
    logger.log_error_retry(
        query_id=query_id,
        retry_count=1,
        strategy="retry_sql"
    )

    # 测试错误恢复
    logger.log_error_recovered(
        query_id=query_id,
        retry_count=2,
        final_strategy="retry_sql"
    )

    # 测试节点执行
    logger.log_node_execution(
        query_id=query_id,
        node_name="generate_sql",
        step=1,
        duration_ms=120.3,
        status="completed"
    )

    # 测试查询结束
    logger.log_query_end(
        query_id=query_id,
        status="success",
        duration_ms=250.8,
        count=19
    )

    print("\n✅ 日志已记录到: logs/test_structured.jsonl")
    print("请查看文件内容验证JSON格式")
