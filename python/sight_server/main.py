"""
Sight Server - FastAPI 主应用
基于 LangChain Agent 的景区数据自然语言查询 API 服务
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from core import SQLQueryAgent
from models import (
    QueryRequest,
    QueryResponse,
    GeoJSONRequest,
    GeoJSONResponse,
    ThoughtChainRequest,
    ThoughtChainResponse,
    HealthResponse,
    ErrorResponse,
    QueryStatus
)
from utils import GeoJSONConverter, CoordinateConverter
from utils.geojson_utils import CoordinateSystem

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    datefmt=settings.LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)

# 全局变量
sql_agent: Optional[SQLQueryAgent] = None
agent_initialized = False

# ✅ 新增：全局查询缓存管理器
from core.cache_manager import QueryCacheManager
query_cache_manager: Optional[QueryCacheManager] = None


# ==================== 生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化 Agent，关闭时清理资源
    """
    # 启动时
    logger.info("🚀 Starting Sight Server...")
    initialize_agent()

    yield

    # 关闭时
    logger.info("🛑 Shutting down Sight Server...")
    if sql_agent is not None:
        try:
            sql_agent.close()
            logger.info("✓ SQL Agent closed")
        except Exception as e:
            logger.error(f"Error closing SQL Agent: {e}")


def initialize_agent() -> bool:
    """
    初始化 SQL Query Agent 和缓存管理器

    Returns:
        bool: 初始化是否成功
    """
    global sql_agent, agent_initialized, query_cache_manager

    if agent_initialized and sql_agent is not None:
        logger.info("Agent already initialized")
        return True

    try:
        # ✅ 初始化查询缓存管理器
        logger.info("Initializing Query Cache Manager...")
        query_cache_manager = QueryCacheManager(
            cache_dir="./cache",
            ttl=3600,  # 1小时
            max_size=1000,
            enable_semantic_search=True,  # ⚠️ 临时禁用语义搜索（torch/torchvision 冲突）
            similarity_threshold=0.92,
            embedding_model="paraphrase-multilingual-MiniLM-L12-v2"
        )
        logger.info("✓ Query Cache Manager initialized successfully")

        # 初始化 SQL Query Agent
        logger.info("Initializing SQL Query Agent...")
        sql_agent = SQLQueryAgent(
            enable_spatial=True
        )
        agent_initialized = True
        logger.info("✓ SQL Query Agent initialized successfully")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to initialize SQL Query Agent: {e}", exc_info=True)
        sql_agent = None
        agent_initialized = False
        return False


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="Sight Server API",
    description="基于 LangChain Agent 的景区数据自然语言查询 API 服务",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==================== CORS 配置 ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# ==================== 异常处理 ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "message": str(exc.detail),
            "status": "error"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "服务器内部错误，请稍后重试",
            "details": str(exc) if settings.DEBUG else None,
            "status": "error"
        }
    )


# ==================== API 端点 ====================

@app.get("/", response_model=HealthResponse, summary="健康检查")
async def root():
    """
    健康检查端点

    返回服务状态和版本信息
    """
    return HealthResponse(
        status="healthy",
        message="Sight Server is running",
        agent_status="initialized" if agent_initialized else "not_initialized",
        database_status="connected" if agent_initialized else "unknown",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse, summary="健康检查（详细）")
async def health_check():
    """
    详细健康检查

    检查 Agent 和数据库连接状态
    """
    # 检查 Agent 状态
    agent_status = "initialized" if agent_initialized and sql_agent else "not_initialized"

    # 检查数据库状态
    database_status = "unknown"
    if sql_agent:
        try:
            # 尝试获取数据库信息
            db_info = sql_agent.db_connector.get_database_info()
            database_status = "connected" if "error" not in db_info else "error"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            database_status = "error"

    return HealthResponse(
        status="healthy" if agent_initialized else "degraded",
        message="All systems operational" if agent_initialized else "Agent not initialized",
        agent_status=agent_status,
        database_status=database_status,
        version="1.0.0"
    )


