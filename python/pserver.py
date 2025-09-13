
# This file is used to create a FastAPI app that serves as a chatbot interface.
import gradio as gr
from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_core.output_parsers import StrOutputParser
from gradio import ChatMessage

import asyncio
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()

# Initialize Neo4j with timeout
try:
    graph = Neo4jGraph(
        url="bolt://localhost:7687",
        username="neo4j",
        password="cznb6666",
        database="neo4j",
        timeout=1000
    )
    logger.info("Successfully connected to Neo4j")
except Exception as e:
    logger.error(f"Failed to connect to Neo4j: {e}")
    graph = None

# Initialize LangChain components
llm = ChatOpenAI(
    temperature=0.7,  # 降低温度以获得更稳定的输出
    model="deepseek-chat",
    openai_api_key="sk-44858716b14c48ebba036313015e4584",
    openai_api_base="https://api.deepseek.com"
)

# 修复提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant working as a guide for Wuhan University. You can answer questions about Wuhan University."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

chain = prompt | llm | StrOutputParser()

# 修复GraphCypherQAChain初始化
if graph:
    try:
        graph.refresh_schema()
        logger.info("Neo4j schema refreshed successfully")
        
        graph_qa = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=True,
            return_direct=False,  # 让LLM处理结果而不是直接返回
            allow_dangerous_requests=True
        )
        logger.info("GraphCypherQAChain initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GraphCypherQAChain: {e}")
        graph_qa = None
else:
    graph_qa = None
    logger.info("No Neo4j connection, skipping GraphCypherQAChain initialization")

# 存储会话历史
store = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# 修复的聊天函数
async def chat_with_timeout(message: str, history):
    try:
        config = {"configurable": {"session_id": "default_session"}}
        
        # 如果有图数据库且问题可能涉及空间查询
        if graph_qa:
            try:
                # # 使用正确的Cypher查询格式
                # corrected_message = message.replace("'", "\\'")  # 转义单引号
                
                # 异步执行图查询
                neo4j_response = await asyncio.wait_for(
                    asyncio.to_thread(
                        graph_qa.invoke, 
                        {"query": message}
                    ),
                    timeout=1000
                )
                print(f"Neo4j response:")
                response = f"根据校园数据库：{neo4j_response}"
                
            except asyncio.TimeoutError:
                print("Neo4j query timeout")
                response = "数据库查询超时，请尝试更简单的问题"
            except Exception as e:
                print(f"Neo4j query error: {e}")
                logger.error(f"Neo4j query error: {e}")
                response = "数据库查询出错，使用通用回答"
                
                # 回退到普通LLM
                llm_response = await chain_with_history.ainvoke(
                    {"input": message},
                    config=config
                )
                response = llm_response
        else:
            # 直接使用LLM
            print("common LLM response")
            llm_response = await chain_with_history.ainvoke(
                {"input": message},
                config=config
            )
            response = llm_response
        
        history.append(ChatMessage(role="user", content=message))
        history.append(ChatMessage(role="assistant", content=response))
        
        return history
        
    except Exception as e:
        print(f"Error in chat function: {e}")
        logger.error(f"Error in chat function: {e}")
        error_msg = "抱歉，处理您的请求时出现了问题"
        history.append(ChatMessage(role="user", content=message))
        history.append(ChatMessage(role="assistant", content=error_msg))
        return history

# 创建Gradio界面
with gr.Blocks() as demo:
    gr.Markdown("# 武汉大学校园助手")
    chatbot = gr.Chatbot(type="messages", height=500)
    msg = gr.Textbox(label="输入您的问题", placeholder="请输入关于武汉大学的问题...")
    clear = gr.ClearButton([msg, chatbot])

    def respond(message, chat_history):
        # 同步调用异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(chat_with_timeout(message, chat_history))
            return result
        finally:
            loop.close()

    msg.submit(respond, [msg, chatbot], [chatbot])
    msg.submit(lambda: "", None, [msg])  # 清空输入框

# Mount Gradio app to FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)












# # This file is used to create a FastAPI app that serves as a chatbot interface.
# import gradio as gr
# from fastapi import FastAPI, HTTPException, Request
# from pydantic import BaseModel
# from langchain_openai import ChatOpenAI
# from langchain.prompts import (
#     ChatPromptTemplate,
#     MessagesPlaceholder,
#     SystemMessagePromptTemplate,
#     HumanMessagePromptTemplate,
# )
# from langchain_core.runnables.history import RunnableWithMessageHistory
# from langchain_community.chat_message_histories import ChatMessageHistory
# # from langchain.chains import LLMChain
# from langchain.memory import ConversationBufferMemory
# from langchain_neo4j import Neo4jGraph,GraphCypherQAChain
# # from langchain.chains import GraphCypherQAChain
# from langchain_core.output_parsers import StrOutputParser
# from gradio import ChatMessage

