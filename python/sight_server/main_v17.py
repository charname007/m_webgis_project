
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.database import DatabaseConnector
from core.agent_v17 import SQLQueryAgentV17
from core.query_cache_manager import QueryCacheManager # ✅ 导入 QueryCacheManager
from core.schemas import QueryResult
from config import get_settings

# --- FastAPI 应用设置 ---
app = FastAPI(
    title="Sight Server - V17",
    description="在 API 入口层集成缓存守卫的高性能查询代理",
    version="17.0.0"
)

# --- 日志配置 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 全局变量与初始化 ---
settings = get_settings()

db_connector = DatabaseConnector(settings.DATABASE_URL)

try:
    db_schema = db_connector.get_schema_representation()
    logger.info("✓ 成功获取并缓存数据库 Schema。")
except Exception as e:
    logger.error(f"✗ 启动时无法获取数据库 Schema: {e}", exc_info=True)
    db_schema = "Error: Could not fetch database schema on startup."

# ✅ 初始化 V17 Agent
agent = SQLQueryAgentV17(db_connector=db_connector, db_schema=db_schema)

# ✅ 初始化 QueryCacheManager
query_cache_manager = QueryCacheManager(
    cache_dir=settings.CACHE_DIR,
    ttl=settings.CACHE_TTL,
    max_size=settings.CACHE_MAX_SIZE,
    enable_semantic_search=settings.CACHE_SEMANTIC_SEARCH,
    similarity_threshold=settings.CACHE_SIMILARITY_THRESHOLD,
    embedding_model=settings.CACHE_EMBEDDING_MODEL
)


# --- API 模型 ---
class QueryRequest(BaseModel):
    query: str
    conversation_id: str = None
    # 允许前端强制跳过缓存，方便调试
    force_rerun: bool = False

# --- API 端点 ---
@app.post("/v17/query", response_model=QueryResult)
def run_agent_query_with_cache_guard(request: QueryRequest):
    """
    V17 查询端点：实现了“缓存守卫”模式。
    1.  在调用 Agent 前，首先检查缓存（精确匹配+语义匹配）。
    2.  如果缓存命中，直接返回缓存结果，极大提升性能。
    3.  如果缓存未命中，调用 Agent 执行完整流程。
    4.  Agent 成功执行后，将其结果存入缓存以备后用。
    """
    logger.info(f"[V17] 接收到查询: '{request.query}', 会话ID: {request.conversation_id}")

    # --- 缓存守卫逻辑 ---
    if not request.force_rerun:
        # 使用上下文（虽然当前为空）调用缓存管理器
        cached_result = query_cache_manager.get_with_semantic_search(request.query, context={})
        if cached_result:
            logger.info(f"[V17] 缓存命中！直接返回结果。查询: '{request.query}'")
            # 确保返回格式与 QueryResult 匹配
            return QueryResult(
                success=True,
                message="查询成功 (来自缓存)。",
                sql=cached_result.get("sql", "N/A from cache"),
                data=cached_result.get("data"),
                # 可选: 从缓存中提取可视化信息
                visualization=cached_result.get("visualization")
            )
    else:
        logger.info("[V17] 'force_rerun' 为 True, 跳过缓存检查。")

    # --- 缓存未命中，执行 Agent ---
    logger.info("[V17] 缓存未命中，调用 Agent 执行完整流程...")
    try:
        agent_result = agent.run(query=request.query, conversation_id=request.conversation_id)

        if agent_result["success"]:
            logger.info("[V17] Agent 执行成功，准备返回并缓存结果。")
            final_result_data = agent_result["final_result"]

            # ✅ 将成功的结果存入缓存
            query_cache_manager.save_query_cache(
                query_text=agent_result["query"],
                result_data=final_result_data, # 存储 Agent 返回的核心结果
                context={}
            )
            # 同时，也将成功的经验存入长期记忆
            agent.memory_manager.learn_from_query(
                query=agent_result["query"],
                sql=final_result_data.get("sql"),
                result=final_result_data,
                success=True
            )

            return QueryResult(
                success=True,
                message="查询成功 (由 Agent 执行)。",
                sql=final_result_data.get("sql"),
                data=final_result_data.get("data"),
                visualization=agent_result.get("visualization")
            )
        else:
            logger.error(f"[V17] Agent 执行失败: {agent_result.get('error')}")
            # 失败的结果不应该被缓存，但可以记录到长期记忆中以供学习
            agent.memory_manager.learn_from_query(
                query=agent_result["query"],
                sql=None,
                result={"error": agent_result.get("error")},
                success=False
            )
            raise HTTPException(status_code=500, detail=agent_result.get("error"))

    except Exception as e:
        logger.error(f"[V17] 处理查询时发生严重错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI 应用启动... Sight Server V17 缓存守卫模式已激活。")

@app.on_event("shutdown")
async def shutdown_event():
    db_connector.close_connection()
    logger.info("数据库连接已关闭。FastAPI 应用关闭。")

# --- 主程序入口 ---
if __name__ == "__main__":
    # 您可能需要在 config.py 中添加这些新的配置项
    # CACHE_DIR = "./query_cache"
    # CACHE_TTL = 3600
    # CACHE_ENABLE_SEMANTIC_SEARCH = True
    # CACHE_SIMILARITY_THRESHOLD = 0.9
    # EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
