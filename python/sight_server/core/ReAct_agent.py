from langgraph.prebuilt import create_react_agent

from .llm import BaseLLM
from .prompts import PromptManager, PromptType
from langgraph.store.postgres import AsyncPostgresStore
from langgraph.checkpoint.postgre import AsyncPostgresSaver
from ..config import settings
m_AsyncPostgresStore = AsyncPostgresStore.from_conn_string(
    settings.DATABASE_URL)
m_AsyncPostgresSaver = AsyncPostgresSaver.from_conn_string(
    settings.DATABASE_URL)

agent = create_react_agent(
    
    
)
