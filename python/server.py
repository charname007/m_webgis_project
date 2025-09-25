import asyncio

from sql_query_agent import SQLQueryAgent # pyright: ignore[reportMissingImports]
# import gradio as gr

import fastapi
import uvicorn
app = fastapi.FastAPI()
m_sql_query_agent=SQLQueryAgent()
import m_model

@app.get("/")
def hello():
    return  m_sql_query_agent.run("hello")
@app.get("/query/{query}")
def query(query: str) :
    # 输入验证：限制长度和内容
    if len(query) > 100 or not query.isalnum():
        return {"error": "Invalid query input"}
    try:
        # 使用参数化查询或转义输入
        result =  m_sql_query_agent.run(query)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}
 
# with gr.Blocks() as demo:
#     gr.Markdown("# ChatBot")
#     chatbot = gr.Chatbot(type="messages", height=500)
#     msg = gr.Textbox(label="输入您的问题", placeholder="请输入...")
#     clear = gr.ClearButton([msg, chatbot])

#     async def respond(message, chat_history):
#         # 直接调用异步方法
#         try:
#             if asyncio.iscoroutinefunction(m_sql_query_agent.chat_with_history):
#                 result = await m_sql_query_agent.chat_with_history(message, chat_history)
#             else:
#                 # 如果 chat_with_history 不是协程函数，则使用 run_in_executor
#                 result = await asyncio.get_event_loop().run_in_executor(
#                     None, m_sql_query_agent.chat_with_history, message, chat_history
#                 )
#             # 确保返回的消息格式正确
#             if isinstance(result, dict) and "role" in result and "content" in result:
#                 return result
#             elif hasattr(result, "role") and hasattr(result, "content"):
#                 return {"role": result.role, "content": result.content}
#             else:
#                 # 默认格式转换
#                 return {"role": "assistant", "content": str(result)}
#         except Exception as e:
#             print(f"Error in respond function: {e}")
#             return [{"role": "assistant", "content": "抱歉，处理您的请求时出现了问题。请稍后再试或简化您的问题。"}]

#     msg.submit(respond, [msg, chatbot], [chatbot])
#     msg.submit(lambda: "", None, [msg])  # 清空输入框   
# app = gr.mount_gradio_app(app, demo, path="/")
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
