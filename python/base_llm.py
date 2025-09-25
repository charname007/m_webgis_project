from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
import os


class BaseLLM:
    """Base class for LLM operations with chat history support."""
    
    def __init__(self, temperature=1.3, model="deepseek-chat", 
                 openai_api_key=None, openai_api_base="https://api.deepseek.com",
                 prompt=None, outparser=None):
        """
        Initialize the LLM with configuration.
        
        Args:
            temperature: Controls randomness (0.0 to 2.0)
            model: Model name to use
            openai_api_key: API key (defaults to environment variable)
            openai_api_base: Base URL for API
            prompt: Custom prompt template
            outparser: Custom output parser
        """
        # Get API key from environment if not provided
        self.api_key = openai_api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set as DEEPSEEK_API_KEY environment variable")
        
        # Set default prompt template if not provided
        self.prompt = prompt or self._get_default_prompt()
        
        # Set default output parser if not provided
        self.outparser = outparser or StrOutputParser()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            temperature=temperature,
            model=model,
            api_key=self.api_key,
            base_url=openai_api_base
        )
        
        # Initialize history storage
        self.history_store = {}
        
        # Create chain
        self.chain = self.prompt | self.llm | self.outparser
        
        # Create chain with history support
        self.chain_with_history = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
    
    def _get_default_prompt(self):
        """Get the default prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
    
    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """
        Get or create chat history for a session.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            ChatMessageHistory object for the session
        """
        if session_id not in self.history_store:
            self.history_store[session_id] = ChatMessageHistory()
        return self.history_store[session_id]
    
    def invoke(self, input_text: str, session_id: str = "default"):
        """
        Invoke the LLM with input text and session history.
        
        Args:
            input_text: Input text to send to LLM
            session_id: Session identifier for history tracking
            
        Returns:
            LLM response
        """
        config = {"configurable": {"session_id": session_id}}
        return self.chain_with_history.invoke(
            {"input": input_text},
            config=config
        )
    
    def clear_session_history(self, session_id: str):
        """
        Clear chat history for a specific session.
        
        Args:
            session_id: Session identifier to clear
        """
        if session_id in self.history_store:
            self.history_store[session_id].clear()
    
    def clear_all_histories(self):
        """Clear all chat histories."""
        self.history_store.clear()
