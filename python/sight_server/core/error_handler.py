"""
增强的错误处理器模块 - Sight Server
提供详细的错误分类、智能重试策略和错误分析功能
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedErrorHandler:
    """
    增强的错误处理器

    功能:
    - 详细的错误分类和识别
    - 智能重试策略和退避机制
    - 错误模式学习和预防
    - 错误信息解析和利用
    - 自动修复建议生成
    """

    def __init__(self, max_retries: int = 5, enable_learning: bool = True):
        """
        初始化增强的错误处理器

        Args:
            max_retries: 最大重试次数，默认5次
            enable_learning: 是否启用错误模式学习
        """
        self.max_retries = max_retries
        self.enable_learning = enable_learning
        self.logger = logger
        
        # 错误模式知识库
        self.error_patterns = self._initialize_error_patterns()
        
        # 错误统计
        self.error_stats = {
            "total_errors": 0,
            "error_types": {},
            "successful_recoveries": 0,
            "failed_recoveries": 0
        }

    def _initialize_error_patterns(self) -> Dict[str, Any]:
        """初始化错误模式知识库"""
        return {
            "sql_syntax_errors": [
                {
                    "pattern": r"syntax error.*near.*\"(.*?)\"",
                    "description": "SQL语法错误",
                    "severity": "high",
                    "fix_strategy": "retry_sql",
                    "prevention": "检查SQL语法，特别是引号和关键字"
                },
                {
                    "pattern": r"missing FROM-clause entry",
                    "description": "缺少FROM子句",
                    "severity": "high", 
                    "fix_strategy": "retry_sql",
                    "prevention": "确保SQL包含完整的FROM子句"
                },
                {
                    "pattern": r"aggregate.*nested.*aggregate",
                    "description": "聚合函数嵌套错误",
                    "severity": "medium",
                    "fix_strategy": "retry_sql",
                    "prevention": "避免在json_agg内使用COUNT/SUM等聚合函数"
                }
            ],
            "timeout_errors": [
                {
                    "pattern": r"timeout|timed out",
                    "description": "查询超时",
                    "severity": "medium",
                    "fix_strategy": "simplify_query",
                    "prevention": "添加LIMIT限制，简化查询条件"
                }
            ],
            "connection_errors": [
                {
                    "pattern": r"connection.*refused|connect.*failed",
                    "description": "数据库连接失败",
                    "severity": "high",
                    "fix_strategy": "retry_execution",
                    "prevention": "检查数据库连接配置和网络状态"
                }
            ],
            "field_errors": [
                {
                    "pattern": r"column.*does not exist",
                    "description": "字段不存在",
                    "severity": "medium",
                    "fix_strategy": "retry_sql", 
                    "prevention": "检查字段名是否正确，使用Schema信息"
                }
            ],
            "permission_errors": [
                {
                    "pattern": r"permission denied|access denied",
                    "description": "权限不足",
                    "severity": "high",
                    "fix_strategy": "fail",
                    "prevention": "检查数据库用户权限"
                }
            ]
        }

    def analyze_error(self, error_message: str, sql: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度分析错误

        Args:
            error_message: 错误消息
            sql: 相关的SQL语句
            context: 上下文信息

        Returns:
            错误分析结果
        """
        error_lower = error_message.lower()
        
        # 1. 错误分类
        error_type = self._classify_error_detailed(error_message)
        
        # 2. 错误模式匹配
        matched_patterns = self._match_error_patterns(error_message)
        
        # 3. 错误原因分析
        root_cause = self._analyze_root_cause(error_message, sql, context)
        
        # 4. 影响评估
        impact_assessment = self._assess_impact(error_type, sql, context)
        
        # 5. 修复建议
        fix_suggestions = self._generate_fix_suggestions(error_type, matched_patterns, sql, context)
        
        analysis = {
            "error_type": error_type,
            "error_message": error_message,
            "sql": sql,
            "matched_patterns": matched_patterns,
            "root_cause": root_cause,
            "impact_assessment": impact_assessment,
            "fix_suggestions": fix_suggestions,
            "timestamp": datetime.now().isoformat(),
            "analysis_id": f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # 更新统计
        self._update_error_stats(error_type, analysis)
        
        # 学习错误模式（如果启用）
        if self.enable_learning:
            self._learn_from_error(analysis)
        
        return analysis

    def _classify_error_detailed(self, error_message: str) -> str:
        """
        详细的错误分类

        Args:
            error_message: 错误消息

        Returns:
            详细的错误类型
        """
        error_lower = error_message.lower()
        
        # SQL语法错误（细分）
        if re.search(r"syntax error.*near", error_lower):
            return "SQL_SYNTAX_ERROR_NEAR"
        elif re.search(r"missing FROM-clause entry", error_lower):
            return "SQL_SYNTAX_ERROR_MISSING_FROM"
        elif re.search(r"aggregate.*nested.*aggregate", error_lower):
            return "SQL_SYNTAX_ERROR_AGGREGATE_NESTED"
        elif re.search(r"unexpected token", error_lower):
            return "SQL_SYNTAX_ERROR_UNEXPECTED_TOKEN"
            
        # 连接错误
        elif re.search(r"connection.*refused", error_lower):
            return "CONNECTION_ERROR_REFUSED"
        elif re.search(r"connect.*failed", error_lower):
            return "CONNECTION_ERROR_FAILED"
        elif re.search(r"timeout.*connect", error_lower):
            return "CONNECTION_ERROR_TIMEOUT"
            
        # 执行错误
        elif re.search(r"timeout.*execution", error_lower):
            return "EXECUTION_ERROR_TIMEOUT"
        elif re.search(r"deadlock", error_lower):
            return "EXECUTION_ERROR_DEADLOCK"
            
        # 字段/表错误
        elif re.search(r"column.*does not exist", error_lower):
            return "FIELD_ERROR_COLUMN_NOT_EXIST"
        elif re.search(r"relation.*does not exist", error_lower):
            return "FIELD_ERROR_TABLE_NOT_EXIST"
        elif re.search(r"duplicate column", error_lower):
            return "FIELD_ERROR_DUPLICATE_COLUMN"
            
        # 权限错误
        elif re.search(r"permission denied", error_lower):
            return "PERMISSION_ERROR_DENIED"
        elif re.search(r"access denied", error_lower):
            return "PERMISSION_ERROR_ACCESS"
            
        # 数据格式错误
        elif re.search(r"invalid.*json", error_lower):
            return "DATA_FORMAT_ERROR_JSON"
        elif re.search(r"parse.*error", error_lower):
            return "DATA_FORMAT_ERROR_PARSE"
            
        else:
            return "UNKNOWN_ERROR"

    def _match_error_patterns(self, error_message: str) -> List[Dict[str, Any]]:
        """
        匹配已知错误模式

        Args:
            error_message: 错误消息

        Returns:
            匹配的模式列表
        """
        matched = []
        
        for category, patterns in self.error_patterns.items():
            for pattern_info in patterns:
                if re.search(pattern_info["pattern"], error_message, re.IGNORECASE):
                    matched.append({
                        "category": category,
                        "description": pattern_info["description"],
                        "severity": pattern_info["severity"],
                        "fix_strategy": pattern_info["fix_strategy"],
                        "prevention": pattern_info["prevention"]
                    })
        
        return matched

    def _analyze_root_cause(self, error_message: str, sql: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析错误根本原因

        Args:
            error_message: 错误消息
            sql: SQL语句
            context: 上下文

        Returns:
            根本原因分析
        """
        root_cause = {
            "primary_cause": "unknown",
            "contributing_factors": [],
            "confidence": 0.0
        }
        
        error_lower = error_message.lower()
        sql_upper = sql.upper()
        
        # 分析SQL结构
        if "missing FROM-clause" in error_lower:
            root_cause["primary_cause"] = "missing_from_clause"
            root_cause["confidence"] = 0.9
            
            # 检查SQL是否缺少FROM
            if "FROM" not in sql_upper:
                root_cause["contributing_factors"].append("SQL完全缺少FROM子句")
            else:
                # 检查别名使用
                if re.search(r'\ba\.', sql) and "a_sight" not in sql:
                    root_cause["contributing_factors"].append("使用了别名a但没有定义表a_sight")
                if re.search(r'\bt\.', sql) and "tourist_spot" not in sql:
                    root_cause["contributing_factors"].append("使用了别名t但没有定义表tourist_spot")
                    
        elif "syntax error" in error_lower:
            root_cause["primary_cause"] = "sql_syntax_error"
            root_cause["confidence"] = 0.8
            
            # 检查常见语法问题
            if "SELECT *" in sql_upper:
                root_cause["contributing_factors"].append("使用了SELECT *，建议明确指定字段")
            if "LIMIT" not in sql_upper and "COUNT" not in sql_upper:
                root_cause["contributing_factors"].append("缺少LIMIT限制，可能导致性能问题")
                
        elif "timeout" in error_lower:
            root_cause["primary_cause"] = "query_complexity"
            root_cause["confidence"] = 0.7
            
            # 检查查询复杂度
            if "JOIN" in sql_upper and sql_upper.count("JOIN") > 2:
                root_cause["contributing_factors"].append("多表JOIN可能增加查询复杂度")
            if "WHERE" in sql_upper and len(sql) > 500:
                root_cause["contributing_factors"].append("查询条件可能过于复杂")
                
        elif "column.*does not exist" in error_lower:
            root_cause["primary_cause"] = "field_not_exist"
            root_cause["confidence"] = 0.9
            
            # 提取不存在的字段名
            field_match = re.search(r"column \"(.*?)\" does not exist", error_message)
            if field_match:
                root_cause["contributing_factors"].append(f"字段 '{field_match.group(1)}' 不存在")
        
        return root_cause

    def _assess_impact(self, error_type: str, sql: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估错误影响

        Args:
            error_type: 错误类型
            sql: SQL语句
            context: 上下文

        Returns:
            影响评估
        """
        impact = {
            "severity": "low",
            "recoverable": True,
            "user_impact": "minimal",
            "system_impact": "minimal"
        }
        
        # 根据错误类型设置严重性
        if error_type.startswith("PERMISSION_ERROR"):
            impact["severity"] = "critical"
            impact["recoverable"] = False
            impact["user_impact"] = "complete_failure"
            impact["system_impact"] = "requires_configuration_change"
            
        elif error_type.startswith("CONNECTION_ERROR"):
            impact["severity"] = "high"
            impact["recoverable"] = True
            impact["user_impact"] = "service_unavailable"
            impact["system_impact"] = "requires_infrastructure_check"
            
        elif error_type.startswith("SQL_SYNTAX_ERROR"):
            impact["severity"] = "medium"
            impact["recoverable"] = True
            impact["user_impact"] = "query_failure"
            impact["system_impact"] = "requires_sql_fix"
            
        elif error_type.startswith("EXECUTION_ERROR"):
            impact["severity"] = "medium"
            impact["recoverable"] = True
            impact["user_impact"] = "delayed_response"
            impact["system_impact"] = "performance_degradation"
            
        elif error_type.startswith("FIELD_ERROR"):
            impact["severity"] = "low"
            impact["recoverable"] = True
            impact["user_impact"] = "incorrect_results"
            impact["system_impact"] = "requires_schema_check"
            
        return impact

    def _generate_fix_suggestions(self, error_type: str, matched_patterns: List[Dict], 
                                sql: str, context: Dict[str, Any]) -> List[str]:
        """
        生成修复建议

        Args:
            error_type: 错误类型
            matched_patterns: 匹配的模式
            sql: SQL语句
            context: 上下文

        Returns:
            修复建议列表
        """
        suggestions = []
        
        # 基于错误类型的建议
        if error_type.startswith("SQL_SYNTAX_ERROR"):
            suggestions.append("检查SQL语法，确保所有关键字和标点符号正确")
            suggestions.append("验证FROM子句是否完整定义了所有使用的表别名")
            
            if "missing FROM-clause" in str(matched_patterns):
                suggestions.append("添加缺失的FROM子句，确保所有使用的表都有定义")
                
        elif error_type.startswith("CONNECTION_ERROR"):
            suggestions.append("检查数据库连接配置和网络连接")
            suggestions.append("验证数据库服务是否正常运行")
            
        elif error_type.startswith("EXECUTION_ERROR_TIMEOUT"):
            suggestions.append("简化查询条件，减少数据量")
            suggestions.append("添加LIMIT限制返回结果数量")
            suggestions.append("考虑添加适当的索引优化查询性能")
            
        elif error_type.startswith("FIELD_ERROR"):
            suggestions.append("检查字段名拼写是否正确")
            suggestions.append("验证表结构是否包含该字段")
            suggestions.append("使用数据库Schema信息确认可用字段")
            
        # 基于匹配模式的建议
        for pattern in matched_patterns:
            suggestions.append(pattern["prevention"])
            
        # 通用建议
        suggestions.append("检查生成的SQL是否符合PostgreSQL语法规范")
        suggestions.append("验证表名和字段名是否使用正确的引号")
        
        return list(set(suggestions))  # 去重

    def determine_retry_strategy(self, error_analysis: Dict[str, Any], 
                               retry_count: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        确定重试策略

        Args:
            error_analysis: 错误分析结果
            retry_count: 当前重试次数
            context: 上下文

        Returns:
            重试策略配置
        """
        error_type = error_analysis["error_type"]
        impact = error_analysis["impact_assessment"]
        
        strategy = {
            "should_retry": True,
            "strategy_type": "retry_sql",
            "backoff_seconds": 0,
            "max_retries": self.max_retries,
            "reason": ""
        }
        
        # 检查是否可恢复
        if not impact["recoverable"]:
            strategy["should_retry"] = False
            strategy["reason"] = "错误不可恢复"
            return strategy
            
        # 检查重试次数
        if retry_count >= self.max_retries:
            strategy["should_retry"] = False
            strategy["reason"] = f"已达到最大重试次数 ({self.max_retries})"
            return strategy
            
        # 根据错误类型确定策略
        if error_type.startswith("SQL_SYNTAX_ERROR"):
            strategy["strategy_type"] = "retry_sql"
            strategy["backoff_seconds"] = 0  # 立即重试
            strategy["reason"] = "SQL语法错误，重新生成SQL"
            
        elif error_type.startswith("EXECUTION_ERROR_TIMEOUT"):
            strategy["strategy_type"] = "simplify_query"
            strategy["backoff_seconds"] = 1  # 短暂等待
            strategy["reason"] = "查询超时，简化查询条件"
            
        elif error_type.startswith("CONNECTION_ERROR"):
            strategy["strategy_type"] = "retry_execution"
            # 指数退避：1, 2, 4, 8秒
            strategy["backoff_seconds"] = min(2 ** retry_count, 8)
            strategy["reason"] = "连接错误，稍后重试执行"
            
        elif error_type.startswith("FIELD_ERROR"):
            strategy["strategy_type"] = "retry_sql"
            strategy["backoff_seconds"] = 0
            strategy["reason"] = "字段错误，重新生成SQL"
            
        else:
            # 未知错误，保守策略
            if retry_count < 2:
                strategy["strategy_type"] = "retry_sql"
                strategy["backoff_seconds"] = 1
                strategy["reason"] = "未知错误，尝试重新生成SQL"
            else:
                strategy["should_retry"] = False
                strategy["reason"] = "未知错误，重试失败"
                
        return strategy

    def _update_error_stats(self, error_type: str, analysis: Dict[str, Any]):
        """更新错误统计"""
        self.error_stats["total_errors"] += 1
        
        if error_type in self.error_stats["error_types"]:
            self.error_stats["error_types"][error_type] += 1
        else:
            self.error_stats["error_types"][error_type] = 1

    def _learn_from_error(self, analysis: Dict[str, Any]):
        """
        从错误中学习模式

        Args:
            analysis: 错误分析结果
        """
        # 这里可以实现错误模式学习逻辑
        # 例如：记录常见错误、优化错误检测规则等
        pass

    def get_error_stats(self) -> Dict[str, Any]:
        """
        获取错误统计信息

        Returns:
            错误统计
        """
        stats = self.error_stats.copy()
        
        # 计算错误率
        if stats["total_errors"] > 0:
            stats["recovery_rate"] = round(
                (stats["successful_recoveries"] / stats["total_errors"]) * 100, 2
            ) if stats["successful_recoveries"] > 0 else 0
        else:
            stats["recovery_rate"] = 0
            
        return stats

    def reset_stats(self):
        """重置错误统计"""
        self.error_stats = {
            "total_errors": 0,
            "error_types": {},
            "successful_recoveries": 0,
            "failed_recoveries": 0
        }


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== 增强错误处理器测试 ===\n")
    
    # 创建错误处理器
    error_handler = EnhancedErrorHandler(max_retries=5, enable_learning=True)
    
    # 测试1: SQL语法错误分析
    print("--- 测试1: SQL语法错误分析 ---")
    sql_syntax_error = "syntax error at or near \"SELECT\""
    test_sql = "SELECT json_agg(json_build_object('name', a.name)) WHERE a.level = '5A'"
    
    analysis1 = error_handler.analyze_error(sql_syntax_error, test_sql, {})
    print(f"错误类型: {analysis1['error_type']}")
    print(f"根本原因: {analysis1['root_cause']['primary_cause']}")
    print(f"修复建议: {analysis1['fix_suggestions'][:2]}")
    
    # 测试2: 连接错误分析
    print("\n--- 测试2: 连接错误分析 ---")
    connection_error = "connection refused to database server"
    analysis2 = error_handler.analyze_error(connection_error, test_sql, {})
    print(f"错误类型: {analysis2['error_type']}")
    print(f"影响评估: {analysis2['impact_assessment']}")
    
    # 测试3: 重试策略
    print("\n--- 测试3: 重试策略 ---")
    strategy = error_handler.determine_retry_strategy(analysis1, 1, {})
    print(f"是否重试: {strategy['should_retry']}")
    print(f"策略类型: {strategy['strategy_type']}")
    print(f"退避时间: {strategy['backoff_seconds']}秒")
    
    # 测试4: 错误统计
    print("\n--- 测试4: 错误统计 ---")
    stats = error_handler.get_error_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
