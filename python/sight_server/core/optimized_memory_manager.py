"""
优化的内存管理器模块 - Sight Server
提供增强的内存管理功能，包括会话自动清理和性能优化

✅ 重构说明：OptimizedMemoryManager 继承自 MemoryManager 基类
- 复用基类的工具方法（_extract_query_template, _is_similar 等）
- 扩展会话管理、自动清理和性能监控功能
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
        enable_step_compression: bool = True  # ✅ 新增：启用步骤压缩
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
            f"step_saving={enable_step_saving} (level: {step_saving_level})"
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

        self.logger.info(f"Started new session: {conversation_id}")

        return {
            "session_history": [],
            "conversation_id": conversation_id,
            "knowledge_base": self.knowledge_base.copy(),
            "learned_patterns": []
        }

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

        self.logger.debug(f"Added query to session: {query[:50]}... (response_time: {response_time:.2f}s)")

        return history_entry

    def _cleanup_old_sessions(self) -> int:
        """
        清理过期会话

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
            session_data = self.sessions[session_id]
            memory_estimate = self._estimate_session_memory(session_data)
            
            del self.sessions[session_id]
            cleaned_count += 1
            
            self.cleanup_stats["memory_saved_mb"] += memory_estimate
            self.logger.debug(f"Cleaned expired session: {session_id} (estimated {memory_estimate:.2f}MB)")

        if expired_sessions:
            self.cleanup_stats["last_cleanup_time"] = current_time.isoformat()
            self.cleanup_stats["total_cleanups"] += 1
            self.cleanup_stats["sessions_cleaned"] += cleaned_count
            
            self.logger.info(f"Cleaned {cleaned_count} expired sessions")

        return cleaned_count

    def _cleanup_oldest_sessions(self, keep_count: int) -> int:
        """
        清理最旧的会话

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
            memory_estimate = self._estimate_session_memory(session_data)
            
            del self.sessions[session_id]
            removed_count += 1
            
            self.cleanup_stats["memory_saved_mb"] += memory_estimate
            self.logger.debug(f"Cleaned old session: {session_id} (estimated {memory_estimate:.2f}MB)")

        self.cleanup_stats["last_cleanup_time"] = datetime.now().isoformat()
        self.cleanup_stats["total_cleanups"] += 1
        self.cleanup_stats["sessions_cleaned"] += removed_count
        
        self.logger.info(f"Cleaned {removed_count} oldest sessions (keeping {keep_count})")

        return removed_count

    def _estimate_session_memory(self, session_data: Dict[str, Any]) -> float:
        """
        估算会话占用的内存大小（MB）

        Args:
            session_data: 会话数据

        Returns:
            估算的内存大小（MB）
        """
        try:
            # 将会话数据序列化为JSON字符串来估算大小（使用 DecimalEncoder 处理 Decimal 类型）
            json_str = json.dumps(session_data, ensure_ascii=False, cls=DecimalEncoder)
            size_bytes = len(json_str.encode('utf-8'))
            size_mb = size_bytes / (1024 * 1024)
            return size_mb
        except Exception as e:
            self.logger.warning(f"Failed to estimate session memory: {e}")
            return 0.1  # 默认估算值

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

        return {
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

    def get_memory_usage_stats(self) -> Dict[str, Any]:
        """
        获取内存使用统计

        Returns:
            内存使用统计
        """
        total_sessions = len(self.sessions)
        total_queries = sum(len(session["query_history"]) for session in self.sessions.values())
        
        # 估算总内存使用
        total_memory_mb = sum(
            self._estimate_session_memory(session) for session in self.sessions.values()
        )

        return {
            "total_sessions": total_sessions,
            "total_queries": total_queries,
            "estimated_memory_mb": round(total_memory_mb, 2),
            "max_sessions": self.max_sessions,
            "session_ttl_seconds": self.session_ttl,
            "cleanup_stats": self.cleanup_stats.copy()
        }

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
            self.logger.info(f"Learned successful pattern: {pattern['query_template']} (response_time: {response_time:.2f}s)")
            return pattern
        elif not success:
            self.knowledge_base["failed_patterns"].append(pattern)
            self.logger.info(f"Learned failed pattern: {pattern['query_template']} (response_time: {response_time:.2f}s)")
            return pattern

        return None

    def find_similar_queries(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        查找相似的历史查询，考虑性能因素

        Args:
            query: 当前查询
            top_k: 返回前k个相似查询

        Returns:
            相似查询列表，按响应时间排序
        """
        similar = []

        # 从成功模式中查找
        for pattern in self.knowledge_base.get("success_patterns", []):
            if self._is_similar(query, pattern["query_template"]):
                similar.append({
                    "pattern": pattern,
                    "type": "success",
                    "response_time": pattern.get("response_time", 0)
                })

        # 按响应时间排序（最快的优先）
        similar.sort(key=lambda x: x["response_time"])

        # 限制返回数量
        return similar[:top_k]


    # ✅ 复用基类的工具方法，无需重新实现
    # - _extract_query_template() 从基类继承
    # - _extract_sql_template() 从基类继承
    # - _is_similar() 从基类继承
    # 这些方法在基类 MemoryManager 中已经实现，直接复用

    # 注释掉重复的实现，使用基类方法
    # def _extract_query_template(self, query: str) -> str:
    #     """提取查询模板"""
    #     ...（基类已实现）

    # def _extract_sql_template(self, sql: str) -> str:
    #     """提取SQL模板"""
    #     ...（基类已实现）

    # def _is_similar(self, query1: str, query2: str) -> bool:
    #     """判断两个查询是否相似"""
    #     ...（基类已实现）

    def export_memory(self) -> Dict[str, Any]:
        """导出记忆数据"""
        return {
            "sessions": self.sessions,
            "knowledge_base": self.knowledge_base,
            "cleanup_stats": self.cleanup_stats,
            "current_session_id": self.current_session_id,
            "export_time": datetime.now().isoformat()
        }

    def import_memory(self, memory_data: Dict[str, Any]) -> bool:
        """导入记忆数据"""
        try:
            if "sessions" in memory_data:
                self.sessions = memory_data["sessions"]
            if "knowledge_base" in memory_data:
                self.knowledge_base = memory_data["knowledge_base"]
            if "cleanup_stats" in memory_data:
                self.cleanup_stats = memory_data["cleanup_stats"]
            if "current_session_id" in memory_data:
                self.current_session_id = memory_data["current_session_id"]
            
            self.logger.info("Imported memory data successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to import memory: {e}")
            return False

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

        self.logger.debug(f"Saved step: {step_type} (importance: {importance})")
        return step_record

    def _should_save_step(self, step_type: str, importance: int) -> bool:
        """
        判断是否应该保存该步骤

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

    def _compress_step_data(self, step_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        压缩步骤数据，移除冗余信息

        Args:
            step_record: 原始步骤记录

        Returns:
            压缩后的步骤记录
        """
        compressed = {
            "step_type": step_record.get("step_type"),
            "timestamp": step_record.get("timestamp"),
            "importance": step_record.get("importance"),
            "session_id": step_record.get("session_id")
        }

        # 提取关键数据
        step_data = step_record.get("step_data", {})
        key_data = self._extract_key_step_data(step_data, step_record["step_type"])
        compressed["key_data"] = key_data

        return compressed

    def _extract_key_step_data(self, step_data: Dict[str, Any], step_type: str) -> Dict[str, Any]:
        """
        提取步骤关键数据

        Args:
            step_data: 完整步骤数据
            step_type: 步骤类型

        Returns:
            关键数据
        """
        if step_type == "sql_generation":
            return {
                "query": step_data.get("query", "")[:100],  # 限制长度
                "generated_sql": step_data.get("generated_sql", "")[:200],
                "intent_type": step_data.get("intent_info", {}).get("intent_type"),
                "step_number": step_data.get("step_number")
            }
        elif step_type == "error_recovery":
            return {
                "error_type": step_data.get("error_type"),
                "error_message": step_data.get("error_message", "")[:200],
                "recovery_strategy": step_data.get("recovery_strategy"),
                "step_number": step_data.get("step_number")
            }
        elif step_type == "strategy_decision":
            return {
                "decision_reason": step_data.get("decision_reason", "")[:200],
                "selected_strategy": step_data.get("selected_strategy"),
                "step_number": step_data.get("step_number")
            }
        else:
            # 通用提取，只保留关键字段
            return {
                "summary": str(step_data)[:300]  # 限制总长度
            }

    def _cleanup_old_steps(self, session: Dict[str, Any], keep_count: int) -> int:
        """
        清理旧步骤

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

        self.logger.debug(f"Cleaned {removed_count} old steps (keeping {keep_count})")
        return removed_count

    def get_step_history(self, session_id: str = None, step_type: str = None) -> List[Dict[str, Any]]:
        """
        获取步骤历史

        Args:
            session_id: 会话ID，如果为None则使用当前会话
            step_type: 步骤类型过滤，如果为None则返回所有步骤

        Returns:
            步骤历史列表
        """
        target_session_id = session_id or self.current_session_id
        if target_session_id not in self.sessions:
            return []

        session = self.sessions[target_session_id]
        steps = session.get("step_history", [])

        if step_type:
            steps = [step for step in steps if step.get("step_type") == step_type]

        return steps

    def get_debug_trace(self, session_id: str = None) -> Dict[str, Any]:
        """
        获取完整的调试轨迹

        Args:
            session_id: 会话ID，如果为None则使用当前会话

        Returns:
            调试轨迹信息
        """
        target_session_id = session_id or self.current_session_id
        if target_session_id not in self.sessions:
            return {}

        session = self.sessions[target_session_id]
        steps = session.get("step_history", [])

        # 分析步骤性能
        performance_summary = self._analyze_step_performance(steps)

        return {
            "session_id": target_session_id,
            "total_steps": len(steps),
            "step_types": list(set(step.get("step_type") for step in steps)),
            "compressed_steps": self._compress_step_history(steps),
            "performance_summary": performance_summary,
            "session_start_time": session.get("start_time"),
            "session_last_accessed": session.get("last_accessed")
        }

    def _analyze_step_performance(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析步骤性能

        Args:
            steps: 步骤列表

        Returns:
            性能摘要
        """
        if not steps:
            return {}

        step_types = {}
        total_importance = 0

        for step in steps:
            step_type = step.get("step_type")
            importance = step.get("importance", 1)
            
            if step_type not in step_types:
                step_types[step_type] = {
                    "count": 0,
                    "total_importance": 0,
                    "average_importance": 0
                }
            
            step_types[step_type]["count"] += 1
            step_types[step_type]["total_importance"] += importance
            total_importance += importance

        # 计算平均重要性
        for step_type in step_types:
            step_types[step_type]["average_importance"] = (
                step_types[step_type]["total_importance"] / step_types[step_type]["count"]
            )

        return {
            "step_types": step_types,
            "total_steps": len(steps),
            "average_importance": total_importance / len(steps) if steps else 0,
            "most_common_step": max(step_types.items(), key=lambda x: x[1]["count"])[0] if step_types else None
        }

    def _compress_step_history(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        压缩步骤历史

        Args:
            steps: 原始步骤列表

        Returns:
            压缩后的步骤列表
        """
        compressed = []
        for step in steps:
            compressed_step = {
                "type": step.get("step_type"),
                "timestamp": step.get("timestamp"),
                "importance": step.get("importance"),
                "key_data": step.get("key_data", {})
            }
            compressed.append(compressed_step)
        return compressed

    def extract_learning_patterns(self) -> List[Dict[str, Any]]:
        """
        从中间步骤中提取学习模式

        Returns:
            学习模式列表
        """
        patterns = []
        
        for session_id, session in self.sessions.items():
            steps = session.get("step_history", [])
            sql_steps = [step for step in steps if step.get("step_type") == "sql_generation"]
            
            for step in sql_steps:
                step_data = step.get("step_data", {})
                if isinstance(step_data, dict):
                    pattern = {
                        "query_template": self._extract_query_template(step_data.get("query", "")),
                        "sql_template": self._extract_sql_template(step_data.get("generated_sql", "")),
                        "success_rate": self._calculate_step_success_rate(step, session),
                        "average_response_time": step_data.get("response_time"),
                        "learned_from": "step_history",
                        "session_id": session_id,
                        "learned_at": datetime.now().isoformat()
                    }
                    patterns.append(pattern)
        
        return patterns

    def _calculate_step_success_rate(self, step: Dict[str, Any], session: Dict[str, Any]) -> float:
        """
        计算步骤成功率

        Args:
            step: 步骤记录
            session: 会话数据

        Returns:
            成功率 (0-1)
        """
        # 这里可以根据实际业务逻辑计算成功率
        # 目前返回默认值
        return 0.8

    def get_step_memory_usage(self) -> Dict[str, Any]:
        """
        获取步骤内存使用统计

        Returns:
            步骤内存使用统计
        """
        total_steps = 0
        total_step_memory = 0
        
        for session in self.sessions.values():
            steps = session.get("step_history", [])
            total_steps += len(steps)
            for step in steps:
                total_step_memory += self._estimate_step_memory(step)
        
        return {
            "total_steps": total_steps,
            "total_step_memory_mb": round(total_step_memory, 2),
            "average_step_memory_kb": round((total_step_memory * 1024) / max(total_steps, 1), 2),
            "step_saving_enabled": self.enable_step_saving,
            "step_saving_level": self.step_saving_level
        }

    def _estimate_step_memory(self, step: Dict[str, Any]) -> float:
        """
        估算步骤占用的内存大小（MB）

        Args:
            step: 步骤数据

        Returns:
            估算的内存大小（MB）
        """
        try:
            json_str = json.dumps(step, ensure_ascii=False, cls=DecimalEncoder)
            size_bytes = len(json_str.encode('utf-8'))
            size_mb = size_bytes / (1024 * 1024)
            return size_mb
        except Exception as e:
            self.logger.warning(f"Failed to estimate step memory: {e}")
            return 0.01  # 默认估算值

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


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== OptimizedMemoryManager 测试 ===\n")

    # 创建管理器（使用较小的配置便于测试）
    manager = OptimizedMemoryManager(
        max_sessions=5,
        session_ttl=60,  # 1分钟，便于测试过期
        enable_auto_cleanup=True
    )

    # 测试1: 创建多个会话
    print("--- 测试1: 创建多个会话 ---")
    for i in range(3):
        session_id = f"test-session-{i:03d}"
        manager.start_session(session_id)
        print(f"Created session: {session_id}")

    # 测试2: 添加查询和性能数据
    print("\n--- 测试2: 添加查询和性能数据 ---")
    manager.current_session_id = "test-session-001"
    entry = manager.add_query_to_session(
        query="查询浙江省的5A景区",
        result={"count": 10, "data": []},
        sql="SELECT * FROM a_sight WHERE province='浙江省'",
        success=True,
        response_time=1.5
    )
    print(f"Added query with response_time: {entry['response_time']}s")

    # 测试3: 学习模式
    print("\n--- 测试3: 学习模式 ---")
    pattern = manager.learn_from_query(
        query="查询浙江省的5A景区",
        sql="SELECT * FROM a_sight WHERE province='浙江省'",
        result={"count": 10},
        success=True,
        response_time=1.5
    )
    if pattern:
        print(f"Learned pattern with response_time: {pattern['response_time']}s")
    else:
        print("No pattern learned")

    # 测试4: 获取会话统计
    print("\n--- 测试4: 获取会话统计 ---")
    stats = manager.get_session_stats("test-session-001")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 测试5: 获取内存使用统计
    print("\n--- 测试5: 获取内存使用统计 ---")
    memory_stats = manager.get_memory_usage_stats()
    for key, value in memory_stats.items():
        if key == "cleanup_stats":
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")

    # 测试6: 清理所有会话
    print("\n--- 测试6: 清理所有会话 ---")
    cleared_count = manager.clear_all_sessions()
    print(f"Cleared {cleared_count} sessions")
