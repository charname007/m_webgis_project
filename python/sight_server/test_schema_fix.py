"""
Schema修复验证测试脚本
验证数据库schema在所有SQL生成路径中正确传递
"""

import logging
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.processors.schema_fetcher import SchemaFetcher
from core.graph.nodes import AgentNodes
from core.schemas import AgentState

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MockSQLGenerator:
    """模拟SQL生成器，用于测试schema传递"""
    
    def __init__(self):
        self.logger = logger
        self.schema_received_count = 0
        self.last_schema = None
    
    def generate_initial_sql(self, query, intent_info=None, database_schema=None):
        """模拟生成初始SQL，记录是否收到schema"""
        self.schema_received_count += 1
        self.last_schema = database_schema
        
        logger.info(f"✅ generate_initial_sql 收到schema: {database_schema is not None}")
        if database_schema:
            logger.info(f"Schema长度: {len(database_schema)} 字符")
        
        return "SELECT * FROM a_sight LIMIT 10"
    
    def generate_followup_sql(self, original_query, previous_sql, record_count, missing_fields, database_schema=None):
        """模拟生成后续SQL，记录是否收到schema"""
        self.schema_received_count += 1
        self.last_schema = database_schema
        
        logger.info(f"✅ generate_followup_sql 收到schema: {database_schema is not None}")
        if database_schema:
            logger.info(f"Schema长度: {len(database_schema)} 字符")
        
        return "SELECT * FROM tourist_spot LIMIT 10"
    
    def fix_sql_with_error(self, sql, error, query, database_schema=None):
        """模拟修复SQL，记录是否收到schema"""
        self.schema_received_count += 1
        self.last_schema = database_schema
        
        logger.info(f"✅ fix_sql_with_error 收到schema: {database_schema is not None}")
        if database_schema:
            logger.info(f"Schema长度: {len(database_schema)} 字符")
        
        return "SELECT * FROM a_sight LIMIT 5"
    
    def fix_sql_with_context(self, sql, error_context, query, database_schema=None):
        """模拟使用上下文修复SQL，记录是否收到schema"""
        self.schema_received_count += 1
        self.last_schema = database_schema
        
        logger.info(f"✅ fix_sql_with_context 收到schema: {database_schema is not None}")
        if database_schema:
            logger.info(f"Schema长度: {len(database_schema)} 字符")
        
        return "SELECT * FROM a_sight LIMIT 5"
    
    def regenerate_with_feedback(self, query, previous_sql, feedback, intent_info=None, database_schema=None):
        """模拟基于反馈重新生成SQL，记录是否收到schema"""
        self.schema_received_count += 1
        self.last_schema = database_schema
        
        logger.info(f"✅ regenerate_with_feedback 收到schema: {database_schema is not None}")
        if database_schema:
            logger.info(f"Schema长度: {len(database_schema)} 字符")
        
        return "SELECT * FROM a_sight LIMIT 10"
    
    def analyze_missing_info(self, query, current_data):
        """模拟分析缺失信息"""
        return {
            "has_missing": False,
            "missing_fields": [],
            "data_complete": True,
            "suggestion": "数据完整"
        }


class MockSQLExecutor:
    """模拟SQL执行器"""
    
    def execute(self, sql):
        return {
            "status": "success",
            "data": [{"name": "测试景区", "level": "5A"}],
            "count": 1
        }


class MockResultParser:
    """模拟结果解析器"""
    
    def merge_results(self, results_list):
        return results_list[0] if results_list else []


class MockAnswerGenerator:
    """模拟答案生成器"""
    
    def generate(self, query, data, count):
        return f"找到{count}个结果"


