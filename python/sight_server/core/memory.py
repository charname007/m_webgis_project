"""
Memory管理模块 - Sight Server
提供会话记忆和知识库管理功能
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    记忆管理器

    功能:
    - 短期记忆：管理当前会话的查询历史
    - 长期记忆：跨会话的知识积累
    - 查询模式学习
    - 相似查询检索
    """

    def __init__(self):
        """初始化记忆管理器"""
        self.logger = logger
        # 短期记忆：当前会话
        self.current_session = {}
        # 长期记忆：知识库
        self.knowledge_base = {
            "common_queries": {},  # 常见查询及其SQL模板
            "optimization_rules": [],  # 查询优化规则
            "failed_patterns": [],  # 失败的查询模式
            "success_patterns": []  # 成功的查询模式
        }

    def start_session(self, conversation_id: str) -> Dict[str, Any]:
        """
        开始新会话

        Args:
            conversation_id: 会话ID

        Returns:
            初始化的会话状态
        """
        self.current_session = {
            "conversation_id": conversation_id,
            "start_time": datetime.now().isoformat(),
            "query_history": [],
            "context": {}
        }

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
        success: bool
    ) -> Dict[str, Any]:
        """
        添加查询到会话历史

        Args:
            query: 查询文本
            result: 查询结果
            sql: 执行的SQL
            success: 是否成功

        Returns:
            更新后的会话历史记录
        """
        history_entry = {
            "query": query,
            "sql": sql,
            "success": success,
            "result_count": result.get("count", 0) if result else 0,
            "timestamp": datetime.now().isoformat()
        }

        if "query_history" not in self.current_session:
            self.current_session["query_history"] = []

        self.current_session["query_history"].append(history_entry)

        self.logger.debug(f"Added query to session: {query[:50]}...")

        return history_entry

    def learn_from_query(
        self,
        query: str,
        sql: str,
        result: Dict[str, Any],
        success: bool
    ) -> Optional[Dict[str, Any]]:
        """
        从查询中学习模式

        Args:
            query: 查询文本
            sql: 执行的SQL
            result: 查询结果
            success: 是否成功

        Returns:
            学习到的模式（如果有）
        """
        pattern = {
            "query_template": self._extract_query_template(query),
            "sql_template": self._extract_sql_template(sql),
            "success": success,
            "result_count": result.get("count", 0) if result else 0,
            "learned_at": datetime.now().isoformat()
        }

        # 如果成功且结果数量 > 0，添加到成功模式
        if success and result.get("count", 0) > 0:
            self.knowledge_base["success_patterns"].append(pattern)
            self.logger.info(f"Learned successful pattern: {pattern['query_template']}")
            return pattern
        elif not success:
            self.knowledge_base["failed_patterns"].append(pattern)
            self.logger.info(f"Learned failed pattern: {pattern['query_template']}")
            return pattern

        return None

    def find_similar_queries(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        查找相似的历史查询

        Args:
            query: 当前查询
            top_k: 返回前k个相似查询

        Returns:
            相似查询列表
        """
        similar = []

        # 从成功模式中查找
        for pattern in self.knowledge_base.get("success_patterns", []):
            if self._is_similar(query, pattern["query_template"]):
                similar.append({
                    "pattern": pattern,
                    "type": "success"
                })

        # 限制返回数量
        return similar[:top_k]

    def get_optimization_suggestions(self, query: str, sql: str) -> List[str]:
        """
        获取查询优化建议

        Args:
            query: 查询文本
            sql: SQL语句

        Returns:
            优化建议列表
        """
        suggestions = []

        # 检查是否缺少索引字段
        if "WHERE" in sql.upper() and "INDEX" not in sql.upper():
            suggestions.append("建议：考虑在WHERE子句使用的字段上添加索引")

        # 检查是否使用了SELECT *
        if "SELECT *" in sql.upper():
            suggestions.append("建议：避免使用SELECT *，明确指定需要的字段")

        # 检查是否缺少LIMIT
        if "LIMIT" not in sql.upper() and "COUNT" not in sql.upper():
            suggestions.append("建议：添加LIMIT限制返回结果数量，提高查询性能")

        return suggestions

    def _extract_query_template(self, query: str) -> str:
        """
        提取查询模板（去除具体数值和名称）

        Args:
            query: 查询文本

        Returns:
            查询模板
        """
        # 简单实现：提取查询类型关键词
        keywords = []

        # 查询类型
        if "查询" in query or "查找" in query:
            keywords.append("查询")
        if "统计" in query or "多少" in query:
            keywords.append("统计")
        if "距离" in query or "附近" in query:
            keywords.append("空间")

        # 实体类型
        if "景区" in query or "景点" in query:
            keywords.append("景区")
        if "省" in query or "市" in query:
            keywords.append("地区")
        if "5A" in query or "4A" in query:
            keywords.append("评级")

        return " + ".join(keywords) if keywords else "通用查询"

    def _extract_sql_template(self, sql: str) -> str:
        """
        提取SQL模板

        Args:
            sql: SQL语句

        Returns:
            SQL模板
        """
        # 提取SQL主要结构
        template_parts = []

        sql_upper = sql.upper()

        if "SELECT" in sql_upper:
            template_parts.append("SELECT")
        if "JOIN" in sql_upper:
            template_parts.append("JOIN")
        if "WHERE" in sql_upper:
            template_parts.append("WHERE")
        if "GROUP BY" in sql_upper:
            template_parts.append("GROUP_BY")
        if "ORDER BY" in sql_upper:
            template_parts.append("ORDER_BY")

        return " ".join(template_parts)

    def _is_similar(self, query1: str, query2: str) -> bool:
        """
        判断两个查询是否相似

        Args:
            query1: 查询1
            query2: 查询2

        Returns:
            是否相似
        """
        # 简单实现：检查关键词重叠
        keywords1 = set(self._extract_query_template(query1).split(" + "))
        keywords2 = set(query2.split(" + "))

        # 至少50%关键词重叠
        overlap = len(keywords1 & keywords2)
        total = max(len(keywords1), len(keywords2))

        return overlap / total >= 0.5 if total > 0 else False

    def export_memory(self) -> Dict[str, Any]:
        """
        导出记忆数据

        Returns:
            记忆数据字典
        """
        return {
            "current_session": self.current_session,
            "knowledge_base": self.knowledge_base,
            "export_time": datetime.now().isoformat()
        }

    def import_memory(self, memory_data: Dict[str, Any]) -> bool:
        """
        导入记忆数据

        Args:
            memory_data: 记忆数据

        Returns:
            是否成功
        """
        try:
            if "knowledge_base" in memory_data:
                self.knowledge_base = memory_data["knowledge_base"]
                self.logger.info("Imported knowledge base")
            return True
        except Exception as e:
            self.logger.error(f"Failed to import memory: {e}")
            return False


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== MemoryManager 测试 ===\n")

    manager = MemoryManager()

    # 测试1: 开始会话
    print("--- 测试1: 开始会话 ---")
    session = manager.start_session("test-session-001")
    print(f"Session ID: {session['conversation_id']}\n")

    # 测试2: 添加查询到会话
    print("--- 测试2: 添加查询到会话 ---")
    entry = manager.add_query_to_session(
        query="查询浙江省的5A景区",
        result={"count": 10, "data": []},
        sql="SELECT * FROM a_sight WHERE province='浙江省'",
        success=True
    )
    print(f"Added: {entry['query']}\n")

    # 测试3: 学习查询模式
    print("--- 测试3: 学习查询模式 ---")
    pattern = manager.learn_from_query(
        query="查询浙江省的5A景区",
        sql="SELECT * FROM a_sight WHERE province='浙江省'",
        result={"count": 10},
        success=True
    )
    print(f"Learned pattern: {pattern['query_template']}\n")

    # 测试4: 查找相似查询
    print("--- 测试4: 查找相似查询 ---")
    similar = manager.find_similar_queries("查询杭州市的景区")
    print(f"Found {len(similar)} similar queries\n")

    # 测试5: 优化建议
    print("--- 测试5: 优化建议 ---")
    suggestions = manager.get_optimization_suggestions(
        query="查询景区",
        sql="SELECT * FROM a_sight WHERE province='浙江省'"
    )
    for s in suggestions:
        print(f"  - {s}")
