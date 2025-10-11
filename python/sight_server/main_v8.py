
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sight_server.core.agent_v8 import SQLQueryAgentV8
from sight_server.core.prompts_v8 import PromptManagerV8

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 初始化V8 Agent
agent_v8 = SQLQueryAgentV8(system_prompt=PromptManagerV8.get_prompt())

class QueryRequest(BaseModel):
    query: str

@app.post("/query_v8/")
async def query_agent_v8(request: QueryRequest):
    """
    使用V8 Agent处理查询，具备澄清能力。
    """
    try:
        response = agent_v8.run(request.query)
        # V8 的响应可能是数据，也可能是澄清问题，直接返回即可
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# uvicorn main_v8:app --reload
