
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v4 import SQLQueryAgentV4
from sight_server.core.prompts_v3 import SCENIC_QUERY_PROMPT_V3

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 初始化V4 Agent
agent_v4 = SQLQueryAgentV4(system_prompt=SCENIC_QUERY_PROMPT_V3)

class QueryRequest(BaseModel):
    query: str

@app.post("/query_v4/")
async def query_agent_v4(request: QueryRequest):
    """
    使用V4 Agent处理查询。
    """
    try:
        response = agent_v4.run(request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# uvicorn main_v4:app --reload
