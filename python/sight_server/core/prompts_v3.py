
from .prompts import SCENIC_QUERY_PROMPT

# 新的提示模板，增加了对两个工具的说明
SCENIC_QUERY_PROMPT_V3 = SCENIC_QUERY_PROMPT + """\nIf you need to know the database schema, use the 'get_database_schema' tool. When you have generated the SQL query, use the 'execute_sql_tool' to execute it immediately and return the result.
"""

class PromptManagerV3:
    @staticmethod
    def get_prompt():
        return SCENIC_QUERY_PROMPT_V3
