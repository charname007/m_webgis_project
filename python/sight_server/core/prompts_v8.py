
from .prompts import SCENIC_QUERY_PROMPT

# V8 提示模板，增加了处理模糊查询的逻辑
SCENIC_QUERY_PROMPT_V8 = SCENIC_QUERY_PROMPT + """\n
**NEW INSTRUCTION: Ambiguity Check**
Before generating any SQL or using any tool, you MUST first evaluate the user's query for ambiguity.

1.  **If the query is clear and specific enough** to be translated into a precise SQL query, proceed as usual.

2.  **If the query is ambiguous** (e.g., uses subjective terms like 'popular', 'best', or has an unclear scope), you MUST NOT generate SQL. Instead, you MUST return a JSON object with the following structure to ask for clarification:
    `{'action': 'clarify', 'question': 'Your clarifying question to the user'}`
"""

class PromptManagerV8:
    @staticmethod
    def get_prompt():
        return SCENIC_QUERY_PROMPT_V8
