"""
LangGraph工具模块 - Sight Server

提供用于LangGraph框架的agent使用的工具，包括数据库schema获取和SQL执行功能。
这些工具使用@tool装饰器定义，可以与LangGraph的ToolNode无缝集成。
"""

import logging
from typing import List, Optional, Dict, Any

from langchain_core.tools import tool

from .database import DatabaseConnector
from .processors.schema_fetcher import SchemaFetcher
from .processors.sql_executor import SQLExecutor

logger = logging.getLogger(__name__)

# 全局数据库连接器实例
_db_connector: Optional[DatabaseConnector] = None
_schema_fetcher: Optional[SchemaFetcher] = None
_sql_executor: Optional[SQLExecutor] = None


def _get_db_connector() -> DatabaseConnector:
    """
    获取数据库连接器实例（单例模式）
    
    Returns:
        DatabaseConnector实例
    """
    global _db_connector
    if _db_connector is None:
        try:
            _db_connector = DatabaseConnector()
            logger.info("✓ DatabaseConnector initialized for LangGraph tools")
        except Exception as e:
            logger.error(f"✗ Failed to initialize DatabaseConnector: {e}")
            raise
    return _db_connector


def _get_schema_fetcher() -> SchemaFetcher:
    """
    获取SchemaFetcher实例（单例模式）
    
    Returns:
        SchemaFetcher实例
    """
    global _schema_fetcher
    if _schema_fetcher is None:
        try:
            db_connector = _get_db_connector()
            _schema_fetcher = SchemaFetcher(db_connector)
            logger.info("✓ SchemaFetcher initialized for LangGraph tools")
        except Exception as e:
            logger.error(f"✗ Failed to initialize SchemaFetcher: {e}")
            raise
    return _schema_fetcher


def _get_sql_executor() -> SQLExecutor:
    """
    获取SQLExecutor实例（单例模式）
    
    Returns:
        SQLExecutor实例
    """
    global _sql_executor
    if _sql_executor is None:
        try:
            db_connector = _get_db_connector()
            _sql_executor = SQLExecutor(db_connector)
            logger.info("✓ SQLExecutor initialized for LangGraph tools")
        except Exception as e:
            logger.error(f"✗ Failed to initialize SQLExecutor: {e}")
            raise
    return _sql_executor


@tool
def get_schema(
    table_names: Optional[List[str]] = None,
    use_cache: bool = True
) -> str:
    """
    获取数据库schema信息。
    
    此工具用于获取数据库的表结构、字段信息、主键、外键等schema信息。
    支持获取指定表的schema或所有表的schema。
    
    Args:
        table_names: 可选，要获取schema的表名列表。如果为空，则获取所有表的schema。
        use_cache: 是否使用schema缓存，默认为True以提高性能。
        
    Returns:
        格式化的数据库schema信息字符串，包含表结构、字段类型、约束等信息。
        
    Examples:
        >>> get_schema.invoke({"table_names": ["a_sight", "b_region"]})
        "=== 数据库Schema信息 ===\n数据库: PostgreSQL 14.0..."
        
        >>> get_schema.invoke({"use_cache": False})
        "=== 数据库Schema信息 ===\n数据库: PostgreSQL 14.0..."
    """
    try:
        logger.info(f"[Tool: get_schema] Fetching schema for {len(table_names) if table_names else 'all'} tables")
        
        # 获取SchemaFetcher实例
        schema_fetcher = _get_schema_fetcher()
        
        # 获取schema信息
        schema = schema_fetcher.fetch_schema(
            table_names=table_names,
            use_cache=use_cache
        )
        
        # 检查是否有错误
        if "error" in schema:
            error_msg = f"获取schema失败: {schema['error']}"
            logger.error(f"[Tool: get_schema] {error_msg}")
            return error_msg
        
        # 格式化为LLM友好的文本
        formatted_schema = schema_fetcher.format_schema_for_llm(schema)
        
        logger.info(f"[Tool: get_schema] ✓ Successfully fetched schema for {len(schema.get('tables', {}))} tables")
        return formatted_schema
        
    except Exception as e:
        error_msg = f"获取schema时发生错误: {str(e)}"
        logger.error(f"[Tool: get_schema] {error_msg}")
        return error_msg


