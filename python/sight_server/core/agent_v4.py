
import logging
from typing import Optional, Dict, Any

from .llm import BaseLLM
from .tools import execute_sql_tool, get_database_schema
from .prompts_v3 import PromptManagerV3
from .query_cache_manager import QueryCacheManager # 更改导入

logger = logging.getLogger(__name__)

class SQLQueryAgentV4:
    """
    优化后的SQL查询Agent (V4)，集成了语义缓存和多工具调用。
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
    ):
        self.logger = logger
        self.logger.info("Initializing SQLQueryAgentV4 (Cache + Multi-Tool)...")

        # 初始化 LLM 和工具
        self.llm = BaseLLM(temperature=temperature)
        self.llm.bind_tools([execute_sql_tool, get_database_schema])
        self.logger.info("✓ Tools bound to LLM")

        # 初始化提示
        self.base_prompt = system_prompt or PromptManagerV3.get_prompt()

        # 初始化缓存管理器
        self.cache_manager = None
        if enable_cache:
            try:
                self.cache_manager = QueryCacheManager(ttl=cache_ttl)
                self.logger.info("✓ QueryCacheManager initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize QueryCacheManager: {e}")

    def run(self, query: str) -> Dict[str, Any]:
        """
        执行自然语言查询，优先使用缓存。
        """
        self.logger.info(f"Processing query with V4 agent: {query}")

        # 步骤 1: 查询缓存
        if self.cache_manager:
            cached_result = self.cache_manager.get(query)
            if cached_result:
                self.logger.info("✓ Cache hit! Returning cached result.")
                return {"status": "success", "source": "cache", "data": cached_result}

        self.logger.info("Cache miss. Proceeding with LLM query.")

        # 步骤 2: 缓存未命中，调用 LLM
        full_prompt = f"{self.base_prompt}\n\nUser Query: {query}"
        response = self.llm.invoke(full_prompt)

        # 步骤 3: 填充缓存
        if self.cache_manager and response:
            # 假设 response 包含可缓存的数据
            self.cache_manager.set(query, response)
            self.logger.info("✓ New result stored in cache.")

        return {"status": "success", "source": "llm", "data": response}
