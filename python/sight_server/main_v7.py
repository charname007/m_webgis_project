
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v7 import SQLQueryAgentV7
from sight_server.core.prompts_v3 import SCENIC_QUERY_PROMPT_V3

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 初始化V7 Agent
agent_v7 = SQLQueryAgentV7(system_prompt=SCENIC_QUERY_PROMPT_V3)

class QueryRequest(BaseModel):
    query: str

@app.post("/query_v7/")
async def query_agent_v7(request: QueryRequest):
    """
    使用V7 Agent处理查询，具备安全验证能力。
    """
    try:
        response = agent_v7.run(request.query)
        # 如果是安全错误，返回400 Bad Request
        if response.get("error_type") == "SECURITY":
            raise HTTPException(status_code=400, detail=response.get("message"))
        return {"response": response}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# uvicorn main_v7:app --reload
