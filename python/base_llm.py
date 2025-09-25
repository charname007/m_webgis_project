from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from openai import base_url


class base_llm:
    def __init__(self, temperature=1.3, model="deepseek-chat", openai_api_key="sk-44858716b14c48ebba036313015e4584", openai_api_base="https://api.deepseek.com", prompt=ChatPromptTemplate.from_messages([
                ("system", "You are a helpful AI assistant."),
        MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
    ]),outparser=StrOutputParser()):
        self.llm = ChatOpenAI(
            temperature=temperature,
            model="deepseek-chat",
            api_key="sk-44858716b14c48ebba036313015e4584",
            base_url="https://api.deepseek.com"
        )
        self.chat_history = ChatMessageHistory()
        self.history_store = {}
        self.prompt = prompt
        self.chain = self.prompt | self.llm | outparser
        self.chain_with_history = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        if session_id not in self.history_store:
            self.history_store[session_id] = ChatMessageHistory()
        return self.history_store[session_id]
