
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v12 import SQLQueryAgentV12

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 初始化V12 Agent
agent_v12 = SQLQueryAgentV12()

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

@app.post("/query_v12/")
async def query_agent_v12(request: QueryRequest):
    """
    使用V12 Analyst Agent处理可能需要多步推理的复杂查询。
    """
    try:
        response = agent_v12.run(query=request.query, conversation_id=request.conversation_id)
        return {"response": response}
    except Exception as e:
        logging.error(f"Error processing V12 query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

@app.get("/")
async def root():
    return {"message": "SQL Query Analyst Agent V12 is running. Use the /query_v12/ endpoint."}


# uvicorn main_v12:app --reload
