
import logging
from typing import Optional, Dict, Any

from .llm import BaseLLM
from .tools import execute_sql_tool, get_database_schema
from .prompts_v3 import PromptManagerV3
from .query_cache_manager import QueryCacheManager

logger = logging.getLogger(__name__)

class SQLQueryAgentV5:
    """
    优化后的SQL查询Agent (V5)，具备自愈能力。
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: int = 2,
    ):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV5 (Self-Healing)...")

        self.llm = BaseLLM(temperature=temperature)
        self.llm.bind_tools([execute_sql_tool, get_database_schema])
        self.max_retries = max_retries
        self.base_prompt = system_prompt or PromptManagerV3.get_prompt()

    def run(self, query: str) -> Dict[str, Any]:
        """
        执行查询，并在失败时自动重试。
        """
        self.logger.info(f"Processing query with V5 agent: {query}")

        last_error = None
        for attempt in range(self.max_retries + 1):
            self.logger.info(f"Attempt {attempt + 1}/{self.max_retries + 1}")

            # 构建提示，如果存在错误，则加入错误信息
            prompt_addition = f"\nPrevious attempt failed with error: {last_error}. Please analyze the error and provide a corrected SQL query." if last_error else ""
            full_prompt = f"{self.base_prompt}{prompt_addition}\n\nUser Query: {query}"

            # 调用LLM
            response = self.llm.invoke(full_prompt)
            
            # 检查是否有工具调用及其结果
            if response and hasattr(response, 'tool_calls') and response.tool_calls:
                tool_call = response.tool_calls[0]
                if tool_call['name'] == 'execute_sql_tool':
                    # 直接从响应中获取工具调用的结果
                    tool_output = tool_call.get('output') or execute_sql_tool(**tool_call['args'])
                    if tool_output and tool_output.get('status') == 'success':
                        self.logger.info("✓ SQL execution successful.")
                        return {"status": "success", "source": "llm", "data": tool_output, "attempts": attempt + 1}
                    else:
                        last_error = tool_output.get('message', 'Unknown execution error.')
                        self.logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                else:
                    # 如果调用的不是预期的SQL工具，当作成功处理，直接返回
                    return {"status": "success", "source": "llm", "data": response, "attempts": attempt + 1}
            else:
                # 如果没有工具调用，说明LLM直接返回了答案
                return {"status": "success", "source": "llm", "data": response, "attempts": attempt + 1}

        self.logger.error("Query failed after all retries.")
        return {"status": "error", "message": "Query failed after all retries.", "last_error": last_error, "attempts": self.max_retries + 1}

