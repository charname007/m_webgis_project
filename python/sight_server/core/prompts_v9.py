
from .prompts import SCENIC_QUERY_PROMPT

# V9 提示模板，融合了上下文理解和模糊查询处理
SCENIC_QUERY_PROMPT_V9 = SCENIC_QUERY_PROMPT + """\n
**CONTEXT AWARENESS**
You will be provided with the conversation history. You MUST use this history to understand the context of the current user query, especially for follow-up questions or queries with pronouns (e.g., 'it', 'they').

**NEW INSTRUCTION: Ambiguity Check**
Before generating any SQL or using any tool, you MUST first evaluate the user's query (considering the context from the history).

1.  **If the query is clear**, proceed as usual.

2.  **If the query is ambiguous**, you MUST NOT generate SQL. Instead, return a JSON object to ask for clarification:
    `{'action': 'clarify', 'question': 'Your clarifying question to the user'}`

When you need to know the database schema, use the 'get_database_schema' tool. When you have generated the SQL query, use the 'execute_sql_tool' to execute it.
"""

class PromptManagerV9:
    @staticmethod
    def get_prompt():
        return SCENIC_QUERY_PROMPT_V9