@app.get("/query", response_model=QueryResponse, summary="自然语言查询 (GET)")
async def query_get(
    q: str = Query(..., description="自然语言查询文本", examples=["查询浙江省的5A景区"]),
    limit: Optional[int] = Query(None, description="结果数量限制", ge=1, le=100),
    include_sql: bool = Query(True, description="是否返回 SQL 语句")  # ✅ 改为默认True
):

    """
    自然语言查询端点 (GET 方法)

    **功能：**
    - 将自然语言查询转换为 SQL 并执行
    - 返回 Agent 的自然语言回答和结构化数据
    - ✅ 支持语义相似度缓存（响应时间 < 0.1s）

    **返回：**
    - answer: Agent 生成的自然语言回答
    - data: 结构化查询结果数组
    - count: 结果数量
    - sql: 执行的 SQL（可选）

    **URL 示例：**
    - GET /query?q=查询浙江省的5A景区
    - GET /query?q=查找距离杭州10公里内的景区&limit=20
    - GET /query?q=统计浙江省有多少个4A景区&include_sql=true
    """
    # 检查 Agent 是否初始化
    if not agent_initialized or sql_agent is None:
        if not initialize_agent():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SQL Query Agent 未初始化，请检查配置"
            )

    try:
        logger.info(f"Processing GET query: {q}")
        start_time = time.time()

        # ✅ 1. 尝试从缓存获取（语义相似度搜索）
        cached_response = None
        if query_cache_manager:
            cache_context = {
                "enable_spatial": True,  # 从 agent 配置获取
                "query_intent": None,    # 第一次查询时未知
                "include_sql": include_sql
            }

            # 使用语义搜索获取缓存
            cached_result = query_cache_manager.get_with_semantic_search(
                q,
                cache_context
            )

            if cached_result:
                # 缓存命中，直接构建响应
                cache_execution_time = time.time() - start_time
                logger.info(f"✓ Cache HIT: {q[:50]}... (time={cache_execution_time:.3f}s)")

                cached_response = QueryResponse(
                    status=QueryStatus(cached_result.get("status", "success")),
                    answer=cached_result.get("answer", ""),
                    data=cached_result.get("data"),
                    count=cached_result.get("count", 0),
                    message=cached_result.get("message", "查询成功（缓存）"),
                    sql=cached_result.get("sql") if include_sql else None,
                    execution_time=round(cache_execution_time, 3),
                    intent_info=cached_result.get("intent_info")
                )
                return cached_response

        # ✅ 2. 缓存未命中，执行 Agent 查询
        logger.info(f"✗ Cache MISS: {q[:50]}... Executing Agent...")
        result_json = sql_agent.run(q)

        # 解析结果
        import json
        result_dict = json.loads(result_json)

        # 计算执行时间
        execution_time = time.time() - start_time

        # 构建响应
        response = QueryResponse(
            status=QueryStatus(result_dict.get("status", "success")),
            answer=result_dict.get("answer", ""),
            data=result_dict.get("data"),
            count=result_dict.get("count", 0),
            message=result_dict.get("message", "查询成功"),
            sql=result_dict.get("sql") if include_sql else None,
            execution_time=round(execution_time, 2),
            intent_info=result_dict.get("intent_info")  # ✅ 添加意图信息
        )

        # ✅ 3. 保存缓存（包含完整的 QueryResponse）
        if query_cache_manager and result_dict.get("status") == "success":
            cache_context["query_intent"] = result_dict.get("intent_info", {}).get("intent_type", "query")

            # 转换 QueryResponse 为字典
            cache_data = {
                "status": response.status.value,
                "answer": response.answer,
                "data": response.data,
                "count": response.count,
                "message": response.message,
                "sql": response.sql,
                "intent_info": response.intent_info
            }

            cache_key = query_cache_manager.get_cache_key(q, cache_context)
            if query_cache_manager.set(cache_key, cache_data, q):
                logger.info(f"✓ Cache SAVED: {q[:50]}...")

        logger.info(f"GET query completed in {execution_time:.2f}s, count={response.count}")
        return response

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Agent output: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent 输出格式错误"
        )
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询执行失败: {str(e)}"
        )


