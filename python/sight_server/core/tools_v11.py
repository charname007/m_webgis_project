
# V11 版本的工具集，不再需要 get_database_schema

from .database import DatabaseConnector
from .sql_validator import SQLValidator
from typing import Dict, Any

sql_validator = SQLValidator()

def execute_sql_tool(sql: str) -> Dict[str, Any]:
    """
    执行经过安全验证的SQL查询。
    """
    is_safe, message = sql_validator.validate(sql)
    if not is_safe:
        return {"status": "error", "message": message, "error_type": "SECURITY_VALIDATION_FAILED"}

    try:
        db_connector = DatabaseConnector()
        raw_result = db_connector.execute_raw_query(sql)
        db_connector.close()
        
        if isinstance(raw_result, list) and all(isinstance(i, dict) for i in raw_result):
            return {"status": "success", "data": raw_result}
        return {"status": "success", "data": "Query executed, but result format is not as expected."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

