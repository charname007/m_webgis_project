
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v14 import SQLQueryAgentV14

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI-Powered Data Visualization Agent API",
    description="The ultimate V14 Agent endpoint."
)

# 初始化V14 Agent
agent_v14 = SQLQueryAgentV14()

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

@app.post("/query/") # 使用根路径，因为这是我们的最终生产版本
async def query_agent_v14(request: QueryRequest):
    """
    使用 V14 Visualizer Agent 处理查询，返回包含可选可视化配置的结果。
    """
    try:
        response = agent_v14.run(query=request.query, conversation_id=request.conversation_id)
        return response
    except Exception as e:
        logging.error(f"Error processing V14 query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

@app.get("/")
async def root():
    return {"message": "SQL Query Visualizer Agent V14 is running. Use the /query/ endpoint."}


# uvicorn main_v14:app --reload
