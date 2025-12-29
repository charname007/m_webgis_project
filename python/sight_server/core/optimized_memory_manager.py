"""
优化的内存管理器模块 - Sight Server
提供增强的内存管理功能，包括会话自动清理和性能优化

✅ 重构说明：OptimizedMemoryManager 继承自 MemoryManager 基类
- 复用基类的工具方法（_extract_query_template, _is_similar 等）
- 扩展会话管理、自动清理和性能监控功能
- 集成数据库持久化存储
- 保持向后兼容性
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
from .memory import MemoryManager  # ✅ 导入基类
from .cache_manager import DecimalEncoder  # ✅ 导入 DecimalEncoder 处理 Decimal 类型
from .database import DatabaseConnector  # ✅ 导入数据库连接器

logger = logging.getLogger(__name__)


class OptimizedMemoryManager(MemoryManager):  # ✅ 继承自 MemoryManager
    """
    优化的内存管理器

    功能:
    - 短期记忆：管理当前会话的查询历史
    - 长期记忆：跨会话的知识积累
    - 会话自动清理和过期管理
    - 内存使用监控和优化
    - 查询模式学习和性能优化
    - 中间步骤保存和调试追踪
    - 数据库持久化存储支持
    """

    def __init__(
        self,
        max_sessions: int = 100,
        session_ttl: int = 86400,  # 24小时
        enable_auto_cleanup: bool = True,
        cleanup_interval: int = 3600,  # 1小时
        enable_step_saving: bool = True,  # ✅ 新增：启用步骤保存
        step_saving_level: str = "debug",  # ✅ 新增：保存级别 basic/debug/detailed/learning
        max_steps_per_session: int = 1000,  # ✅ 新增：每会话最大步骤数
        enable_step_compression: bool = True,  # ✅ 新增：启用步骤压缩
        enable_database_persistence: bool = True,  # ✅ 新增：启用数据库持久化
        database_connector: Optional[DatabaseConnector] = None  # ✅ 新增：数据库连接器
    ):
        """
        初始化优化的内存管理器

        Args:
            max_sessions: 最大会话数量，默认100
            session_ttl: 会话生存时间（秒），默认24小时
            enable_auto_cleanup: 是否启用自动清理
            cleanup_interval: 自动清理间隔（秒），默认1小时
            enable_step_saving: 是否启用步骤保存，默认True
            step_saving_level: 步骤保存级别，默认"debug"
            max_steps_per_session: 每会话最大步骤数，默认1000
            enable_step_compression: 是否启用步骤压缩，默认True
            enable_database_persistence: 是否启用数据库持久化，默认True
            database_connector: 数据库连接器实例，如果为None则自动创建
        """
        # ✅ 调用基类初始化
        super().__init__()

        # ✅ 添加优化相关的属性
        self.max_sessions = max_sessions
        self.session_ttl = session_ttl
        self.enable_auto_cleanup = enable_auto_cleanup
        self.cleanup_interval = cleanup_interval

        # ✅ 新增：步骤保存相关属性
        self.enable_step_saving = enable_step_saving
        self.step_saving_level = step_saving_level
        self.max_steps_per_session = max_steps_per_session
        self.enable_step_compression = enable_step_compression

        # ✅ 新增：数据库持久化相关属性
        self.enable_database_persistence = enable_database_persistence
        self.database_connector = database_connector or DatabaseConnector()

        # ✅ 定义步骤类型和重要性级别
        self.step_types = {
            "sql_generation": 2,      # 中等重要性
            "sql_execution": 3,       # 高重要性
            "error_recovery": 3,      # 高重要性
            "strategy_decision": 2,   # 中等重要性
            "pattern_matching": 1,    # 低重要性
            "optimization_suggestion": 1,  # 低重要性
            "final_result": 4         # 最高重要性
        }

        # ✅ 定义保存级别规则
        self.saving_level_rules = {
            "basic": ["final_result", "error"],
            "debug": ["sql_generation", "sql_execution", "error_recovery", "strategy_decision"],
            "detailed": ["sql_generation", "sql_execution", "error_recovery", "strategy_decision", "pattern_matching", "optimization_suggestion"],
            "learning": ["sql_generation", "error_recovery", "pattern_matching"]
        }

        # ✅ 覆盖基类的 current_session，使用多会话管理
        # 内存存储
        self.sessions = {}  # 所有会话（替代基类的 current_session）
        self.current_session_id = None  # 当前活跃会话ID

        # ✅ 复用基类的 knowledge_base，添加性能统计
        self.knowledge_base = {
            "common_queries": {},  # 常见查询及其SQL模板
            "optimization_rules": [],  # 查询优化规则
            "failed_patterns": [],  # 失败的查询模式
            "success_patterns": [],  # 成功的查询模式
            "performance_stats": {  # 性能统计
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "average_response_time": 0,
                "cache_hit_rate": 0
            }
        }
        
        # 清理统计
        self.cleanup_stats = {
            "last_cleanup_time": None,
            "total_cleanups": 0,
            "sessions_cleaned": 0,
            "memory_saved_mb": 0
        }
        
        self.logger.info(
            f"OptimizedMemoryManager initialized: max_sessions={max_sessions}, "
            f"session_ttl={session_ttl}s, auto_cleanup={enable_auto_cleanup}, "
            f"step_saving={enable_step_saving} (level: {step_saving_level}), "
            f"database_persistence={enable_database_persistence}"
        )

    def start_session(self, conversation_id: str) -> Dict[str, Any]:
        """
        开始新会话，自动清理旧会话

        Args:
            conversation_id: 会话ID

        Returns:
            初始化的会话状态
        """
        # 自动清理过期会话
        if self.enable_auto_cleanup:
            self._cleanup_old_sessions()

        # 检查会话数量限制
        if len(self.sessions) >= self.max_sessions:
            self._cleanup_oldest_sessions(keep_count=int(self.max_sessions * 0.8))

        # 创建新会话
        current_time = datetime.now()
        self.sessions[conversation_id] = {
            "conversation_id": conversation_id,
            "start_time": current_time.isoformat(),
            "last_accessed": current_time.isoformat(),
            "query_history": [],
            "context": {},
            "performance": {
                "query_count": 0,
                "success_count": 0,
                "total_response_time": 0,
                "average_response_time": 0
            },
            # ✅ 新增：步骤历史记录
            "step_history": [],
            "step_saving_config": {
                "level": self.step_saving_level,
                "max_steps": self.max_steps_per_session,
                "compression_enabled": self.enable_step_compression
            }
        }
        
        self.current_session_id = conversation_id

        # ✅ 新增：保存会话到数据库
        if self.enable_database_persistence:
            try:
                self.database_connector.save_conversation_history(
                    session_id=conversation_id,
                    query_text="SESSION_START",
                    sql_query="",
                    result_data={"status": "session_started"},
                    execution_time=0.0,
                    status="success"
                )
                self.logger.debug(f"Session {conversation_id} saved to database")
            except Exception as e:
                self.logger.warning(f"Failed to save session to database: {e}")

        self.logger.info(f"Started new session: {conversation_id}")

        return {
            "session_history": [],
            "conversation_id": conversation_id,
            "knowledge_base": self.knowledge_base.copy(),
            "learned_patterns": []
        }

    def _cleanup_old_sessions(self) -> int:
        """
        清理过期会话（简化实现）
        
        Returns:
            清理的会话数量
        """
        current_time = datetime.now()
        expired_sessions = []

        for session_id, session in self.sessions.items():
            last_accessed = datetime.fromisoformat(session["last_accessed"])
            time_diff = (current_time - last_accessed).total_seconds()
            
            if time_diff > self.session_ttl:
                expired_sessions.append(session_id)

        # 清理过期会话
        cleaned_count = 0
        for session_id in expired_sessions:
            del self.sessions[session_id]
            cleaned_count += 1
            self.logger.debug(f"Cleaned expired session: {session_id}")

        return cleaned_count

    def _cleanup_oldest_sessions(self, keep_count: int) -> int:
        """
        清理最旧的会话（简化实现）
        
        Args:
            keep_count: 要保留的会话数量
            
        Returns:
            清理的会话数量
        """
        current_size = len(self.sessions)
        if current_size <= keep_count:
            return 0

        # 按最后访问时间排序
        sessions_sorted = sorted(
            self.sessions.items(),
            key=lambda x: datetime.fromisoformat(x[1]["last_accessed"])
        )

        # 删除最旧的会话
        removed_count = 0
        for session_id, session_data in sessions_sorted[:current_size - keep_count]:
            del self.sessions[session_id]
            removed_count += 1
            self.logger.debug(f"Cleaned old session: {session_id}")

        return removed_count

    def _should_save_step(self, step_type: str, importance: int) -> bool:
        """
        判断是否应该保存该步骤（简化实现）
        
        Args:
            step_type: 步骤类型
            importance: 重要性级别
            
        Returns:
            是否应该保存
        """
        # 检查保存级别规则
        allowed_types = self.saving_level_rules.get(self.step_saving_level, [])
        if step_type not in allowed_types:
            return False

        # 检查重要性阈值
        min_importance = self.step_types.get(step_type, 1)
        if importance < min_importance:
            return False

        return True

    def _cleanup_old_steps(self, session: Dict[str, Any], keep_count: int) -> int:
        """
        清理旧步骤（简化实现）
        
        Args:
            session: 会话数据
            keep_count: 要保留的步骤数量
            
        Returns:
            清理的步骤数量
        """
        if "step_history" not in session:
            return 0

        steps = session["step_history"]
        current_size = len(steps)
        if current_size <= keep_count:
            return 0

        # 按时间戳排序，删除最旧的步骤
        steps_sorted = sorted(steps, key=lambda x: x.get("timestamp", ""))
        removed_count = current_size - keep_count

        # 保留最新的步骤
        session["step_history"] = steps_sorted[removed_count:]
        return removed_count

    def _compress_step_data(self, step_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        压缩步骤数据（简化实现）
        
        Args:
            step_record: 原始步骤记录
            
        Returns:
            压缩后的步骤记录
        """
        # 简化实现，直接返回原始记录
        return step_record

    def clear_all_sessions(self) -> int:
        """
        清除所有会话
        
        Returns:
            清除的会话数量
        """
        session_count = len(self.sessions)
        self.sessions.clear()
        self.current_session_id = None
        
        self.logger.info(f"Cleared all {session_count} sessions")
        return session_count

    def add_query_to_session(
        self,
        query: str,
        result: Dict[str, Any],
        sql: str,
        success: bool,
        response_time: float = 0.0
    ) -> Dict[str, Any]:
        """
        添加查询到会话历史，更新性能统计

        Args:
            query: 查询文本
            result: 查询结果
            sql: 执行的SQL
            success: 是否成功
            response_time: 响应时间（秒）

        Returns:
            更新后的会话历史记录
        """
        if self.current_session_id not in self.sessions:
            self.logger.warning(f"No active session found for ID: {self.current_session_id}")
            return {}

        session = self.sessions[self.current_session_id]
        
        # 更新最后访问时间
        session["last_accessed"] = datetime.now().isoformat()

        history_entry = {
            "query": query,
            "sql": sql,
            "success": success,
            "result_count": result.get("count", 0) if result else 0,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }

        session["query_history"].append(history_entry)

        # 更新会话性能统计
        session["performance"]["query_count"] += 1
        if success:
            session["performance"]["success_count"] += 1
        session["performance"]["total_response_time"] += response_time
        
        if session["performance"]["query_count"] > 0:
            session["performance"]["average_response_time"] = (
                session["performance"]["total_response_time"] / 
                session["performance"]["query_count"]
            )

        # ✅ 新增：保存查询历史到数据库
        if self.enable_database_persistence:
            try:
                self.database_connector.save_conversation_history(
                    session_id=self.current_session_id,
                    query_text=query,
                    sql_query=sql,
                    result_data=result,
                    execution_time=response_time,
                    status="success" if success else "error"
                )
                self.logger.debug(f"Query history saved to database for session: {self.current_session_id}")
            except Exception as e:
                self.logger.warning(f"Failed to save query history to database: {e}")

        self.logger.debug(f"Added query to session: {query[:50]}... (response_time: {response_time:.2f}s)")

        return history_entry

    def save_step(
        self,
        step_type: str,
        step_data: Dict[str, Any],
        importance: int = 1,
        session_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        保存中间步骤

        Args:
            step_type: 步骤类型
            step_data: 步骤数据
            importance: 重要性级别 (1-4)
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            保存的步骤记录，如果未保存则返回None
        """
        if not self.enable_step_saving:
            return None

        target_session_id = session_id or self.current_session_id
        if target_session_id not in self.sessions:
            self.logger.warning(f"No active session found for ID: {target_session_id}")
            return None

        session = self.sessions[target_session_id]
        
        # 检查是否应该保存该步骤
        if not self._should_save_step(step_type, importance):
            self.logger.debug(f"Skipping step saving for type: {step_type} (importance: {importance})")
            return None

        # 检查步骤数量限制
        if len(session.get("step_history", [])) >= self.max_steps_per_session:
            self._cleanup_old_steps(session, keep_count=int(self.max_steps_per_session * 0.8))

        # 创建步骤记录
        step_record = {
            "step_type": step_type,
            "step_data": step_data,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
            "session_id": target_session_id
        }

        # 如果需要压缩，则压缩步骤数据
        if self.enable_step_compression:
            step_record = self._compress_step_data(step_record)

        # 添加到步骤历史
        if "step_history" not in session:
            session["step_history"] = []
        session["step_history"].append(step_record)

        # 更新最后访问时间
        session["last_accessed"] = datetime.now().isoformat()

        # ✅ 新增：保存AI上下文到数据库
        if self.enable_database_persistence:
            try:
                self.database_connector.save_ai_context(
                    session_id=target_session_id,
                    context_type=f"step_{step_type}",
                    context_data=step_record
                )
                self.logger.debug(f"Step {step_type} saved to database for session: {target_session_id}")
            except Exception as e:
                self.logger.warning(f"Failed to save step to database: {e}")

        self.logger.debug(f"Saved step: {step_type} (importance: {importance})")
        return step_record

    def learn_from_query(
        self,
        query: str,
        sql: str,
        result: Dict[str, Any],
        success: bool,
        response_time: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        """
        从查询中学习模式，包含性能数据

        Args:
            query: 查询文本
            sql: 执行的SQL
            result: 查询结果
            success: 是否成功
            response_time: 响应时间

        Returns:
            学习到的模式（如果有）
        """
        pattern = {
            "query_template": self._extract_query_template(query),
            "sql_template": self._extract_sql_template(sql),
            "success": success,
            "result_count": result.get("count", 0) if result else 0,
            "response_time": response_time,
            "learned_at": datetime.now().isoformat()
        }

        # 更新知识库性能统计
        self.knowledge_base["performance_stats"]["total_queries"] += 1
        if success:
            self.knowledge_base["performance_stats"]["successful_queries"] += 1
        else:
            self.knowledge_base["performance_stats"]["failed_queries"] += 1

        # 更新平均响应时间
        current_avg = self.knowledge_base["performance_stats"]["average_response_time"]
        total_queries = self.knowledge_base["performance_stats"]["total_queries"]
        self.knowledge_base["performance_stats"]["average_response_time"] = (
            (current_avg * (total_queries - 1) + response_time) / total_queries
        )

        # 如果成功且结果数量 > 0，添加到成功模式
        if success and result.get("count", 0) > 0:
            self.knowledge_base["success_patterns"].append(pattern)
            
            # ✅ 新增：保存学习模式到 pattern_cache 表（使用分离存储）
            if self.enable_database_persistence:
                try:
                    pattern_key = f"success_pattern:{pattern['query_template']}"
                    self.database_connector.save_pattern_cache(
                        pattern_key=pattern_key,
                        query_template=pattern['query_template'],
                        sql_template=pattern['sql_template'],
                        response_time=pattern['response_time'],
                        result_count=pattern['result_count']
                    )
                    self.logger.debug(f"Success pattern saved to pattern_cache: {pattern_key}")
                except Exception as e:
                    self.logger.warning(f"Failed to save success pattern to pattern_cache: {e}")
            
            self.logger.info(f"Learned successful pattern: {pattern['query_template']} (response_time: {response_time:.2f}s)")
            return pattern
        elif not success:
            self.knowledge_base["failed_patterns"].append(pattern)
            self.logger.info(f"Learned failed pattern: {pattern['query_template']} (response_time: {response_time:.2f}s)")
            return pattern

        return None

    def get_session_stats(self, session_id: str = None) -> Optional[Dict[str, Any]]:
        """
        获取会话统计信息

        Args:
            session_id: 会话ID，如果为None则返回当前会话

        Returns:
            会话统计信息
        """
        target_session_id = session_id or self.current_session_id
        if target_session_id not in self.sessions:
            return None

        session = self.sessions[target_session_id]
        performance = session["performance"]
        
        if performance["query_count"] > 0:
            success_rate = (performance["success_count"] / performance["query_count"]) * 100
        else:
            success_rate = 0

        stats = {
            "session_id": target_session_id,
            "query_count": performance["query_count"],
            "success_count": performance["success_count"],
            "success_rate": round(success_rate, 2),
            "average_response_time": round(performance["average_response_time"], 2),
            "total_response_time": round(performance["total_response_time"], 2),
            "history_size": len(session["query_history"]),
            "start_time": session["start_time"],
            "last_accessed": session["last_accessed"]
        }

        # ✅ 新增：从数据库获取更完整的统计信息
        if self.enable_database_persistence:
            try:
                db_stats = self.database_connector.get_session_statistics(target_session_id)
                if db_stats:
                    stats.update({
                        "database_query_count": db_stats.get("total_queries", 0),
                        "database_success_rate": db_stats.get("success_rate", 0),
                        "database_avg_execution_time": db_stats.get("avg_execution_time", 0)
                    })
            except Exception as e:
                self
