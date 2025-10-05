"""
LLM基础类模块 - Sight Server
提供LangChain LLM封装，支持聊天历史和配置管理
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from config import settings
import logging

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
        outparser: Optional[StrOutputParser] = None
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

        # 设置提示词模板
        self.prompt = prompt or self._get_default_prompt()

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
            f"api_base={self.api_base}"
        )

    def _get_default_prompt(self) -> ChatPromptTemplate:
        """
        获取默认提示词模板

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
        config = {"configurable": {"session_id": session_id}}
        try:
            response = self.chain_with_history.invoke(
                {"input": input_text},
                config=config
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
            response = self.chain.invoke({"input": input_text})
            logger.debug(f"LLM response (no history): {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"Error invoking LLM without history: {e}")
            raise

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