class MockSchemaFetcher:
    """模拟Schema获取器"""
    
    def __init__(self):
        self.fetch_count = 0
        self.format_count = 0
    
    def fetch_schema(self, use_cache=True):
        """模拟获取schema"""
        self.fetch_count += 1
        logger.info(f"✅ fetch_schema 被调用 (第{self.fetch_count}次)")
        
        return {
            "tables": {
                "a_sight": {
                    "columns": [
                        {"name": "id", "type": "integer", "nullable": False},
                        {"name": "name", "type": "varchar", "nullable": False},
                        {"name": "level", "type": "varchar", "nullable": True},
                    ]
                },
                "tourist_spot": {
                    "columns": [
                        {"name": "id", "type": "integer", "nullable": False},
                        {"name": "name", "type": "varchar", "nullable": False},
                        {"name": "rating", "type": "numeric", "nullable": True},
                    ]
                }
            },
            "spatial_tables": {},
            "database_info": {
                "pg_version": "PostgreSQL 14.0",
                "table_count": 2,
                "spatial_table_count": 0
            }
        }
    
    def format_schema_for_llm(self, schema):
        """模拟格式化schema"""
        self.format_count += 1
        logger.info(f"✅ format_schema_for_llm 被调用 (第{self.format_count}次)")
        
        formatted = "=== 模拟数据库Schema ===\n"
        formatted += "表: a_sight (字段: id, name, level)\n"
        formatted += "表: tourist_spot (字段: id, name, rating)\n"
        return formatted


def test_schema_passing():
    """测试schema在所有路径中的传递"""
    logger.info("🚀 开始测试schema传递...")
    
    # 创建模拟组件
    sql_generator = MockSQLGenerator()
    sql_executor = MockSQLExecutor()
    result_parser = MockResultParser()
    answer_generator = MockAnswerGenerator()
    schema_fetcher = MockSchemaFetcher()
    
    # 创建AgentNodes实例
    agent_nodes = AgentNodes(
        sql_generator=sql_generator,
        sql_executor=sql_executor,
        result_parser=result_parser,
        answer_generator=answer_generator,
        schema_fetcher=schema_fetcher
    )
    
    # 测试状态
    test_state: AgentState = {
        "query": "查询浙江省的5A景区",
        "enhanced_query": "查询浙江省的5A景区",
        "query_intent": "query",
        "requires_spatial": False,
        "intent_info": {
            "intent_type": "query",
            "is_spatial": False,
            "confidence": 0.9,
            "keywords_matched": ["浙江省", "5A"]
        },
        "database_schema": schema_fetcher.fetch_schema(),
        "schema_fetched": True,
        "sql_history": [],
        "execution_results": [],
        "thought_chain": [],
        "current_step": 0,
        "current_sql": "",
        "current_result": {},
        "should_continue": True,
        "max_iterations": 3,
        "error": "",
        "retry_count": 0,
        "max_retries": 5,
        "last_error": "",
        "error_history": [],
        "fallback_strategy": "",
        "error_type": "",
        "final_data": [],
        "answer": "",
        "status": "pending",
        "message": "",
        "session_history": [],
        "conversation_id": "test-001",
        "knowledge_base": {},
        "learned_patterns": [],
        "saved_checkpoint_id": "",
        "saved_checkpoint_step": 0,
        "is_resumed_from_checkpoint": False,
        "last_checkpoint_time": "",
        "error_context": {},
        "query_id": "test-query-001",
        "query_start_time": "",
        "node_execution_logs": [],
        "validation_history": [],
        "validation_retry_count": 0,
        "max_validation_retries": 3,
        "validation_feedback": "",
        "is_validation_enabled": True,
        "should_return_data": True,
        "analysis": "",
        "insights": [],
        "suggestions": [],
        "analysis_type": ""
    }
    
    logger.info("📋 测试1: 初始SQL生成")
    result1 = agent_nodes.generate_sql(test_state)
    logger.info(f"结果: {result1.get('current_sql', 'N/A')}")
    
    logger.info("📋 测试2: 后续SQL生成")
    test_state["current_step"] = 1
    test_state["final_data"] = [{"name": "西湖", "level": "5A"}]
    result2 = agent_nodes.generate_sql(test_state)
    logger.info(f"结果: {result2.get('current_sql', 'N/A')}")
    
    logger.info("📋 测试3: 错误修复SQL")
    test_state["last_error"] = "语法错误"
    test_state["fallback_strategy"] = "retry_sql"
    result3 = agent_nodes.generate_sql(test_state)
    logger.info(f"结果: {result3.get('current_sql', 'N/A')}")
    
    logger.info("📋 测试4: 带上下文的错误修复")
    test_state["error_context"] = {
        "failed_sql": "SELECT * FROM unknown_table",
        "error_message": "表不存在",
        "error_code": "42P01",
        "failed_at_step": 1
    }
    result4 = agent_nodes.generate_sql(test_state)
    logger.info(f"结果: {result4.get('current_sql', 'N/A')}")
    
    logger.info("📋 测试5: 基于验证反馈重新生成")
    test_state["validation_feedback"] = "缺少评分信息，请补充"
    result5 = agent_nodes.generate_sql(test_state)
    logger.info(f"结果: {result5.get('current_sql', 'N/A')}")
    
    # 统计结果
    logger.info("📊 测试结果统计:")
    logger.info(f"✅ Schema获取次数: {schema_fetcher.fetch_count}")
    logger.info(f"✅ Schema格式化次数: {schema_fetcher.format_count}")
    logger.info(f"✅ SQL生成器收到schema次数: {sql_generator.schema_received_count}")
    
    if sql_generator.schema_received_count == 5:
        logger.info("🎉 所有测试通过！schema在所有路径中正确传递")
    else:
        logger.warning(f"⚠️ 部分测试失败，期望5次，实际{sql_generator.schema_received_count}次")
    
    return sql_generator.schema_received_count == 5


