
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v11 import SQLQueryAgentV11

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 初始化V11 Agent
# 注意：所有的复杂性（如加载schema）都已封装在Agent的__init__中
agent_v11 = SQLQueryAgentV11()

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

@app.post("/query_v11/")
async def query_agent_v11(request: QueryRequest):
    """
    使用终极版 V11 Agent 处理查询。
    """
    try:
        response = agent_v11.run(query=request.query, conversation_id=request.conversation_id)
        return response
    except Exception as e:
        logging.error(f"Error processing V11 query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

@app.get("/")
async def root():
    return {"message": "SQL Query Agent V11 is running. Use the /query_v11/ endpoint to interact."}


# uvicorn main_v11:app --reload
