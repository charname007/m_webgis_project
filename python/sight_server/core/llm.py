"""
LLM基础类模块 - Sight Server
提供LangChain LLM封装，支持聊天历史和配置管理
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from config import settings
import logging
from .graph.context_schemas import LLMContextSchema

logger = logging.getLogger(__name__)


class BaseLLM:
    """
    LLM基础类，封装LangChain的ChatOpenAI

    功能:
    - 支持聊天历史记录
    - 自动从配置文件加载参数
    - 支持自定义提示词和输出解析器
    - 会话管理
    """

    def __init__(
        self,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        prompt: Optional[ChatPromptTemplate] = None,
        outparser: Optional[StrOutputParser] = None,
        system_context: Optional[Dict[str, Any]] = None
    ):
        """
        初始化LLM实例

        Args:
            temperature: 温度参数(0.0-2.0)，控制随机性。默认使用配置文件
            model: 模型名称。默认使用配置文件
            api_key: API密钥。默认使用配置文件
            api_base: API基础URL。默认使用配置文件
            prompt: 自定义提示词模板
            outparser: 自定义输出解析器
            system_context: 系统上下文信息（如数据库schema）
        """
        # 使用配置文件中的值作为默认值，允许参数覆盖
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        if not self.api_key:
            raise ValueError(
                "API key is required. Please set DEEPSEEK_API_KEY in .env file "
                "or pass api_key parameter"
            )

        # 使用配置文件中的默认值
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.model = model or settings.LLM_MODEL
        self.api_base = api_base or settings.DEEPSEEK_API_BASE

        # 初始化系统上下文
        self.system_context = system_context or {}
        self.custom_system_prompt: Optional[str] = None

        # 设置提示词模板
        self.prompt = prompt or self._build_prompt_from_context()

        # 设置输出解析器
        self.outparser = outparser or StrOutputParser()

        # 初始化LLM
        self.llm = ChatOpenAI(
            temperature=self.temperature,
            model=self.model,
            api_key=self.api_key,
            base_url=self.api_base
        )

        # 初始化历史记录存储
        self.history_store = {}

        # 创建链
        self.chain = self.prompt | self.llm | self.outparser

        # 创建支持历史记录的链
        self.chain_with_history = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

        logger.info(
            f"BaseLLM initialized: model={self.model}, "
            f"temperature={self.temperature}, "
            f"api_base={self.api_base}, "
            f"system_context_keys={list(self.system_context.keys())}"
        )

    def _build_prompt_from_context(self) -> ChatPromptTemplate:
        """
        基于system_context构建提示词模板

        Returns:
            构建的ChatPromptTemplate
        """
        system_message = self._build_system_message()
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
    
    def _build_system_message(self) -> str:
        """
        构建系统消息，包含数据库schema等上下文

        Returns:
            系统消息文本
        """
        # 如果没有系统上下文，使用默认提示词
        if self.custom_system_prompt:
            return self.custom_system_prompt

        if not self.system_context:
            return "You are a helpful AI assistant."
        
        # 构建专业的系统提示词
        system_parts = ["你是一个精通PostgreSQL和PostGIS的SQL专家，专门处理全国景区旅游数据查询。"]
        
        # 添加数据库schema信息
        if "database_schema" in self.system_context:
            schema = self.system_context["database_schema"]
            if isinstance(schema, str) and schema.strip():
                system_parts.append(f"\n**数据库Schema信息**:\n{schema}")
        
        # 添加核心职责
        system_parts.extend([
            "\n**核心职责**:",
            "- 将自然语言查询转换为准确的SQL语句",
            "- 运用PostGIS专业知识处理空间查询", 
            "- 确保查询性能和结果准确性",
            "- 遵循最佳SQL实践"
        ])
        
        return "\n".join(system_parts)
    
    def set_system_prompt(self, system_prompt: str):
        """
        覆盖当前LLM的system prompt

        Args:
            system_prompt: 含有数据库schema等上下文的system message
        """
        if not system_prompt or not system_prompt.strip():
            logger.warning("set_system_prompt called with empty prompt, ignoring")
            return

        cleaned_prompt = system_prompt.strip()
        if cleaned_prompt == self.custom_system_prompt:
            logger.debug("System prompt unchanged; skipping rebuild")
            return

        self.custom_system_prompt = cleaned_prompt
        self._rebuild_prompt()
        logger.info("Custom system prompt updated (length=%s)", len(cleaned_prompt))

    def update_system_context(self, context_updates: Dict[str, Any]):
        """
        更新系统上下文并重建prompt

        Args:
            context_updates: 要更新的上下文信息
        """
        self.system_context.update(context_updates)
        self._rebuild_prompt()
        logger.info(f"System context updated: {list(context_updates.keys())}")
    
    def _rebuild_prompt(self):
        """重建提示词模板"""
        self.prompt = self._build_prompt_from_context()
        
        # 重新创建链
        self.chain = self.prompt | self.llm | self.outparser
        self.chain_with_history = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        logger.debug("Prompt rebuilt with updated system context")
    
    def _get_default_prompt(self) -> ChatPromptTemplate:
        """
        获取默认提示词模板（向后兼容）

        Returns:
            默认的ChatPromptTemplate
        """
        return ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """
        获取或创建会话历史记录

        Args:
            session_id: 会话唯一标识符

        Returns:
            ChatMessageHistory对象
        """
        if session_id not in self.history_store:
            self.history_store[session_id] = ChatMessageHistory()
        return self.history_store[session_id]

    def invoke(self, input_text: str, session_id: str = "default") -> str:
        """
        调用LLM处理输入文本

        Args:
            input_text: 输入文本
            session_id: 会话ID，用于历史记录跟踪

        Returns:
            LLM响应文本
        """
        context = LLMContextSchema(session_id=session_id)
        try:
            response = self.chain_with_history.invoke(
                {"input": input_text},
                context=context
            )
            logger.debug(f"LLM response for session {session_id}: {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"Error invoking LLM: {e}")
            raise

    def invoke_without_history(self, input_text: str) -> str:
        """
        调用LLM处理输入文本（不保存历史记录）

        Args:
            input_text: 输入文本

        Returns:
            LLM响应文本
        """
        try:
            # 创建一个不包含历史记录的简单prompt
            simple_prompt = self._build_simple_prompt()
            simple_chain = simple_prompt | self.llm | self.outparser
            response = simple_chain.invoke({"input": input_text})
            logger.debug(f"LLM response (no history): {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"Error invoking LLM without history: {e}")
            raise

    def _build_simple_prompt(self) -> ChatPromptTemplate:
        """
        构建不包含历史记录的简单提示词模板

        Returns:
            简单的ChatPromptTemplate
        """
        system_message = self._build_system_message()
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{input}")
        ])

    def clear_session_history(self, session_id: str):
        """
        清除指定会话的历史记录

        Args:
            session_id: 会话ID
        """
        if session_id in self.history_store:
            self.history_store[session_id].clear()
            logger.info(f"Session history cleared for: {session_id}")

    def clear_all_histories(self):
        """清除所有会话历史记录"""
        self.history_store.clear()
        logger.info("All session histories cleared")

    def get_all_sessions(self) -> list:
        """
        获取所有会话ID列表

        Returns:
            会话ID列表
        """
        return list(self.history_store.keys())

    def get_session_message_count(self, session_id: str) -> int:
        """
        获取指定会话的消息数量

        Args:
            session_id: 会话ID

        Returns:
            消息数量
        """
        if session_id in self.history_store:
            return len(self.history_store[session_id].messages)
        return 0


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # 创建LLM实例
        llm = BaseLLM()

        # 测试基本调用
        print("\n=== 测试1: 基本调用（无历史） ===")
        response = llm.invoke_without_history("你好，请介绍一下自己")
        print(f"Response: {response}")

        # 测试会话调用
        print("\n=== 测试2: 会话调用（带历史） ===")
        session_id = "test_session"
        response1 = llm.invoke("我的名字是张三", session_id=session_id)
        print(f"Response 1: {response1}")

        response2 = llm.invoke("我刚才说我叫什么？", session_id=session_id)
        print(f"Response 2: {response2}")

        # 查看会话信息
        print(f"\n会话消息数量: {llm.get_session_message_count(session_id)}")

        # 清除历史
        llm.clear_session_history(session_id)
        print("历史记录已清除")

    except Exception as e:
        print(f"Error: {e}")
