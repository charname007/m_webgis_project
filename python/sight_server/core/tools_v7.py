
from .database import DatabaseConnector
from .sql_validator import SQLValidator  # 导入验证器
from typing import Dict, Any

# 初始化一个验证器实例，可以在模块级别共享
sql_validator = SQLValidator()

def execute_sql_tool(sql: str) -> Dict[str, Any]:
    """
    执行经过安全验证的SQL查询。
    """
    # 步骤 1: 安全验证
    is_safe, message = sql_validator.validate(sql)
    if not is_safe:
        # 如果不安全，立即返回错误，不执行数据库操作
        return {"status": "error", "message": message, "error_type": "SECURITY_VALIDATION_FAILED"}

    # 步骤 2: 只有在验证通过后才执行查询
    try:
        db_connector = DatabaseConnector()
        raw_result = db_connector.execute_raw_query(sql)
        db_connector.close()
        
        if isinstance(raw_result, list) and all(isinstance(i, dict) for i in raw_result):
            return {"status": "success", "data": raw_result}
        return {"status": "success", "data": "Query executed, but result format is not as expected."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# get_database_schema 工具不需要安全验证，保持不变
def get_database_schema() -> Dict[str, Any]:
    """
    获取数据库的 schema 信息。
    """
    try:
        db_connector = DatabaseConnector()
        schema = db_connector.get_schema()
        db_connector.close()
        return {"status": "success", "data": schema}
    except Exception as e:
        return {"status": "error", "message": str(e)}

