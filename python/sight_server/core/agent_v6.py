
import logging
from typing import Optional, Dict, Any

from .llm import BaseLLM
from .tools import execute_sql_tool, get_database_schema
from .prompts_v3 import PromptManagerV3
from .query_cache_manager import QueryCacheManager

logger = logging.getLogger(__name__)

class SQLQueryAgentV6:
    """
    优化后的SQL查询Agent (V6)，融合了缓存、多工具和自愈能力。
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: int = 2,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
    ):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV6 (Cache + Self-Healing)...")

        self.llm = BaseLLM(temperature=temperature)
        self.llm.bind_tools([execute_sql_tool, get_database_schema])
        self.max_retries = max_retries
        self.base_prompt = system_prompt or PromptManagerV3.get_prompt()
        
        self.cache_manager = None
        if enable_cache:
            try:
                self.cache_manager = QueryCacheManager(ttl=cache_ttl)
                self.logger.info("✓ QueryCacheManager initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize QueryCacheManager: {e}")

    def run(self, query: str) -> Dict[str, Any]:
        """
        执行查询，融合缓存和自愈机制。
        """
        self.logger.info(f"Processing query with V6 agent: {query}")

        # 步骤 1: 查询缓存
        if self.cache_manager:
            cached_result = self.cache_manager.get(query)
            if cached_result:
                self.logger.info("✓ Cache hit! Returning cached result.")
                return {"status": "success", "source": "cache", "data": cached_result}

        self.logger.info("Cache miss. Proceeding with self-healing LLM query.")

        # 步骤 2: 缓存未命中，启动自愈循环
        last_error = None
        for attempt in range(self.max_retries + 1):
            self.logger.info(f"Attempt {attempt + 1}/{self.max_retries + 1}")

            prompt_addition = f"\nPrevious attempt failed with error: {last_error}. Please correct the query." if last_error else ""
            full_prompt = f"{self.base_prompt}{prompt_addition}\n\nUser Query: {query}"

            response = self.llm.invoke(full_prompt)

            if response and hasattr(response, 'tool_calls') and response.tool_calls:
                tool_call = response.tool_calls[0]
                if tool_call['name'] == 'execute_sql_tool':
                    tool_output = tool_call.get('output') or execute_sql_tool(**tool_call['args'])
                    if tool_output and tool_output.get('status') == 'success':
                        self.logger.info("✓ SQL execution successful.")
                        # 步骤 3: 成功后，填充缓存
                        if self.cache_manager:
                            self.cache_manager.set(query, tool_output)
                            self.logger.info("✓ New result stored in cache.")
                        return {"status": "success", "source": "llm", "data": tool_output, "attempts": attempt + 1}
                    else:
                        last_error = tool_output.get('message', 'Unknown execution error.')
                        self.logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                else:
                    return {"status": "success", "source": "llm", "data": response, "attempts": attempt + 1}
            else:
                return {"status": "success", "source": "llm", "data": response, "attempts": attempt + 1}

        self.logger.error("Query failed after all retries.")
        return {"status": "error", "message": "Query failed after all retries.", "last_error": last_error, "attempts": self.max_retries + 1}
