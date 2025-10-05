"""
API数据模型 - Sight Server
定义FastAPI使用的请求和响应Pydantic模型
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


# ==================== 枚举类型 ====================

class ReturnFormat(str, Enum):
    """返回格式枚举"""
    JSON = "json"           # 标准JSON格式
    GEOJSON = "geojson"     # GeoJSON FeatureCollection格式
    STRUCTURED = "structured"  # 结构化Pydantic对象


class CoordinateSystem(str, Enum):
    """坐标系枚举"""
    WGS84 = "wgs84"     # WGS-84 (EPSG:4326) - GPS标准
    GCJ02 = "gcj02"     # GCJ-02 - 国测局火星坐标系
    BD09 = "bd09"       # BD-09 - 百度坐标系


class QueryStatus(str, Enum):
    """查询状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


# ==================== 请求模型 ====================

class QueryRequest(BaseModel):
    """
    标准查询请求模型
    """
    query: str = Field(
        default=...,
        description="自然语言查询文本",
        min_length=1,
        max_length=500,
        examples=["查询浙江省的5A景区"]
    )
    limit: Optional[int] = Field(
        default=10,
        description="返回结果数量限制",
        ge=1,
        le=100
    )
    return_format: ReturnFormat = Field(
        default=ReturnFormat.JSON,
        description="返回数据格式"
    )
    include_sql: bool = Field(
        default=False,
        description="是否在响应中包含执行的SQL语句"
    )

    @validator('query')
    def validate_query(cls, v):
        """验证查询文本"""
        v = v.strip()
        if not v:
            raise ValueError('查询文本不能为空')

        # 检查危险关键词
        dangerous_patterns = [
            'drop table', 'delete from', 'truncate',
            'alter table', 'create table', 'exec',
            'execute', 'xp_', 'sp_'
        ]
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f'查询包含潜在危险关键词: {pattern}')

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "query": "查询杭州市的5A景区",
                "limit": 10,
                "return_format": "json",
                "include_sql": False
            }
        }


class GeoJSONRequest(BaseModel):
    """
    GeoJSON查询请求模型
    """
    query: str = Field(
        default=...,
        description="自然语言查询文本",
        min_length=1,
        max_length=500
    )
    coordinate_system: CoordinateSystem = Field(
        default=CoordinateSystem.WGS84,
        description="坐标系统类型"
    )
    limit: Optional[int] = Field(
        default=100,
        description="返回结果数量限制",
        ge=1,
        le=1000
    )
    include_properties: bool = Field(
        default=True,
        description="是否包含属性信息"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "查找距离杭州10公里内的景区",
                "coordinate_system": "wgs84",
                "limit": 100,
                "include_properties": True
            }
        }


class ThoughtChainRequest(BaseModel):
    """
    思维链查询请求模型
    """
    query: str = Field(
        default=...,
        description="自然语言查询文本",
        min_length=1,
        max_length=500
    )
    verbose: bool = Field(
        default=True,
        description="是否返回详细的思维链步骤"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "统计浙江省有多少个4A景区",
                "verbose": True
            }
        }


# ==================== 响应模型 ====================

class QueryResponse(BaseModel):
    """
    标准查询响应模型（增强版）

    包含 Agent 的自然语言回答、深度分析和结构化数据
    """
    status: QueryStatus = Field(
        description="查询状态"
    )
    answer: str = Field(
        default="",
        description="Agent 生成的自然语言回答"
    )
    data: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="查询结果的结构化数据（summary类型时可能为None）"
    )
    count: int = Field(
        default=0,
        description="结果数量"
    )
    message: str = Field(
        default="",
        description="响应消息"
    )
    sql: Optional[str] = Field(
        default=None,
        description="执行的SQL语句（可选）"
    )
    execution_time: Optional[float] = Field(
        default=None,
        description="查询执行时间（秒）"
    )
    intent_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="查询意图分析信息，包含 intent_type, is_spatial, keywords_matched 等"
    )
    # ✅ 新增：深度分析字段
    analysis: Optional[str] = Field(
        default=None,
        description="深度分析内容（2-4段文字）"
    )
    insights: Optional[List[str]] = Field(
        default=None,
        description="关键洞察列表（3-5条重要发现）"
    )
    suggestions: Optional[List[str]] = Field(
        default=None,
        description="相关建议列表（可选，基于数据提供的实用建议）"
    )
    analysis_type: Optional[str] = Field(
        default=None,
        description="分析类型（statistical/spatial/trend/general）"
    )
    # ✅ 新增：验证信息
    validation_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="验证信息（包含验证状态和重试次数）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "answer": "武汉市共有56个景区，主要分布在武昌区、洪山区等中心城区",
                "data": [
                    {
                        "district": "武昌区",
                        "count": 15,
                        "percentage": 26.8
                    }
                ],
                "count": 7,
                "message": "查询成功",
                "sql": "SELECT json_agg(...) FROM a_sight WHERE ...",
                "execution_time": 1.23,
                "intent_info": {
                    "intent_type": "summary",
                    "is_spatial": False,
                    "confidence": 0.70
                },
                "analysis": "根据查询结果，武汉市景区空间分布呈现以下特征：\\n\\n1. **区域分布不均**：武昌区景区数量最多（15个），占比26.8%，其次是洪山区（12个），说明中心城区的旅游资源更为集中。\\n\\n2. **空间聚集特征**：主要景区集中在东部区域（经度114.3-114.4°），可能与长江沿线和东湖风景区有关。\\n\\n3. **发展潜力**：西部地区景区较少，可考虑开发新的旅游资源以平衡区域发展。",
                "insights": [
                    "武昌区景区数量最多，占全市的26.8%",
                    "景区主要集中在东部区域（经度114.3-114.4°）",
                    "西部地区景区仅占15%，存在较大的开发空间"
                ],
                "suggestions": [
                    "可以考虑在西部地区开发新的旅游资源",
                    "加强中心城区景区的服务质量和基础设施建设"
                ],
                "analysis_type": "spatial",
                "validation_info": {
                    "validated": True,
                    "retry_count": 0,
                    "validation_message": "结果符合用户需求"
                }
            }
        }