# import asyncio
# from typing import List
# import json

# # Initialize FastAPI
# app = FastAPI()

# # Initialize Neo4j with timeout
# try:
#     graph = Neo4jGraph(
#         url="bolt://localhost:7687",
#         username="neo4j",
#         password="cznb6666",
#         database="neo4j",
#         timeout=100  # 60 seconds timeout
#     )
# except Exception as e:
#     print(f"Failed to connect to Neo4j: {e}")
#     graph = None

# # Fallback in-memory storage
# # job_seekers = []
# # job_positions = []

# # Initialize LangChain components
# llm = ChatOpenAI(
#     temperature=0.95,
#     model="deepseek-chat",
#     openai_api_key="sk-44858716b14c48ebba036313015e4584",
#     openai_api_base="https://api.deepseek.com"
# )

# prompt = ChatPromptTemplate(
#     messages=[
#         SystemMessagePromptTemplate.from_template(
#             "You are a helpful AI assistant working as a guide for WuHan University. You can answer questions about wuhan university."
#         ),
#         MessagesPlaceholder(variable_name="chat_history"),
#         HumanMessagePromptTemplate.from_template("{question}")
#     ]
# )

# # memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
# # conversation = LLMChain(
# #     llm=llm,
# #     prompt=prompt,
# #     verbose=True,
# #     memory=memory
# # )



# chain = prompt | llm  | StrOutputParser()

# # # Initialize GraphCypherQAChain if Neo4j is available
# if graph:
#     graph_qa = GraphCypherQAChain.from_llm(
#         llm,
#         graph=graph,
#         verbose=True,
#         allow_dangerous_requests=True  # 明确确认了解风险

#     )
    
# # 3. 创建一个存储来管理不同会话的历史记录
# # 这里使用简单的字典在内存中存储，对于生产环境，建议使用数据库
# store = {}

# def get_session_history(session_id: str) -> ChatMessageHistory:
#     if session_id not in store:
#         store[session_id] = ChatMessageHistory()
#     return store[session_id]

# # 4. 使用 RunnableWithMessageHistory 包装核心链
# chain_with_history = RunnableWithMessageHistory(
#     chain,
#     get_session_history, # 提供获取历史记录的函数
#     input_messages_key="input", # 输入中用户问题的键
#     history_messages_key="chat_history", # 提示模板中历史消息的变量名
# )

# # 5. 调用时，需要传入 config 来指定会话 ID
# # 这样，同一个 session_id 的对话会自动共享历史
# config = {"configurable": {"session_id": "user_123"}} # 可以为每个用户或会话设置唯一的 ID

# # Define chat function with timeout
# async def chat_with_timeout(message, history):
#     try:
#         if graph:
#             neo4j_response = await asyncio.wait_for(
#                 asyncio.to_thread(graph_qa.run, message),
#                 timeout=30.0  # 10 seconds timeout
#             )
#             history.append(ChatMessage(role="assistant", content=f"Based on our database: {neo4j_response}"))
#         else:
#             response = chain_with_history.invoke({"question": message})
#             history.append(ChatMessage(role="assistant", content=response.get('text', 'No response')))
#         return history
#     except asyncio.TimeoutError:
#         history.append(ChatMessage(role="assistant", content="I'm sorry, but the database query took too long. Please try a simpler question or try again later."))
#         return history
#     except Exception as e:
#         print(f"Error in chat function: {e}")
#         history.append(ChatMessage(role="assistant", content="An error occurred. Please try again later."))
#         return history


# # # Create Gradio interface
# # iface = gr.ChatInterface(chat_with_timeout,type='messages')
# # Create Gradio interface
# with gr.Blocks() as demo:
#     chatbot = gr.Chatbot(type="messages")
#     msg = gr.Textbox()
#     clear = gr.ClearButton([msg, chatbot])

#     msg.submit(chat_with_timeout, [msg, chatbot], [chatbot])

# #
# # # Mount Gradio app to FastAPI
# app = gr.mount_gradio_app(app, demo, path="/")

# # Run the app
# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="0.0.0.0", port=8000)