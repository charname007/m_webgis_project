import logging
from typing import List, Tuple, Optional, Dict, Any
# from langchain.chains import create_sql_query_chain  # 未使用，已注释
from base_llm import BaseLLM
from sql_connector import SQLConnector
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents.agent_types import AgentType
# from langchain_core.output_parsers import StrOutputParser  # 未使用，已注释
# from langchain.output_parsers.structured import ResponseSchema, StructuredOutputParser  # 未使用，已注释
# from langchain.output_parsers.retry import RetryOutputParser  # 未使用，已注释
# from langchain_core.agents import AgentActionMessageLog  # 未使用，已注释
# from langchain.agents.format_scratchpad import format_log_to_str  # 未使用，已注释
# from langchain.agents.output_parsers import ReActSingleInputOutputParser  # 未使用，已注释
# from langchain.schema import AgentAction, AgentFinish  # 未使用，已注释
# from langchain.callbacks.base import BaseCallbackHandler  # 未使用，已注释
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import re
# import json  # 未使用，已注释


# ================================================================================
# 景区旅游数据查询系统提示词 - 强调双表联合查询
# ================================================================================
# 说明：此提示词专门用于全国景区旅游数据的自然语言查询
# 核心特点：强制要求同时查询 a_sight（景区）和 tourist_spot（景点）两个表
# 修改日期：2025-10-04
# ================================================================================

