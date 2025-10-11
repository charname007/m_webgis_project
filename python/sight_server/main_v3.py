
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v3 import SQLQueryAgentV3
from sight_server.core.prompts_v3 import SCENIC_QUERY_PROMPT_V3

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 初始化V3 Agent
agent_v3 = SQLQueryAgentV3(system_prompt=SCENIC_QUERY_PROMPT_V3)

class QueryRequest(BaseModel):
    query: str

@app.post("/query_v3/")
async def query_agent_v3(request: QueryRequest):
    """
    使用V3 Agent处理查询。
    """
    try:
        response = agent_v3.run(request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# uvicorn main_v3:app --reload
