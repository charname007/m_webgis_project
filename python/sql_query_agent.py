import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Optional, Dict, Any
from langchain.chains import create_sql_query_chain
from param import output
from base_llm import BaseLLM  # pyright: ignore[reportMissingImports]
from sql_connector import SQLConnector  # pyright: ignore[reportMissingImports]
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers.retry import RetryOutputParser
from langchain_core.agents import AgentActionMessageLog
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.schema import AgentAction, AgentFinish

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder


class SQLQueryAgent:
    """SQL查询代理类，用于处理自然语言到SQL查询的转换和执行"""
    
    def __init__(self, system_prompt: Optional[str] = None):
        """
        初始化SQL查询代理
        
        Args:
            system_prompt: 自定义系统提示词，如果为None则使用默认提示词
        """
        self.connector = SQLConnector()
        
        # 创建LLM实例
        self.llm = BaseLLM()
        
        # 如果提供了自定义系统提示词，则使用它
        if system_prompt:
            # 创建包含自定义知识的系统提示词
            custom_prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ])
            
            # 重新配置LLM的提示词
            self.llm.prompt = custom_prompt
        
        self.executor = ThreadPoolExecutor()  # 使用线程池处理异步任务
        
        # 创建SQL代理
        self.agent = create_sql_agent(
            llm=self.llm.llm, 
            db=self.connector.db, 
            verbose=True, 
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
            handle_parsing_errors=True,
            output_parser=RetryOutputParser.from_llm(llm=self.llm.llm, parser=StrOutputParser())
        )
        # 确保输出解析为字符串
        self.chain = self.agent | StrOutputParser()
        
        # 初始化思维链捕获相关变量
        self.thought_chain_log = []
    
    def run(self, query: str) -> str:
        """
        执行SQL查询
        
        Args:
            query: 自然语言查询字符串
            
        Returns:
            SQL查询结果字符串
        """
        try:
            if not isinstance(query, str):
                query = str(query)
            
            # SQL agent expects input as a dictionary with 'input' key
            result = self.agent.invoke({"input": query})
            
            if not isinstance(result, str):
                # Extract the output from the agent result
                if hasattr(result, 'get') and callable(result.get):
                    result = result.get('output', str(result))
                else:
                    result = str(result)
            
            return result
        except Exception as e:
            print(f"Error in run function: {e}")
            return f"抱歉，处理您的请求时出现了问题：{str(e)}"
    
    def run_with_thought_chain(self, query: str) -> Dict[str, Any]:
        """
        执行SQL查询并返回完整的思维链
        
        Args:
            query: 自然语言查询字符串
            
        Returns:
            包含思维链和最终结果的字典
        """
        try:
            if not isinstance(query, str):
                query = str(query)
            
            # 清空之前的思维链日志
            self.thought_chain_log = []
            
            # 创建一个自定义的回调处理器来捕获思维链
            from langchain.callbacks.base import BaseCallbackHandler
            
            class ThoughtChainCallbackHandler(BaseCallbackHandler):
                def __init__(self, agent_instance):
                    self.agent = agent_instance
                    self.steps = []
                
                def on_agent_action(self, action: AgentAction, **kwargs):
                    """捕获Agent的每个Action步骤"""
                    # 直接使用AgentAction的属性，避免复杂的AgentActionMessageLog构造
                    step = {
                        "type": "action",
                        "action": action.tool,
                        "action_input": action.tool_input,
                        "log": action.log,
                        "timestamp": kwargs.get('run_id', 'unknown')
                    }
                    self.steps.append(step)
                    self.agent.thought_chain_log.append(step)
                
                def on_agent_finish(self, finish: AgentFinish, **kwargs):
                    """捕获Agent的完成步骤"""
                    step = {
                        "type": "final_answer",
                        "content": finish.return_values.get('output', ''),
                        "log": finish.log,
                        "timestamp": kwargs.get('run_id', 'unknown')
                    }
                    self.steps.append(step)
                    self.agent.thought_chain_log.append(step)
            
            # 创建回调处理器
            callback_handler = ThoughtChainCallbackHandler(self)
            
            # 执行查询并捕获思维链
            result = self.agent.invoke(
                {"input": query},
                config={"callbacks": [callback_handler]}
            )
            
            # 提取最终结果
            final_result = result
            if not isinstance(result, str):
                if hasattr(result, 'get') and callable(result.get):
                    final_result = result.get('output', str(result))
                else:
                    final_result = str(result)
            
            # 使用format_log_to_str格式化思维链
            formatted_thought_chain = format_log_to_str(self.thought_chain_log) if self.thought_chain_log else ""
            
            return {
                "status": "success",
                "final_answer": final_result,
                "thought_chain": self.thought_chain_log,
                "formatted_thought_chain": formatted_thought_chain,
                "step_count": len(self.thought_chain_log)
            }
            
        except Exception as e:
            print(f"Error in run_with_thought_chain function: {e}")
            return {
                "status": "error",
                "error": f"处理您的请求时出现了问题：{str(e)}",
                "thought_chain": [],
                "formatted_thought_chain": "",
                "step_count": 0
            }
    
    async def chat_with_history(
        self, 
        query: str, 
        chat_history: Optional[List[Tuple[str, str]]] = None, 
        **kwargs
    ) -> Dict[str, str]:
        """
        带聊天历史的异步对话方法
        
        Args:
            query: 当前用户查询
            chat_history: 聊天历史记录，格式为[(用户消息, AI回复), ...]
            **kwargs: 其他参数
            
        Returns:
            包含AI回复的字典
        """
        if chat_history is None:
            chat_history = []

        # 清理聊天历史，移除None值和格式化文本
        cleaned_history = []
        for msg, resp in chat_history:
            if msg is None or resp is None:
                continue
            cleaned_msg = str(msg).replace("\n", " ").strip()
            cleaned_resp = str(resp).replace("\n", " ").strip()
            cleaned_history.append((cleaned_msg, cleaned_resp))

        # 处理空查询和空历史的情况
        if not cleaned_history and not query.strip():
            return {"role": "assistant", "content": self.run("")}

        # 构建包含上下文的完整查询
        context = "\n".join([f"User: {msg}\nAI: {resp}" for msg, resp in cleaned_history])
        full_query = f"{context}\nUser: {query}"

        # 在线程池中异步执行查询
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(self.executor, self.run, full_query)
        
        return {"role": "assistant", "content": result}
    
    def close(self):
        """清理资源"""
        self.executor.shutdown(wait=True)
        # SQLDatabase 对象通常不需要手动关闭，由连接池管理
        # 如果需要清理，可以在这里添加其他资源清理逻辑