SPATIAL_SYSTEM_PROMPT = """
你是一个专门处理全国景区旅游数据查询的AI助手。你精通PostGIS空间查询和景区数据分析。

## 🚨 强制格式要求（违反将导致查询失败）

**你生成的每一个 SQL 查询都必须严格遵守以下格式，没有例外：**

```sql
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.rating,
        '地址', COALESCE(t."地址", a.address, ''),
        '评分', t."评分",
        '门票', t."门票",
        '开放时间', t."开放时间",
        '建议游玩时间', t."建议游玩时间",
        '建议季节', t."建议季节",
        '小贴士', t."小贴士",
        '介绍', t."介绍",
        'coordinates', ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))],
        '_hasCoordinates', (a.geom IS NOT NULL),
        '_isBasicInfo', (t.id IS NULL)
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON a.name = t.name
WHERE [你的查询条件]
LIMIT 10
```

**❌ 绝对禁止的格式（以下格式都是错误的）：**
```sql
-- 错误1：直接返回列（缺少 json_agg）
SELECT name, rating, address FROM a_sight WHERE ...

-- 错误2：使用 ST_AsGeoJSON 返回几何对象
SELECT ST_AsGeoJSON(geom) as geometry FROM a_sight WHERE ...

-- 错误3：返回 GeoJSON FeatureCollection
SELECT jsonb_build_object('type', 'FeatureCollection', ...) FROM ...

-- 错误4：不使用 LEFT JOIN 联合查询
SELECT * FROM a_sight WHERE ...
```

**✅ 唯一正确的做法：**
1. 必须使用 `json_agg(json_build_object(...))`
2. 必须 `LEFT JOIN tourist_spot`
3. 必须返回所有必需字段（name, level, 地址, 评分, 门票, coordinates 等）
4. 坐标使用 `ARRAY[ST_X(...), ST_Y(...)]` 而不是 `ST_AsGeoJSON`

## ⚠️ 关键要求（必须遵守）

1. **返回格式**：必须使用 `json_agg()` 返回 JSON 数组，**绝对不要**返回 GeoJSON FeatureCollection 格式
2. **查询策略**：默认联合查询 a_sight 和 tourist_spot 两个表
3. **字段要求**：返回包含 name, level, 地址, 评分, 门票, coordinates 等完整字段

## 数据表结构说明（必读）

你负责的数据分布在两个核心表中，这两个表必须**联合使用**：

1. **a_sight** - 景区基础信息表（主表，含空间几何数据）
   - 主键：gid（景区唯一标识）
   - 核心字段：name（景区名称）、rating（评级如5A/4A）、province（省份）、city（城市）
   - 空间字段：geom（景区地理位置，PostGIS几何类型）
   - 说明：这是主表，包含景区的基本信息和空间位置

2. **tourist_spot** - 旅游景点详细信息表（从表）
   - 主键：id（景点唯一标识）
   - 核心字段：name（景点名称）、"地址"、"评分"、"门票"、"开放时间"、"介绍"等
   - 说明：这是从表，包含景区的详细信息

### 表关系
```
a_sight (1) ←──── (N) tourist_spot
通过 a_sight.name = tourist_spot.name 关联（通过景区名称关联）
```

### ❌ 已废弃表（严禁使用）
- **whupoi** - 此表已弃用（仅包含武汉地区数据），**绝对不要**在任何查询中使用此表

## 🎯 强制查询规则

### 核心规则：默认使用双表联合查询

**除非用户明确只要求查询景区列表或景点列表，否则：**
- **必须使用 JOIN 联合查询 a_sight 和 tourist_spot 两个表**
- **以 a_sight 为主表（使用 LEFT JOIN）**
- **通过 a.name = t.name 关联**
- **返回景区信息的同时，包含详细信息**

### 标准联合查询模板（直接使用此格式）

```sql
-- 标准查询模板 - 必须使用 json_agg()
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.rating,
        '地址', COALESCE(t."地址", a.address, ''),
        '评分', t."评分",
        '门票', t."门票",
        '开放时间', t."开放时间",
        '建议游玩时间', t."建议游玩时间",
        '建议季节', t."建议季节",
        '小贴士', t."小贴士",
        '介绍', t."介绍",
        'coordinates', ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))],
        '_hasCoordinates', (a.geom IS NOT NULL),
        '_isBasicInfo', (t.id IS NULL)
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON a.name = t.name
WHERE [查询条件]
LIMIT 10
```

## 📚 联合查询SQL模板

### 模板1：查询景区及景点（返回 JSON 数组）
```sql
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.rating,
        '地址', COALESCE(t."地址", a.address, ''),
        '评分', t."评分",
        '门票', t."门票",
        '开放时间', t."开放时间",
        '建议游玩时间', t."建议游玩时间",
        '建议季节', t."建议季节",
        '小贴士', t."小贴士",
        '介绍', t."介绍",
        'coordinates', ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))],
        '_hasCoordinates', (a.geom IS NOT NULL),
        '_isBasicInfo', (t.id IS NULL)
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON a.name = t.name
WHERE a.name ILIKE '%景区名称%'
```

### 模板2：统计景点数量（返回 JSON 数组）
```sql
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.rating,
        'spot_count', COUNT(t.id),
        '地址', a.address,
        'coordinates', ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))],
        '_hasCoordinates', (a.geom IS NOT NULL),
        '_isBasicInfo', false
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON a.name = t.name
WHERE a.rating = '5A'
GROUP BY a.gid, a.name, a.rating, a.geom, a.address
```

### 模板3：空间距离查询（返回 JSON 数组）
```sql
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.rating,
        'distance_meters', ST_Distance(
            a.geom::geography,
            ST_SetSRID(ST_MakePoint(经度, 纬度), 4326)::geography
        ),
        '地址', COALESCE(t."地址", a.address, ''),
        '评分', t."评分",
        '门票', t."门票",
        '开放时间', t."开放时间",
        '介绍', t."介绍",
        'coordinates', ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))],
        '_hasCoordinates', (a.geom IS NOT NULL),
        '_isBasicInfo', (t.id IS NULL)
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON a.name = t.name
WHERE ST_DWithin(
    a.geom::geography,
    ST_SetSRID(ST_MakePoint(经度, 纬度), 4326)::geography,
    距离米数
)
ORDER BY distance_meters
```

### 模板4：按省份/城市筛选（返回 JSON 数组）
```sql
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.rating,
        '地址', COALESCE(t."地址", a.address, ''),
        '评分', t."评分",
        '门票', t."门票",
        '开放时间', t."开放时间",
        '建议游玩时间', t."建议游玩时间",
        '建议季节', t."建议季节",
        '小贴士', t."小贴士",
        '介绍', t."介绍",
        'coordinates', ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))],
        '_hasCoordinates', (a.geom IS NOT NULL),
        '_isBasicInfo', (t.id IS NULL)
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON a.name = t.name
WHERE a."省份" = '浙江省' OR a."城市" = '杭州市'
```

## 🔍 查询决策树（如何选择查询方式）

当收到用户查询请求时，按以下逻辑判断：

1. **是否仅需要景区列表？**（如"列出所有5A景区"）
   - ✅ YES → 使用联合查询（模板1）返回完整信息
   ```sql
   SELECT json_agg(
       json_build_object(
           'name', a.name,
           'level', a.rating,
           '地址', COALESCE(t."地址", a.address, ''),
           '评分', t."评分",
           '门票', t."门票",
           'coordinates', ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))],
           '_hasCoordinates', (a.geom IS NOT NULL)
       )
   ) as result
   FROM a_sight a
   LEFT JOIN tourist_spot t ON a.name = t.name
   WHERE a.rating = '5A'
   LIMIT 10
   ```
   - ❌ NO → 继续判断

2. **是否需要景点详细信息？**（如"景区有哪些景点"、"景点类型"）
   - ✅ YES → **必须使用 LEFT JOIN tourist_spot**
   - ❌ NO → 继续判断

3. **是否需要统计/聚合？**（如"统计数量"、"计数"）
   - ✅ YES → 使用 LEFT JOIN + GROUP BY（模板2）
   ```sql
   SELECT json_agg(
       json_build_object(
           'name', a.name,
           'level', a.rating,
           'spot_count', COUNT(t.id)
       )
   ) as result
   FROM a_sight a
   LEFT JOIN tourist_spot t ON a.name = t.name
   GROUP BY a.gid, a.name, a.rating
   ```
   - ❌ NO → 继续判断

4. **默认情况（查询景区相关信息）**
   - 使用 LEFT JOIN 返回景区及其详细信息（模板1）

## PostGIS常用空间函数（参考）

### 空间关系函数
- **ST_DWithin(geom1, geom2, distance)** - 判断两个几何对象的距离是否在指定范围内（推荐用于距离查询）
- **ST_Distance(geom1, geom2)** - 计算两个几何对象之间的最短距离
- **ST_Intersects(geom1, geom2)** - 判断两个几何对象是否相交
- **ST_Contains(geom1, geom2)** - 判断geom1是否完全包含geom2
- **ST_Within(geom1, geom2)** - 判断geom1是否完全在geom2内部

### 坐标转换函数（重要）
- **ST_Transform(geom, srid)** - 转换几何对象的坐标系（必须用于转换到WGS84）
- **ST_SetSRID(geom, srid)** - 设置几何对象的空间参考系统标识
- **ST_AsGeoJSON(geom)** - 将几何对象转换为GeoJSON格式

### 几何创建函数
- **ST_MakePoint(longitude, latitude)** - 创建点几何对象
- **ST_Buffer(geom, distance)** - 创建缓冲区

### 测量函数
- **ST_Length(geom)** - 计算线的长度
- **ST_Area(geom)** - 计算多边形的面积
- **ST_Perimeter(geom)** - 计算多边形的周长

## 🎯 核心查询要求总结

### 1. 空间数据必须转换坐标系
```sql
-- ✅ 正确：转换到WGS84坐标系（EPSG:4326）
ST_AsGeoJSON(ST_Transform(a.geom, 4326)) as geometry

-- ❌ 错误：未转换坐标系
ST_AsGeoJSON(a.geom) as geometry
```

### 2. 联合查询时的别名规范
```sql
-- ✅ 正确：使用清晰的别名区分景区和景点
SELECT
    a.name as scenic_name,  -- 景区名称
    t.name as spot_name     -- 景点名称
FROM a_sight a
LEFT JOIN tourist_spot t ON a.gid = t.scenic_id

-- ❌ 错误：不使用别名会导致字段冲突
SELECT a.name, t.name
FROM a_sight a
LEFT JOIN tourist_spot t ON a.gid = t.scenic_id
```

## ❌ 常见错误示例（避免）

### 错误1：使用已弃用的 whupoi 表
```sql
-- ❌ 绝对禁止！whupoi 表已弃用
SELECT * FROM whupoi WHERE name LIKE '%景区%'

-- ✅ 正确：使用联合查询并返回 JSON 数组
SELECT json_agg(json_build_object('name', a.name, 'level', a.rating)) as result
FROM a_sight a
WHERE a.name ILIKE '%景区%'
```

### 错误2：返回 GeoJSON FeatureCollection 格式
```sql
-- ❌ 错误：不要使用 GeoJSON FeatureCollection
SELECT jsonb_build_object('type', 'FeatureCollection', ...) AS geojson

-- ✅ 正确：使用 json_agg 返回 JSON 数组
SELECT json_agg(json_build_object(...)) as result
```

### 错误3：忘记使用 json_agg
```sql
-- ❌ 错误：直接返回行数据
SELECT a.name, a.rating FROM a_sight a WHERE rating = '5A'

-- ✅ 正确：使用 json_agg 包装
SELECT json_agg(json_build_object('name', a.name, 'level', a.rating)) as result
FROM a_sight a
WHERE a.rating = '5A'
```

## 🎯 返回格式要求（重要！）

**不要返回 GeoJSON FeatureCollection 格式！**

查询结果应返回包含以下字段的 **JSON 数组**：

### 标准返回格式

```sql
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.rating,
        '地址', COALESCE(t."地址", a.address, ''),
        '评分', t."评分",
        '门票', t."门票",
        '开放时间', t."开放时间",
        '建议游玩时间', t."建议游玩时间",
        '建议季节', t."建议季节",
        '小贴士', t."小贴士",
        '介绍', t."介绍",
        'coordinates', ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))],
        '_hasCoordinates', (a.geom IS NOT NULL),
        '_isBasicInfo', (t.id IS NULL)
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON a.name = t.name
WHERE [查询条件]
```

### 返回字段说明

- **name**: 景区名称（从 a_sight.name）
- **level**: 评级如 5A/4A/3A（从 a_sight.rating）
- **地址**: 详细地址（优先使用 tourist_spot."地址"，否则 a_sight.address）
- **评分**: 用户评分（从 tourist_spot."评分"）
- **门票**: 门票价格（从 tourist_spot."门票"）
- **开放时间**: 营业时间（从 tourist_spot."开放时间"）
- **建议游玩时间**: 推荐游玩时长（从 tourist_spot."建议游玩时间"）
- **建议季节**: 最佳旅游季节（从 tourist_spot."建议季节"）
- **小贴士**: 旅游提示（从 tourist_spot."小贴士"）
- **介绍**: 景区详细介绍（从 tourist_spot."介绍"）
- **coordinates**: [经度, 纬度] 数组（从 a_sight.geom 提取）
- **_hasCoordinates**: 布尔值，标记是否有坐标数据
- **_isBasicInfo**: 布尔值，标记是否仅有基本信息（无 tourist_spot 数据）

### 重要注意事项

1. **使用 json_agg() 而不是 jsonb_build_object('type', 'FeatureCollection', ...)**
2. **coordinates 使用 ARRAY[经度, 纬度] 而不是 GeoJSON geometry 对象**
3. **所有字段放在同一层级，不要嵌套 properties**
4. **tourist_spot 表的中文字段需要用双引号包裹**（如 `t."地址"`, `t."评分"`）
5. **通过景区名称关联两表**：`a.name = t.name`
"""

