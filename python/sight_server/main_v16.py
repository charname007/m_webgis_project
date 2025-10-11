
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.database import DatabaseConnector
from core.agent_v16 import SQLQueryAgentV16  # ✅ 导入 V16 Agent
from core.schemas import QueryResult
from config import get_settings

# --- FastAPI 应用设置 ---
app = FastAPI(
    title="Sight Server - V16",
    description="搭载真实 Embedding 和数据库持久化的 SQL 查询代理",
    version="16.0.0"
)

# --- 日志配置 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 全局变量 ---
settings = get_settings()

# 初始化数据库连接器
db_connector = DatabaseConnector(settings.DATABASE_URL)

# 动态获取并缓存数据库 Schema
try:
    db_schema = db_connector.get_schema_representation()
    logger.info("✓ 成功获取并缓存数据库 Schema。")
except Exception as e:
    logger.error(f"✗ 启动时无法获取数据库 Schema: {e}", exc_info=True)
    db_schema = "Error: Could not fetch database schema on startup."

# ✅ 初始化 V16 Agent
agent = SQLQueryAgentV16(db_connector=db_connector, db_schema=db_schema)

# --- API 模型 ---
class QueryRequest(BaseModel):
    query: str
    conversation_id: str = None

# --- API 端点 ---
@app.post("/v16/query", response_model=QueryResult)
def run_agent_query(request: QueryRequest):
    """
    运行 V16 Agent 来处理自然语言查询。
    - 支持通过 conversation_id 进行多轮对话。
    - 利用数据库进行 Checkpoint 和 Memory 的持久化。
    - 使用真实的 sentence-transformers 模型进行语义搜索。
    """
    logger.info(f"接收到 V16 查询请求: '{request.query}' (会话 ID: {request.conversation_id})")
    try:
        result = agent.run(query=request.query, conversation_id=request.conversation_id)
        return result
    except Exception as e:
        logger.error(f"处理查询时发生意外错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI 应用启动... Sight Server V16 已就绪。")

@app.on_event("shutdown")
async def shutdown_event():
    db_connector.close_connection()
    logger.info("数据库连接已关闭。FastAPI 应用关闭。")

# --- 主程序入口 ---
if __name__ == "__main__":
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