class GeoJSONResponse(BaseModel):
    """
    GeoJSON响应模型
    """
    type: str = Field(
        default="FeatureCollection",
        description="GeoJSON类型"
    )
    features: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="要素集合"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元数据信息"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [120.15, 30.25]
                        },
                        "properties": {
                            "name": "西湖",
                            "level": "5A"
                        }
                    }
                ],
                "metadata": {
                    "count": 1,
                    "coordinate_system": "wgs84"
                }
            }
        }


class ThoughtChainResponse(BaseModel):
    """
    思维链查询响应模型
    """
    status: QueryStatus = Field(
        description="查询状态"
    )
    final_answer: str = Field(
        default="",
        description="最终答案"
    )
    thought_chain: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="思维链步骤"
    )
    step_count: int = Field(
        default=0,
        description="思维链步骤数"
    )
    sql_queries: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="SQL查询列表"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "final_answer": "浙江省共有18个4A景区",
                "thought_chain": [
                    {
                        "step": 1,
                        "type": "action",
                        "action": "sql_db_query"
                    }
                ],
                "step_count": 3,
                "sql_queries": [
                    {
                        "sql": "SELECT COUNT(*) FROM a_sight WHERE ...",
                        "result": "18"
                    }
                ]
            }
        }


class HealthResponse(BaseModel):
    """
    健康检查响应模型
    """
    status: str = Field(
        description="服务状态"
    )
    message: str = Field(
        description="状态消息"
    )
    agent_status: str = Field(
        description="Agent状态"
    )
    database_status: str = Field(
        default="unknown",
        description="数据库状态"
    )
    version: str = Field(
        default="1.0.0",
        description="API版本"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "Sight Server is running",
                "agent_status": "initialized",
                "database_status": "connected",
                "version": "1.0.0"
            }
        }


class ErrorResponse(BaseModel):
    """
    错误响应模型
    """
    error: str = Field(
        description="错误类型"
    )
    message: str = Field(
        description="错误消息"
    )
    details: Optional[str] = Field(
        default=None,
        description="详细错误信息"
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="错误时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "查询文本不能为空",
                "details": "Field required: query",
                "timestamp": "2025-10-04T12:34:56"
            }
        }


# ==================== 数据库信息模型 ====================

class TableInfo(BaseModel):
    """
    数据表信息模型
    """
    name: str = Field(
        description="表名"
    )
    schema: str = Field(
        default="public",
        description="模式名"
    )
    type: str = Field(
        description="表类型（table/view）"
    )
    row_count: Optional[int] = Field(
        default=None,
        description="记录数（估算）"
    )
    has_geometry: bool = Field(
        default=False,
        description="是否包含几何列"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "a_sight",
                "schema": "public",
                "type": "table",
                "row_count": 1500,
                "has_geometry": True
            }
        }


class DatabaseInfoResponse(BaseModel):
    """
    数据库信息响应模型
    """
    database_name: str = Field(
        description="数据库名称"
    )
    tables: List[TableInfo] = Field(
        default_factory=list,
        description="数据表列表"
    )
    spatial_tables_count: int = Field(
        default=0,
        description="空间表数量"
    )
    postgis_version: Optional[str] = Field(
        default=None,
        description="PostGIS版本"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "database_name": "scenic_db",
                "tables": [
                    {
                        "name": "a_sight",
                        "schema": "public",
                        "type": "table",
                        "has_geometry": True
                    }
                ],
                "spatial_tables_count": 1,
                "postgis_version": "3.3.2"
            }
        }


# 测试代码
if __name__ == "__main__":
    # 测试模型创建
    print("=== 测试API模型 ===\n")

    # 测试1: QueryRequest
    print("--- 测试1: QueryRequest ---")
    request = QueryRequest(
        query="查询浙江省的5A景区",
        limit=10
    )
    print(request.model_dump_json(indent=2))

    # 测试2: QueryResponse
    print("\n--- 测试2: QueryResponse ---")
    response = QueryResponse(
        status=QueryStatus.SUCCESS,
        data=[{"name": "西湖", "level": "5A"}],
        count=1,
        message="查询成功"
    )
    print(response.model_dump_json(indent=2))

    # 测试3: GeoJSONRequest
    print("\n--- 测试3: GeoJSONRequest ---")
    geo_request = GeoJSONRequest(
        query="查找距离杭州10公里内的景区",
        coordinate_system=CoordinateSystem.WGS84
    )
    print(geo_request.model_dump_json(indent=2))