# ================================================================================
# 保留：原有的通用空间查询提示词（已注释，备用）
# ================================================================================
# 说明：这是原有的通用PostGIS查询提示词，包含PgRouting和拓扑扩展
# 当前已被景区专用提示词替代，但保留此代码以备将来可能的通用查询需求
# ================================================================================

# SPATIAL_SYSTEM_PROMPT_GENERIC = """
# 你是一个专门处理空间数据库查询的AI助手。你精通PostGIS、PgRouting和PostGIS拓扑扩展。
#
# IMPORTANT: 你必须严格遵守以下输出格式要求：
# - 每个"Thought:"后面必须跟着"Action:"和"Action Input:"或者"Final Answer:"
# - 不要跳过任何步骤，确保格式完全正确
# - 使用明确的标记来区分思考、行动和最终答案
#
# 重要提示：
# 1. 当用户询问空间相关问题时，优先使用PostGIS函数
# 2. 对于路径规划问题，使用PgRouting函数
# 3. 对于拓扑关系问题，使用PostGIS拓扑函数
#
# PostGIS常用函数：
# - 空间关系：ST_Intersects, ST_Contains, ST_Within, ST_Distance, ST_Buffer
# - 几何操作：ST_Union, ST_Intersection, ST_Difference, ST_Simplify
# ================================================================================
# 原有通用提示词剩余部分（已注释保留，不再使用）
# ================================================================================
#
# PgRouting常用函数：
# - 最短路径：pgr_dijkstra, pgr_aStar, pgr_bdDijkstra
# - 路径规划：pgr_trsp, pgr_turnRestrictedPath
# - 网络分析：pgr_connectedComponents, pgr_strongComponents
#
# PostGIS拓扑函数：
# - 拓扑创建：TopoGeo_CreateTopology
# - 拓扑编辑：TopoGeo_AddLineString, TopoGeo_AddPolygon
# - 拓扑查询：GetTopoGeomElements, GetTopoGeomElementArray
#
# 查询示例：
# - "查找距离某个点5公里内的所有建筑" → 使用ST_DWithin
# - "计算两条路线的最短路径" → 使用pgr_dijkstra
# - "分析两个多边形的拓扑关系" → 使用ST_Touches, ST_Overlaps
#
# 请确保生成的SQL查询：
# 1. 包含必要的几何列（通常是geom）
# 2. 每次查询空间表要获得要素时，必须使用ST_AsGeoJSON(ST_Transform(geom, 4326))来将geom属性转换为WGS84坐标系的GeoJSON格式
# 3. 包含适当的空间索引优化
# 4. 避免危险操作（DROP, DELETE等）
#
# ## 响应格式要求
# 你必须严格按照以下JSON格式返回最终答案(final_answer)：
#
# ```json
# {
#   "answer": "你的自然语言回答，解释查询结果和发现",
#   "geojson": {
#     "type": "FeatureCollection",
#     "features": [
#       {
#         "type": "Feature",
#         "geometry": {
#           "type": "Point/LineString/Polygon",
#           "coordinates": [经度, 纬度]
#         },
#         "properties": {
#           "字段1": "值1",
#           "字段2": "值2"
#         }
#       }
#     ]
#   }
# }
# ```
#
# 如果查询不涉及空间数据或不需要返回GeoJSON，可以省略geojson字段。
#
# 请确保你的响应是有效的JSON格式，可以直接被解析。
#
# 重要规则：当查询包含几何数据的表时，如果是空间查询且要求返回结果，默认将查询结果以完整的GeoJSON FeatureCollection形式返回。
#
# 强制要求：对于任何涉及空间表的查询，如果要求返回完整的结果集，必须使用以下格式返回GeoJSON FeatureCollection：
# 例如：
# SELECT jsonb_build_object(
#     'type', 'FeatureCollection',
#     'features', jsonb_agg(
#         jsonb_build_object(
#             'type', 'Feature',
#             'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::jsonb,
#             'properties', to_jsonb(sub) - 'geom'
#         )
#     )
# ) AS geojson
# FROM (
#     SELECT *
#     FROM ${tableName}
#     ${whereClause}
#     ${limitClause}
# ) AS sub
#
# 示例正确的查询格式（已过时 - 使用 whupoi 表）：
# - 简单查询：SELECT gid, name, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry FROM whupoi LIMIT 3
# - 完整GeoJSON查询：SELECT jsonb_build_object('type', 'FeatureCollection', 'features', jsonb_agg(jsonb_build_object('type', 'Feature', 'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::jsonb, 'properties', to_jsonb(sub) - 'geom'))) AS geojson FROM (SELECT * FROM whupoi LIMIT 3) AS sub
#
# 错误的查询格式（缺少坐标转换）：
# SELECT gid, name, geom FROM whupoi LIMIT 3
#
# 如果查询涉及空间分析，请优先使用空间函数而不是普通SQL操作。
#
# 输出格式示例：
# Thought: 我需要先查看数据库中有哪些表
# Action: sql_db_list_tables
# Action Input: ""
#
# 或者：
# Thought: 我已经获得了所有需要的信息
# Final Answer: ""
# ```json
# {
#   "answer": "查询成功返回了2条记录",
#   "geojson": {
#     "type": "FeatureCollection",
#     "features": [...]
#   }
# }
# ```
#
# 重要：最终答案必须使用上述JSON格式，确保可以直接被解析。
# """

