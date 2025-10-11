
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v15 import SQLQueryAgentV15

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Persistent AI Data Agent API (V15)",
    description="The final, enterprise-ready version with DB-backed memory and checkpoints."
)

# 初始化V15 Agent
agent_v15 = SQLQueryAgentV15()

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

@app.post("/query/") # 使用根路径，代表这是最终的生产版本
async def query_agent_v15(request: QueryRequest):
    """
    使用 V15 Persistent Agent 处理查询。
    """
    try:
        response = agent_v15.run(query=request.query, conversation_id=request.conversation_id)
        return response
    except Exception as e:
        logging.error(f"Error processing V15 query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

@app.get("/")
async def root():
    return {"message": "SQL Query Persistent Agent V15 is running. Use the /query/ endpoint."}


# uvicorn main_v15:app --reload