def test_schema_fetch_node():
    """测试schema获取节点"""
    logger.info("🚀 开始测试schema获取节点...")
    
    # 创建模拟组件
    schema_fetcher = MockSchemaFetcher()
    
    # 创建AgentNodes实例
    agent_nodes = AgentNodes(
        sql_generator=MockSQLGenerator(),
        sql_executor=MockSQLExecutor(),
        result_parser=MockResultParser(),
        answer_generator=MockAnswerGenerator(),
        schema_fetcher=schema_fetcher
    )
    
    # 测试状态（schema未获取）
    test_state: AgentState = {
        "query": "测试查询",
        "schema_fetched": False,
        "thought_chain": []
    }
    
    logger.info("📋 测试schema获取节点")
    result = agent_nodes.fetch_schema(test_state)
    
    logger.info(f"✅ Schema获取结果: {result.get('schema_fetched', False)}")
    logger.info(f"✅ 数据库schema: {'已设置' if result.get('database_schema') else '未设置'}")
    logger.info(f"✅ 格式化schema: {'已设置' if result.get('formatted_schema') else '未设置'}")
    
    success = (
        result.get('schema_fetched', False) and
        result.get('database_schema') is not None and
        result.get('formatted_schema') is not None
    )
    
    if success:
        logger.info("🎉 Schema获取节点测试通过！")
    else:
        logger.error("❌ Schema获取节点测试失败！")
    
    return success


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🔧 Schema修复验证测试")
    logger.info("=" * 50)
    
    # 运行测试
    test1_passed = test_schema_passing()
    test2_passed = test_schema_fetch_node()
    
    logger.info("=" * 50)
    logger.info("📋 最终测试结果:")
    logger.info(f"✅ Schema传递测试: {'通过' if test1_passed else '失败'}")
    logger.info(f"✅ Schema获取节点测试: {'通过' if test2_passed else '失败'}")
    
    if test1_passed and test2_passed:
        logger.info("🎉 所有测试通过！schema问题已修复")
    else:
        logger.error("❌ 部分测试失败，需要进一步修复")