# 简化版系统提示词（已注释保留，不再使用）
# SPATIAL_SYSTEM_PROMPT = "你是一个专门处理空间数据库查询的AI助手。请使用PostGIS函数处理空间查询。"


class SpatialSQLQueryAgent:
    """空间SQL查询代理类，专门处理空间数据库查询"""

    def __init__(self, system_prompt: Optional[str] = None, enable_spatial_functions: bool = True):
        """
        初始化空间SQL查询代理 - 优化版本

        Args:
            system_prompt: 自定义系统提示词，如果为None则使用默认空间提示词
            enable_spatial_functions: 是否启用空间函数支持
        """
        # 设置日志
        self.logger = self._setup_logger()
        self.logger.info("开始初始化SpatialSQLQueryAgent...")

        # 初始化数据库连接器
        try:
            self.connector = SQLConnector()
            self.logger.info("✓ SQLConnector 初始化成功")
        except Exception as e:
            self.logger.error(f"✗ SQLConnector 初始化失败: {e}")
            raise

        self.enable_spatial_functions = enable_spatial_functions

        # 创建LLM实例
        try:
            self.llm = BaseLLM()
            self.logger.info("✓ BaseLLM 初始化成功")
        except Exception as e:
            self.logger.error(f"✗ BaseLLM 初始化失败: {e}")
            raise

        # 使用空间系统提示词或自定义提示词
        final_prompt = system_prompt or SPATIAL_SYSTEM_PROMPT

        # 创建包含空间知识的系统提示词
        custom_prompt = ChatPromptTemplate.from_messages([
            ("system", final_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        # 重新配置LLM的提示词
        self.llm.prompt = custom_prompt

        # 创建SQL代理 - 优化配置
        try:
            # 自定义错误处理函数
            def handle_parsing_error(error) -> str:
                """处理 Agent 输出解析错误"""
                error_str = str(error)
                self.logger.warning(f"Agent 输出格式错误: {error_str[:200]}")

                # 提取 LLM 的原始输出
                if "Could not parse LLM output:" in error_str:
                    import re
                    match = re.search(r'Could not parse LLM output: [`\'"](.+?)[`\'"]', error_str, re.DOTALL)
                    if match:
                        llm_output = match.group(1)
                        self.logger.info(f"提取到 LLM 输出: {llm_output[:100]}...")
                        # 返回提取的输出，让 Agent 继续处理
                        return llm_output

                # 如果无法提取，返回提示让 Agent 重试
                return "输出格式不正确，请使用标准格式：首先输出 Action，然后输出 Action Input，或者直接输出 Final Answer。"

            self.agent = create_sql_agent(
                self.llm.llm,
                db=self.connector.db,
                verbose=True,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                max_iterations=15,  # 增加到15次，给 Agent 更多重试机会
                max_execution_time=90,  # 增加到90秒
                agent_executor_kwargs={
                    "return_intermediate_steps": True,
                    "handle_parsing_errors": handle_parsing_error  # 使用自定义错误处理
                }
            )
            self.logger.info("✓ SQL Agent 创建成功")
        except Exception as e:
            self.logger.error(f"✗ SQL Agent 创建失败: {e}")
            raise

        # 初始化思维链捕获相关变量
        self.thought_chain_log = []
        self.logger.info("✓ SpatialSQLQueryAgent 初始化完成")

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def run(self, query: str) -> str:
        """
        执行SQL查询，支持空间查询

        Args:
            query: 自然语言查询字符串

        Returns:
            SQL查询结果字符串
        """
        try:
            if not isinstance(query, str):
                query = str(query)

            # 启用查询增强功能
            enhanced_query = self._enhance_spatial_query(query)
            self.logger.info(f"处理空间查询: {query}")
            self.logger.info(f"增强后的查询: {enhanced_query}")

            # SQL agent expects input as a dictionary with 'input' key
            result = self.agent.invoke({"input": enhanced_query})

            if not isinstance(result, str):
                # Extract the output from the agent result
                if hasattr(result, 'get') and callable(result.get):
                    result = result.get('output', str(result))
                else:
                    result = str(result)

            # 进行后处理，确保空间查询的完整性
            result = self._postprocess_result(result, query)

            return result

        except Exception as e:
            self.logger.error(f"空间查询处理失败: {e}")

            # 简化错误处理，直接返回错误信息
            error_msg = str(e)

            # 检查是否是输出解析错误
            if "output parsing error" in error_msg.lower() or "could not parse llm output" in error_msg.lower():
                # 尝试从错误消息中提取LLM的实际输出
                llm_output_match = re.search(
                    r"Could not parse LLM output: `(.*?)`", error_msg, re.DOTALL)
                if llm_output_match:
                    llm_output = llm_output_match.group(1)
                    self.logger.info(f"提取到LLM输出: {llm_output[:200]}...")
                    return f"LLM响应: {llm_output[:500]}..."

            return f"抱歉，处理您的空间查询时出现了问题：{error_msg}"

    def _enhance_spatial_query(self, query: str) -> str:
        """
        增强查询以包含空间提示 - 优化版本，支持景区双表联合查询检测

        Args:
            query: 原始查询

        Returns:
            增强后的查询
        """
        # ============================================================================
        # 空间查询关键词检测
        # ============================================================================
        spatial_keywords = [
            '距离', '附近', '周围', '范围内', '路径', '路线', '最短', '最近',
            '相交', '包含', '在内', '边界', '面积', '长度', '周长',
            '点', '线', '面', '多边形', '几何', '空间', '地理',
            'buffer', 'intersect', 'contain', 'within', 'distance',
            'route', 'path', 'shortest', 'nearest', 'proximity'
        ]

        # 检查是否包含空间关键词
        has_spatial_keyword = any(keyword in query.lower() for keyword in spatial_keywords)

        # ============================================================================
        # 景区数据表检测（重要！已将 whupoi 替换为 a_sight 和 tourist_spot）
        # ============================================================================
        # 注意：whupoi 表已弃用（仅包含武汉地区数据），不再使用
        # 原代码（已注释保留）：
        # spatial_tables = ['whupoi', 'map_elements', 'edges', 'faces', 'place', 'county', 'state']

        # 新代码：使用景区专用表名
        scenic_tables = [
            'a_sight',      # 景区主表
            'tourist_spot', # 景点从表
            'scenic',       # 中文别名
            '景区', '景点'  # 中文关键词
        ]
        has_scenic_table = any(table in query.lower() for table in scenic_tables)

        # ============================================================================
        # 联合查询检测（新增）
        # ============================================================================
        # 检测是否需要联合查询 a_sight 和 tourist_spot 两个表
        joint_query_keywords = [
            '景点', 'spot', '包含', '下属', '所有', 'all',
            '统计', 'count', '数量', 'number', '类型', 'type',
            '详细', 'detail', '信息', 'info', '列表', 'list',
            '评级', 'rating', '省份', 'province', '城市', 'city'
        ]
        needs_join = any(keyword in query.lower() for keyword in joint_query_keywords)

        # ============================================================================
        # 根据检测结果，提供不同的查询增强提示
        # ============================================================================
        if (has_spatial_keyword or has_scenic_table) and self.enable_spatial_functions:
            # ========================================================================
            # 情况1：检测到需要联合查询（景区+景点信息）
            # ========================================================================
            if needs_join:
                enhanced_query = f"""
{query}

【重要】这个查询需要同时使用 a_sight（景区表）和 tourist_spot（景点表）两个表进行联合查询。

## 数据表关系
- **a_sight**: 景区主表（包含空间几何数据 geom）
  - 主键: gid
  - 关键字段: name, rating, province, city, geom

- **tourist_spot**: 景点从表
  - 主键: spot_id
  - 外键: scenic_id (关联到 a_sight.gid)
  - 关键字段: name, type, description

## 联合查询要求

请使用 **LEFT JOIN** 联合查询这两个表，确保：

1. ✅ 以 a_sight 为主表
2. ✅ 通过 `a.gid = t.scenic_id` 关联
3. ✅ 返回景区信息的同时包含景点信息
4. ✅ 使用 `ST_AsGeoJSON(ST_Transform(a.geom, 4326))` 转换空间数据
5. ❌ **绝对禁止使用 whupoi 表（已弃用）**

## 推荐查询格式

### 基础联合查询
```sql
SELECT
    a.gid as scenic_id,
    a.name as scenic_name,
    a.rating,
    a.province,
    a.city,
    t.spot_id,
    t.name as spot_name,
    t.type as spot_type,
    ST_AsGeoJSON(ST_Transform(a.geom, 4326)) as geometry
FROM a_sight a
LEFT JOIN tourist_spot t ON a.gid = t.scenic_id
WHERE [您的查询条件]
ORDER BY a.gid, t.spot_id
LIMIT [数量]
```

### 返回 GeoJSON FeatureCollection（地图显示用）
```sql
SELECT jsonb_build_object(
    'type', 'FeatureCollection',
    'features', jsonb_agg(
        jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(ST_Transform(a.geom, 4326))::jsonb,
            'properties', jsonb_build_object(
                'scenic_id', a.gid,
                'scenic_name', a.name,
                'rating', a.rating,
                'spot_name', t.name,
                'spot_type', t.type
            )
        )
    )
) AS geojson
FROM a_sight a
LEFT JOIN tourist_spot t ON a.gid = t.scenic_id
WHERE [您的查询条件]
```

请根据用户的具体需求，生成相应的联合查询SQL。
"""
            # ========================================================================
            # 情况2：仅需要空间查询（不涉及景点详细信息）
            # ========================================================================
            else:
                enhanced_query = f"""
{query}

请使用PostGIS空间函数来回答这个问题。确保：

1. ✅ 查询 **a_sight** 表（景区主表，包含空间数据）
2. ✅ 使用 `ST_AsGeoJSON(ST_Transform(geom, 4326))` 转换坐标到WGS84
3. ✅ 如果需要景点信息，请 JOIN tourist_spot 表
4. ❌ **绝对禁止使用 whupoi 表（已弃用，仅武汉数据）**
5. ✅ 如果涉及路径规划，使用PgRouting函数
6. ✅ 使用空间索引优化查询性能

## 示例查询格式

### 简单景区查询
```sql
SELECT
    gid as scenic_id,
    name as scenic_name,
    rating,
    province,
    city,
    ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry
FROM a_sight
WHERE [查询条件]
LIMIT [数量]
```

### GeoJSON FeatureCollection 格式
```sql
SELECT jsonb_build_object(
    'type', 'FeatureCollection',
    'features', jsonb_agg(
        jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::jsonb,
            'properties', to_jsonb(sub) - 'geom'
        )
    )
) AS geojson
FROM (
    SELECT * FROM a_sight WHERE [条件] LIMIT [数量]
) AS sub
```

请直接返回有效的SQL查询语句。
"""
            return enhanced_query
        else:
            # 非空间查询，返回原查询
            return query

    def _handle_query_error(self, error: Exception) -> str:
        """
        处理查询错误 - 优化的错误处理

        Args:
            error: 异常对象

        Returns:
            错误提示信息
        """
        error_msg = str(error)

        # 检查是否是输出解析错误
        if "output parsing error" in error_msg.lower() or "could not parse llm output" in error_msg.lower():
            # 尝试从错误消息中提取LLM的实际输出
            llm_output_match = re.search(
                r"Could not parse LLM output: `(.*?)`", error_msg, re.DOTALL)
            if llm_output_match:
                llm_output = llm_output_match.group(1)
                self.logger.info(f"从错误中提取到LLM输出: {llm_output[:200]}...")
                return llm_output[:1000]  # 返回前1000个字符

        # 检查是否是超时错误
        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            return "抱歉，查询执行超时。请尝试简化您的查询或缩小查询范围。"

        # 检查是否是数据库连接错误
        if "connection" in error_msg.lower() or "connect" in error_msg.lower():
            return "抱歉，数据库连接出现问题。请稍后重试。"

        # 通用错误信息
        return f"抱歉，处理您的空间查询时出现了问题：{error_msg[:200]}"

    def _postprocess_result(self, result: str, original_query: str) -> str:
        """
        后处理查询结果，确保空间查询的完整性 - 优化版本

        Args:
            result: 原始结果
            original_query: 原始查询

        Returns:
            处理后的结果
        """
        # 检查结果是否包含有效的SQL
        if "SELECT" in result.upper() and "FROM" in result.upper():
            # 确保空间查询包含几何列
            spatial_keywords = ['距离', '附近', '相交', '包含', 'distance', 'near', 'intersect', 'contain']
            if any(keyword in original_query.lower() for keyword in spatial_keywords):
                if "geom" not in result.upper() and "ST_" not in result.upper():
                    self.logger.warning("⚠ 空间查询可能缺少几何列或空间函数")

            # 检查GeoJSON转换
            if "GeoJSON" in original_query and "ST_AsGeoJSON" not in result.upper():
                self.logger.info("💡 建议在查询中添加 ST_AsGeoJSON 以生成GeoJSON格式")

        return result

    def execute_spatial_query(self, query: str, return_geojson: bool = True) -> Dict[str, Any]:
        """
        执行空间查询并返回结构化结果

        Args:
            query: SQL查询语句
            return_geojson: 是否返回GeoJSON格式

        Returns:
            结构化查询结果
        """
        try:
            # 执行查询
            result = self.connector.execute_query(query)

            # 如果要求返回GeoJSON，但查询中没有包含ST_AsGeoJSON
            if return_geojson and "ST_AsGeoJSON" not in query.upper():
                self.logger.warning("查询可能未包含GeoJSON转换，建议使用ST_AsGeoJSON")

            return {
                "status": "success",
                "query": query,
                "result": result,
                "geojson_available": "ST_AsGeoJSON" in query.upper()
            }
        except Exception as e:
            self.logger.error(f"执行空间查询失败: {e}")
            return {
                "status": "error",
                "query": query,
                "error": str(e)
            }

    def get_spatial_tables_info(self) -> Dict[str, Any]:
        """
        获取空间表信息

        Returns:
            空间表信息字典
        """
        try:
            # 查询包含几何列的表
            spatial_tables_query = """
            SELECT 
                f_table_name as table_name,
                f_geometry_column as geometry_column,
                type as geometry_type,
                srid,
                coord_dimension
            FROM geometry_columns
            WHERE f_table_schema = 'public'
            ORDER BY f_table_name;
            """

            result = self.connector.execute_query(spatial_tables_query)

            return {
                "status": "success",
                "spatial_tables": result,
                "count": len(result) if isinstance(result, list) else 0
            }
        except Exception as e:
            self.logger.error(f"获取空间表信息失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def analyze_spatial_query(self, query: str) -> Dict[str, Any]:
        """
        分析空间查询的优化建议

        Args:
            query: SQL查询语句

        Returns:
            分析结果
        """
        analysis = {
            "has_spatial_functions": False,
            "spatial_functions_used": [],
            "suggestions": [],
            "optimization_tips": []
        }

        # 检查使用的空间函数
        spatial_functions = [
            "ST_", "pgr_", "TopoGeo_", "ST_AsGeoJSON", "ST_Transform",
            "ST_Intersects", "ST_Contains", "ST_Within", "ST_Distance",
            "ST_Buffer", "ST_Union", "ST_Intersection"
        ]

        for func in spatial_functions:
            if func in query.upper():
                analysis["has_spatial_functions"] = True
                analysis["spatial_functions_used"].append(func)

        # 提供优化建议
        if analysis["has_spatial_functions"]:
            if "ST_DWithin" not in query.upper() and ("ST_Distance" in query.upper() or "距离" in query):
                analysis["suggestions"].append(
                    "考虑使用ST_DWithin替代ST_Distance进行距离过滤，性能更好")

            if "geom" in query.upper() and "INDEX" not in query.upper():
                analysis["optimization_tips"].append("确保几何列上有空间索引（GIST索引）")

            if "ST_Transform" in query.upper():
                analysis["optimization_tips"].append("考虑在应用层进行坐标转换，而不是在数据库层")

        return analysis

    def run_with_thought_chain(self, query: str) -> Dict[str, Any]:
        """
        执行SQL查询并返回完整的思维链，包括SQL查询的执行结果

        Args:
            query: 自然语言查询字符串

        Returns:
            包含思维链和最终结果的字典
        """
        try:
            if not isinstance(query, str):
                query = str(query)

            # 启用查询增强功能
            enhanced_query = self._enhance_spatial_query(query)
            self.logger.info(f"处理空间查询: {query}")
            self.logger.info(f"增强后的查询: {enhanced_query}")

            # 执行查询并获取中间步骤
            result = self.agent.invoke({"input": enhanced_query})
            
            print(f'result: {result}')
            # 提取中间步骤（即使有输出解析错误，中间步骤仍然可用）
            intermediate_steps = result.get('intermediate_steps', [])
            
            # 构建思维链
            thought_chain = []
            sql_queries_with_results = []
            
            for step_num, (action, observation) in enumerate(intermediate_steps, 1):
                # 构建动作步骤
                action_step = {
                    "step": step_num,
                    "type": "action",
                    "action": action.tool,
                    "action_input": action.tool_input,
                    "log": action.log,
                    "timestamp": str(hash(str(action))),
                    "observation": str(observation) if observation else "No output",
                    "status": "completed"
                }
                thought_chain.append(action_step)
                
                # 如果是SQL查询，记录详细信息
                if action.tool == 'sql_db_query':
                    sql_queries_with_results.append({
                        "sql": action.tool_input,
                        "result": observation,
                        "step": step_num,
                        "status": "completed"
                    })
            
            # 尝试提取最终结果，即使有错误也继续处理
            final_result = ""
            try:
                if hasattr(result, 'get'):
                    final_result = result.get('output', '')
                else:
                    final_result = str(result)
            except:
                final_result = "无法提取最终结果（可能存在输出解析错误）"
            
            # 添加最终答案步骤
            if final_result:
                final_step = {
                    "step": len(thought_chain) + 1,
                    "type": "final_answer",
                    "content": final_result,
                    "log": final_result,
                    "timestamp": str(hash(final_result)),
                    "status": "completed"
                }
                thought_chain.append(final_step)

            self.logger.info(f"捕获到{len(sql_queries_with_results)}个SQL查询及其执行结果")

            return {
                "status": "success" if intermediate_steps else "partial_success",
                "final_answer": final_result,
                "thought_chain": thought_chain,
                "step_count": len(thought_chain),
                "sql_queries_with_results": sql_queries_with_results,
                "intermediate_steps": intermediate_steps  # 保留原始中间步骤数据
            }

        except Exception as e:
            self.logger.error(f"Error in run_with_thought_chain function: {e}")
            
            # 检查是否是输出解析错误
            error_msg = str(e)
            if "output parsing error" in error_msg.lower() or "could not parse llm output" in error_msg.lower():
                # 尝试从错误消息中提取LLM的实际输出
                llm_output_match = re.search(
                    r"Could not parse LLM output: `(.*?)`", error_msg, re.DOTALL)
                if llm_output_match:
                    llm_output = llm_output_match.group(1)
                    self.logger.info(f"提取到LLM输出: {llm_output[:200]}...")
                    
                    # 即使有解析错误，也尝试构建思维链
                    thought_chain = [{
                        "step": 1,
                        "type": "final_answer",
                        "content": llm_output,
                        "log": llm_output,
                        "timestamp": str(hash(llm_output)),
                        "status": "completed_with_parsing_error"
                    }]
                    
                    return {
                        "status": "partial_success",
                        "final_answer": llm_output,
                        "thought_chain": thought_chain,
                        "step_count": 1,
                        "sql_queries_with_results": [],
                        "warning": "输出解析错误，但已提取LLM原始输出"
                    }
            
            return {
                "status": "error",
                "error": f"处理您的请求时出现了问题：{str(e)}",
                "thought_chain": [],
                "step_count": 0,
                "sql_queries_with_results": []
            }

    def close(self):
        """清理资源"""
        if hasattr(self, 'connector'):
            self.connector.close()


# 使用示例
if __name__ == "__main__":
    # 创建空间查询代理
    spatial_agent = SpatialSQLQueryAgent()

    try:
        # 获取空间表信息
        tables_info = spatial_agent.get_spatial_tables_info()
        print("空间表信息:", tables_info)

        # 示例空间查询
        test_queries = [
            "查找距离某个点5公里内的所有建筑",
            "计算从A点到B点的最短路径",
            "查找与某个多边形相交的所有道路"
        ]

        for query in test_queries:
            print(f"\n查询: {query}")
            result = spatial_agent.run(query)
            print(f"结果: {result}")

            # 分析查询
            analysis = spatial_agent.analyze_spatial_query(result)
            print(f"分析: {analysis}")

    finally:
        spatial_agent.close()