@app.post("/query", response_model=QueryResponse, summary="自然语言查询 (POST)")
async def query_post(request: QueryRequest):
    """
    自然语言查询端点 (POST 方法)

    **功能：**
    - 将自然语言查询转换为 SQL 并执行
    - 返回 Agent 的自然语言回答和结构化数据
    - ✅ 支持语义相似度缓存（响应时间 < 0.1s）

    **返回：**
    - answer: Agent 生成的自然语言回答
    - data: 结构化查询结果数组
    - count: 结果数量
    - sql: 执行的 SQL（可选）

    **示例查询：**
    - "查询浙江省的5A景区"
    - "查找距离杭州10公里内的景区"
    - "统计浙江省有多少个4A景区"
    """
    # 检查 Agent 是否初始化
    if not agent_initialized or sql_agent is None:
        if not initialize_agent():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SQL Query Agent 未初始化，请检查配置"
            )

    try:
        logger.info(f"Processing POST query: {request.query}")
        start_time = time.time()

        # ✅ 1. 尝试从缓存获取（语义相似度搜索）
        cached_response = None
        if query_cache_manager:
            cache_context = {
                "enable_spatial": True,  # 从 agent 配置获取
                "query_intent": None,    # 第一次查询时未知
                "include_sql": request.include_sql
            }

            # 使用语义搜索获取缓存
            cached_result = query_cache_manager.get_with_semantic_search(
                request.query,
                cache_context
            )

            if cached_result:
                # 缓存命中，直接构建响应
                cache_execution_time = time.time() - start_time
                logger.info(f"✓ Cache HIT: {request.query[:50]}... (time={cache_execution_time:.3f}s)")

                cached_response = QueryResponse(
                    status=QueryStatus(cached_result.get("status", "success")),
                    answer=cached_result.get("answer", ""),
                    data=cached_result.get("data"),
                    count=cached_result.get("count", 0),
                    message=cached_result.get("message", "查询成功（缓存）"),
                    sql=cached_result.get("sql") if request.include_sql else None,
                    execution_time=round(cache_execution_time, 3),
                    intent_info=cached_result.get("intent_info")
                )
                return cached_response

        # ✅ 2. 缓存未命中，执行 Agent 查询
        logger.info(f"✗ Cache MISS: {request.query[:50]}... Executing Agent...")
        result_json = sql_agent.run(request.query)

        # 解析结果
        import json
        result_dict = json.loads(result_json)

        # 计算执行时间
        execution_time = time.time() - start_time

        # 构建响应
        response = QueryResponse(
            status=QueryStatus(result_dict.get("status", "success")),
            answer=result_dict.get("answer", ""),
            data=result_dict.get("data"),
            count=result_dict.get("count", 0),
            message=result_dict.get("message", "查询成功"),
            sql=result_dict.get("sql") if request.include_sql else None,
            execution_time=round(execution_time, 2),
            intent_info=result_dict.get("intent_info")  # ✅ 添加意图信息
        )

        # ✅ 3. 保存缓存（包含完整的 QueryResponse）
        if query_cache_manager and result_dict.get("status") == "success":
            cache_context["query_intent"] = result_dict.get("intent_info", {}).get("intent_type", "query")

            # 转换 QueryResponse 为字典
            cache_data = {
                "status": response.status.value,
                "answer": response.answer,
                "data": response.data,
                "count": response.count,
                "message": response.message,
                "sql": response.sql,
                "intent_info": response.intent_info
            }

            cache_key = query_cache_manager.get_cache_key(request.query, cache_context)
            if query_cache_manager.set(cache_key, cache_data, request.query):
                logger.info(f"✓ Cache SAVED: {request.query[:50]}...")

        logger.info(f"POST query completed in {execution_time:.2f}s, count={response.count}")
        return response

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Agent output: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent 输出格式错误"
        )
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询执行失败: {str(e)}"
        )


