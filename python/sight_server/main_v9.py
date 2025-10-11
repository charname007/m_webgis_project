
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v9 import SQLQueryAgentV9

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 初始化V9 Agent
agent_v9 = SQLQueryAgentV9()

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

@app.post("/query_v9/")
async def query_agent_v9(request: QueryRequest):
    """
    使用V9 Agent处理查询，支持多轮对话。
    """
    try:
        response = agent_v9.run(query=request.query, conversation_id=request.conversation_id)
        return {"response": response}
    except Exception as e:
        # 在真实的生产环境中，应该对错误进行更详细的记录
        logging.error(f"Error processing V9 query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

# uvicorn main_v9:app --reload
