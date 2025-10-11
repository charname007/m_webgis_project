
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v6 import SQLQueryAgentV6
from sight_server.core.prompts_v3 import SCENIC_QUERY_PROMPT_V3

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 初始化V6 Agent
agent_v6 = SQLQueryAgentV6(system_prompt=SCENIC_QUERY_PROMPT_V3)

class QueryRequest(BaseModel):
    query: str

@app.post("/query_v6/")
async def query_agent_v6(request: QueryRequest):
    """
    使用V6 Agent处理查询，融合了缓存和自愈能力。
    """
    try:
        response = agent_v6.run(request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# uvicorn main_v6:app --reload