@app.post("/query/geojson", response_model=GeoJSONResponse, summary="GeoJSON 查询")
async def query_geojson(request: GeoJSONRequest):
    """
    GeoJSON 查询端点

    **功能：**
    - 将自然语言查询转换为 SQL 并执行
    - 返回 GeoJSON FeatureCollection 格式

    **用途：**
    - 地图可视化（OpenLayers, Leaflet, Mapbox）
    - 空间分析

    **坐标系支持：**
    - wgs84: WGS-84 (EPSG:4326) - GPS 标准，国际通用
    - gcj02: GCJ-02 - 国测局火星坐标系，高德/腾讯地图
    - bd09: BD-09 - 百度坐标系，百度地图

    **示例查询：**
    - "查询浙江省的5A景区"
    - "查找杭州市所有景区"
    """
    # 检查 Agent 是否初始化
    if not agent_initialized or sql_agent is None:
        if not initialize_agent():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SQL Query Agent 未初始化"
            )

    try:
        logger.info(f"Processing GeoJSON query: {request.query}")
        start_time = time.time()

        # 执行查询
        result_json = sql_agent.run(request.query)

        # 解析结果
        import json
        result_dict = json.loads(result_json)

        # 检查查询状态
        if result_dict.get("status") != "success" or not result_dict.get("data"):
            logger.warning(f"Query returned no data or error: {result_dict.get('message')}")
            return GeoJSONResponse(
                type="FeatureCollection",
                features=[],
                metadata={
                    "count": 0,
                    "coordinate_system": request.coordinate_system.value,
                    "message": result_dict.get("message", "查询无结果"),
                    "execution_time": round(time.time() - start_time, 2)
                }
            )

        # 转换为 GeoJSON
        try:
            # 映射坐标系枚举
            coord_system_map = {
                "wgs84": CoordinateSystem.WGS84,
                "gcj02": CoordinateSystem.GCJ02,
                "bd09": CoordinateSystem.BD09
            }
            target_system = coord_system_map.get(
                request.coordinate_system.value,
                CoordinateSystem.WGS84
            )

            # 使用 GeoJSONConverter 转换
            geojson_data = GeoJSONConverter.from_query_result_auto(
                data=result_dict["data"],
                target_system=target_system,
                include_properties=request.include_properties
            )

            # 添加执行时间到元数据
            geojson_data["metadata"]["execution_time"] = round(time.time() - start_time, 2)
            geojson_data["metadata"]["query"] = request.query
            geojson_data["metadata"]["limit"] = request.limit

            logger.info(
                f"GeoJSON query completed in {geojson_data['metadata']['execution_time']:.2f}s, "
                f"features={geojson_data['metadata']['count']}"
            )

            return GeoJSONResponse(
                type=geojson_data["type"],
                features=geojson_data["features"],
                metadata=geojson_data["metadata"]
            )

        except Exception as convert_error:
            logger.error(f"GeoJSON conversion failed: {convert_error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"GeoJSON 转换失败: {str(convert_error)}"
            )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Agent output: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent 输出格式错误"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GeoJSON query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GeoJSON 查询失败: {str(e)}"
        )


