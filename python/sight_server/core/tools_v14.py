
# V14 版本的工具集，增加了数据可视化能力

from .database import DatabaseConnector
from .sql_validator import SQLValidator
from .visualizer import Visualizer # 导入我们的渲染器
from typing import Dict, Any, List

# --- 工具定义 ---

sql_validator = SQLValidator()
visualizer = Visualizer() # 创建一个渲染器实例

def execute_sql_tool(sql: str) -> Dict[str, Any]:
    # ... (此函数与v13/v11版本完全相同) ...
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

def web_search_tool(query: str, allowed_domains: List[str] = None) -> Dict[str, Any]:
    # ... (此函数与v13版本完全相同) ...
    try:
        mock_result = {
            "search_query": query,
            "results": [
                {"title": f"Search result for '{query}'", "snippet": "This is a simulated web search result.", "url": "https://example.com"}
            ]
        }
        return {"status": "success", "data": mock_result}
    except Exception as e:
        return {"status": "error", "message": f"Web search failed: {e}"}

def generate_visualization_config(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes structured data and generates a configuration for frontend visualization.
    Use this tool AFTER you have successfully retrieved data and believe it can be visualized (e.g., on a map or chart).
    """
    try:
        config = visualizer.generate_config(data)
        if config:
            return {"status": "success", "config": config}
        else:
            return {"status": "no_config", "message": "No suitable visualization found for the given data."}
    except Exception as e:
        return {"status": "error", "message": f"Visualization config generation failed: {e}"}
