
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v13 import SQLQueryAgentV13

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 初始化V13 Agent
agent_v13 = SQLQueryAgentV13()

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

@app.post("/query_v13/")
async def query_agent_v13(request: QueryRequest):
    """
    使用V13 Know-it-all Agent处理查询，支持数据库和网络搜索。
    """
    try:
        response = agent_v13.run(query=request.query, conversation_id=request.conversation_id)
        return {"response": response}
    except Exception as e:
        logging.error(f"Error processing V13 query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

@app.get("/")
async def root():
    return {"message": "SQL Query Know-it-all Agent V13 is running. Use the /query_v13/ endpoint."}


# uvicorn main_v13:app --reload
