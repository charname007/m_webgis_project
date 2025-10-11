
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v2 import SQLQueryAgentV2
from sight_server.core.prompts_v2 import PromptManagerV2, SCENIC_QUERY_PROMPT_V2

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 初始化V2 Agent
agent_v2 = SQLQueryAgentV2(system_prompt=SCENIC_QUERY_PROMPT_V2)

class QueryRequest(BaseModel):
    query: str

@app.post("/query_v2/")
async def query_agent_v2(request: QueryRequest):
    """
    使用V2 Agent处理查询。
    """
    try:
        response = agent_v2.run(request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# uvicorn main_v2:app --reload