@app.post("/query/thought-chain", response_model=ThoughtChainResponse, summary="思维链查询")
async def query_thought_chain(request: ThoughtChainRequest):
    """
    思维链查询端点

    **功能：**
    - 执行自然语言查询并返回完整的 Agent 推理过程
    - 展示 Agent 的思考步骤、执行的 SQL 查询和中间结果
    - 用于调试、学习和理解 Agent 的决策过程

    **用途：**
    - 调试查询问题
    - 理解 Agent 如何处理复杂查询
    - 优化提示词和查询策略
    - 教学演示

    **返回内容：**
    - final_answer: 最终答案
    - thought_chain: 完整的思维链步骤
    - sql_queries: 所有执行的 SQL 查询及其结果
    - step_count: 总步骤数

    **示例查询：**
    - "统计浙江省有多少个4A景区"
    - "查找杭州市评分最高的景区"
    """
    # 检查 Agent 是否初始化
    if not agent_initialized or sql_agent is None:
        if not initialize_agent():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SQL Query Agent 未初始化"
            )

    try:
        logger.info(f"Processing thought chain query: {request.query}")
        start_time = time.time()

        # 执行带思维链的查询
        result = sql_agent.run_with_thought_chain(request.query)

        # 计算执行时间
        execution_time = time.time() - start_time

        # 检查结果状态
        query_status = QueryStatus.SUCCESS if result.get("status") == "success" else QueryStatus.ERROR

        # 构建响应
        response = ThoughtChainResponse(
            status=query_status,
            final_answer=result.get("final_answer", ""),
            thought_chain=result.get("thought_chain", []) if request.verbose else [],
            step_count=result.get("step_count", 0),
            sql_queries=result.get("sql_queries_with_results", [])
        )

        logger.info(
            f"Thought chain query completed in {execution_time:.2f}s, "
            f"steps={response.step_count}, status={response.status}"
        )

        return response

    except Exception as e:
        logger.error(f"Thought chain query failed: {e}", exc_info=True)

        # 返回错误响应
        return ThoughtChainResponse(
            status=QueryStatus.ERROR,
            final_answer="",
            thought_chain=[],
            step_count=0,
            sql_queries=[]
        )


@app.get("/tables", summary="获取数据表列表")
async def get_tables():
    """
    获取数据库表列表

    返回数据库中所有可用的表名
    """
    if not agent_initialized or sql_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SQL Query Agent 未初始化"
        )

    try:
        tables = sql_agent.db_connector.get_usable_table_names()
        spatial_tables = sql_agent.db_connector.get_spatial_tables()

        return {
            "status": "success",
            "tables": tables,
            "count": len(tables),
            "spatial_tables": [t["table_name"] for t in spatial_tables],
            "spatial_count": len(spatial_tables)
        }

    except Exception as e:
        logger.error(f"Failed to get tables: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取表列表失败: {str(e)}"
        )


@app.get("/database/info", summary="获取数据库信息")
async def get_database_info():
    """
    获取数据库详细信息

    包括 PostgreSQL 版本、PostGIS 版本、表数量等
    """
    if not agent_initialized or sql_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SQL Query Agent 未初始化"
        )

    try:
        db_info = sql_agent.db_connector.get_database_info()
        return {
            "status": "success",
            **db_info
        }

    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据库信息失败: {str(e)}"
        )


@app.get("/cache/stats", summary="获取缓存统计信息")
async def get_cache_stats():
    """
    获取查询缓存统计信息

    返回缓存命中率、缓存条目数、语义搜索统计等
    """
    if not query_cache_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="查询缓存管理器未初始化"
        )

    try:
        stats = query_cache_manager.get_cache_stats()
        
        # 添加语义搜索统计（如果可用）
        if hasattr(query_cache_manager, 'enable_semantic_search') and query_cache_manager.enable_semantic_search:
            stats["semantic_search_enabled"] = True
            stats["similarity_threshold"] = query_cache_manager.similarity_threshold
            stats["embedding_model"] = query_cache_manager.embedding_model
        else:
            stats["semantic_search_enabled"] = False

        # 添加语义命中统计
        if "semantic_hits" in query_cache_manager.metadata:
            stats["semantic_hits"] = query_cache_manager.metadata["semantic_hits"]

        return {
            "status": "success",
            "cache_stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取缓存统计失败: {str(e)}"
        )


@app.delete("/cache/clear", summary="清除所有缓存")
async def clear_cache():
    """
    清除所有查询缓存

    强制清除所有缓存条目，用于测试或调试
    """
    if not query_cache_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="查询缓存管理器未初始化"
        )

    try:
        cleared_count = query_cache_manager.clear_all()
        
        return {
            "status": "success",
            "message": f"成功清除 {cleared_count} 个缓存条目",
            "cleared_count": cleared_count
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清除缓存失败: {str(e)}"
        )


# ==================== 启动服务器 ====================

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.SERVER_HOST}:{settings.SERVER_PORT}")

    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.SERVER_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
