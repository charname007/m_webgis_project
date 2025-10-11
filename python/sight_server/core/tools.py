
from .database import DatabaseConnector
from typing import Dict, Any, List

def execute_sql_tool(sql: str) -> Dict[str, Any]:
    """
    执行 SQL 查询并返回结果。

    Args:
        sql: 要执行的 SQL 查询语句。

    Returns:
        一个包含查询结果的字典。
    """
    try:
        db_connector = DatabaseConnector()
        # 直接执行原始查询
        raw_result = db_connector.execute_raw_query(sql)
        db_connector.close()
        # 根据返回结果的格式，如果是列表且包含字典，直接返回
        if isinstance(raw_result, list) and all(isinstance(i, dict) for i in raw_result):
            return {"status": "success", "data": raw_result}
        # 如果格式不满足要求，则返回一个提示信息
        return {"status": "success", "data": "查询成功，但结果格式不符合预期，请检查数据库返回。"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_database_schema() -> Dict[str, Any]:
    """
    获取数据库的 schema 信息。

    Returns:
        一个包含数据库 schema 信息的字典。
    """
    try:
        db_connector = DatabaseConnector()
        schema = db_connector.get_schema()
        db_connector.close()
        return {"status": "success", "data": schema}
    except Exception as e:
        return {"status": "error", "message": str(e)}