@tool
def execute_sql(sql_query: str) -> Dict[str, Any]:
    """
    执行SQL查询并返回结果。
    
    此工具用于执行SELECT查询并返回查询结果。支持空间查询和普通查询。
    自动处理结果解析和错误处理。
    
    Args:
        sql_query: 要执行的SQL查询语句。必须是SELECT查询，不支持DML/DDL操作。
        
    Returns:
        查询结果字典，包含:
        - status: "success" 或 "error"
        - data: 查询结果数据列表
        - count: 返回的记录数量
        - error: 错误信息（如果status为"error"）
        
    Examples:
        >>> execute_sql.invoke({"sql_query": "SELECT * FROM a_sight LIMIT 5"})
        {
            "status": "success",
            "data": [{"id": 1, "name": "西湖", ...}],
            "count": 5,
            "error": None
        }
        
        >>> execute_sql.invoke({"sql_query": "SELECT json_agg(json_build_object('name', name)) FROM a_sight"})
        {
            "status": "success", 
            "data": [{"name": "西湖"}, {"name": "千岛湖"}],
            "count": 2,
            "error": None
        }
    """
    try:
        logger.info(f"[Tool: execute_sql] Executing SQL: {sql_query[:200]}...")
        
        # 获取SQLExecutor实例
        sql_executor = _get_sql_executor()
        
        # 验证SQL语法
        validation_result = sql_executor.validate_sql(sql_query)
        if not validation_result["valid"]:
            error_msg = f"SQL验证失败: {validation_result['error']}"
            logger.error(f"[Tool: execute_sql] {error_msg}")
            return {
                "status": "error",
                "data": None,
                "count": 0,
                "error": error_msg
            }
        
        # 执行SQL查询
        execution_result = sql_executor.execute(sql_query)
        
        if execution_result["status"] == "error":
            logger.error(f"[Tool: execute_sql] SQL执行失败: {execution_result['error']}")
            return {
                "status": "error",
                "data": None,
                "count": 0,
                "error": execution_result["error"]
            }
        
        logger.info(f"[Tool: execute_sql] ✓ Successfully executed SQL, returned {execution_result['count']} records")
        
        return {
            "status": "success",
            "data": execution_result["data"],
            "count": execution_result["count"],
            "error": None
        }
        
    except Exception as e:
        error_msg = f"执行SQL时发生错误: {str(e)}"
        logger.error(f"[Tool: execute_sql] {error_msg}")
        return {
            "status": "error",
            "data": None,
            "count": 0,
            "error": error_msg
        }


# 工具列表导出
TOOLS = [get_schema, execute_sql]


def get_all_tools() -> List:
    """
    获取所有可用的LangGraph工具
    
    Returns:
        工具列表，可以直接用于LangGraph的ToolNode
    """
    return TOOLS.copy()


def get_tool_by_name(tool_name: str):
    """
    根据工具名称获取工具实例
    
    Args:
        tool_name: 工具名称（"get_schema" 或 "execute_sql"）
        
    Returns:
        工具实例，如果未找到则返回None
    """
    tool_map = {
        "get_schema": get_schema,
        "execute_sql": execute_sql
    }
    return tool_map.get(tool_name)


# 清理资源函数
def cleanup():
    """清理工具模块的资源"""
    global _db_connector, _schema_fetcher, _sql_executor
    
    if _db_connector:
        try:
            _db_connector.close()
            logger.info("✓ DatabaseConnector closed")
        except Exception as e:
            logger.warning(f"Error closing DatabaseConnector: {e}")
    
    _db_connector = None
    _schema_fetcher = None
    _sql_executor = None


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== LangGraph Tools 测试 ===\n")
    
    try:
        # 测试工具列表
        print("可用工具:")
        for tool in TOOLS:
            print(f"  - {tool.name}: {tool.description}")
        
        print("\n工具模块初始化完成，可以集成到LangGraph中使用")
        
    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        # 清理资源
        cleanup()