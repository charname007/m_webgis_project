
import logging
from typing import Optional

from .llm import BaseLLM
from .tools import execute_sql_tool, get_database_schema
from .prompts_v3 import PromptManagerV3, SCENIC_QUERY_PROMPT_V3

logger = logging.getLogger(__name__)

class SQLQueryAgentV3:
    """
    优化后的SQL查询Agent (V3)，集成了SQL执行和Schema获取工具。
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV3 (Multi-Tool Enabled)...")

        self.llm = BaseLLM(temperature=temperature)
        # 绑定多个工具
        self.llm.bind_tools([execute_sql_tool, get_database_schema])
        self.logger.info("✓ SQL and Schema tools bound to LLM")

        self.base_prompt = system_prompt or PromptManagerV3.get_prompt()
        self.logger.info(f"✓ Using V3 prompt")

    def run(self, query: str):
        """
        执行自然语言查询。
        """
        self.logger.info(f"Processing query with V3 agent: {query}")
        full_prompt = f"{self.base_prompt}\n\nUser Query: {query}"
        
        response = self.llm.invoke(full_prompt)
        self.logger.info(f"✓ V3 query processed successfully.")
        return response
