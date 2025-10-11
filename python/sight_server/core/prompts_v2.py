
from .prompts import SCENIC_QUERY_PROMPT

# 新的提示模板，增加了工具调用的说明
SCENIC_QUERY_PROMPT_V2 = SCENIC_QUERY_PROMPT + """\nWhen you have generated the SQL query, use the 'execute_sql_tool' to execute it immediately and return the result.
"""

class PromptManagerV2:
    @staticmethod
    def get_prompt(prompt_type):
        if prompt_type.value == 'scenic_query':
            return SCENIC_QUERY_PROMPT_V2
        # 可以为其他提示类型添加V2版本
        return SCENIC_QUERY_PROMPT
