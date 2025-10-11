
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v10 import SQLQueryAgentV10

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 初始化V10 Agent
agent_v10 = SQLQueryAgentV10()

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

@app.post("/query/") # 使用根路径 /query/ 以完全兼容
async def query_agent_v10(request: QueryRequest):
    """
    使用终极版V10 Agent处理查询，输出与V1兼容。
    """
    try:
        response = agent_v10.run(query=request.query, conversation_id=request.conversation_id)
        # 直接返回V10 Agent构建的、V1兼容的字典
        return response
    except Exception as e:
        logging.error(f"Error processing V10 query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

# 为了方便，可以同时保留其他版本的入口以供对比
# from sight_server.main_v9 import query_agent_v9
# app.post("/query_v9/")(query_agent_v9)

# uvicorn main_v10:app --reload
