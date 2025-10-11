
import logging
from typing import Optional

from .llm import BaseLLM
from .tools import execute_sql_tool
from .prompts import PromptManager, PromptType

logger = logging.getLogger(__name__)

class SQLQueryAgentV2:
    """
    优化后的SQL查询Agent (V2)，集成了工具调用功能。
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        prompt_type: PromptType = PromptType.SCENIC_QUERY,
    ):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV2 (Tool-Calling Enabled)...")

        self.llm = BaseLLM(temperature=temperature)
        # 将工具绑定到LLM
        self.llm.bind_tools([execute_sql_tool])
        self.logger.info("✓ Tools bound to LLM")

        self.base_prompt = system_prompt or PromptManager.get_prompt(prompt_type)
        self.logger.info(f"✓ Using prompt type: {prompt_type.value}")

    def run(self, query: str):
        """
        执行自然语言查询。

        Args:
            query: 自然语言查询字符串。

        Returns:
            LLM的响应，其中可能包含工具调用的结果。
        """
        self.logger.info(f"Processing query: {query}")
        # 在提示中结合基本提示和用户问题
        full_prompt = f"{self.base_prompt}\n\nUser Query: {query}"
        
        # 调用LLM，LLM将决定是否使用工具
        response = self.llm.invoke(full_prompt)
        self.logger.info(f"✓ Query processed successfully.")
        return response
