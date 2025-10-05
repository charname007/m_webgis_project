# Sight Server API 使用指南

完整的 API 接口文档和使用示例

## 📑 目录

- [API 概览](#api-概览)
- [认证与安全](#认证与安全)
- [端点详解](#端点详解)
  - [标准查询 POST /query](#1-标准查询)
  - [GeoJSON 查询 POST /query/geojson](#2-geojson-查询)
  - [思维链查询 POST /query/thought-chain](#3-思维链查询)
  - [健康检查 GET /health](#4-健康检查)
  - [数据库信息 GET /database/info](#5-数据库信息)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

## API 概览

**基础 URL**: `http://localhost:8001`

**内容类型**: `application/json`

**支持的 HTTP 方法**: `GET`, `POST`

### 快速导航

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 简单健康检查 |
| `/health` | GET | 详细健康检查 |
| `/query` | POST | 标准 JSON 查询 |
| `/query/geojson` | POST | GeoJSON 格式查询 |
| `/query/thought-chain` | POST | 思维链调试查询 |
| `/tables` | GET | 获取数据表列表 |
| `/database/info` | GET | 获取数据库信息 |
| `/docs` | GET | Swagger UI 文档 |
| `/redoc` | GET | ReDoc 文档 |

## 认证与安全

当前版本不需要 API 认证，但建议：

1. **CORS 配置**: 在生产环境中限制允许的源
2. **速率限制**: 考虑添加速率限制中间件
3. **输入验证**: 已内置危险 SQL 关键词检测

## 端点详解

### 1. 标准查询

**端点**: `POST /query`

**用途**: 将自然语言查询转换为 SQL，返回 JSON 格式数据和自然语言回答。

#### 请求参数

```json
{
  "query": "string (必需)",        // 自然语言查询，1-500字符
  "limit": 10,                     // 结果数量限制，1-100，默认10
  "return_format": "json",         // 返回格式，可选：json, geojson, structured
  "include_sql": false             // 是否返回执行的SQL，默认false
}
```

#### 响应格式

```json
{
  "status": "success",             // 查询状态：success, error, partial
  "answer": "string",              // Agent生成的自然语言回答
  "data": [                        // 结构化查询结果
    {
      "gid": 1,
      "name": "西湖",
      "level": "5A",
      "所属省份": "浙江省",
      "所属城市": "杭州市",
      "coordinates_wgs84": [120.15, 30.25]
    }
  ],
  "count": 19,                     // 结果数量
  "message": "查询成功",           // 状态消息
  "sql": "SELECT ...",             // SQL语句（如果include_sql=true）
  "execution_time": 2.35           // 执行时间（秒）
}
```

#### 示例

**请求**:
```bash
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询浙江省的5A景区",
    "limit": 10,
    "include_sql": true
  }'
```

**响应**:
```json
{
  "status": "success",
  "answer": "浙江省共有19个5A级景区，包括杭州西湖、普陀山、雁荡山等著名景点。",
  "data": [
    {
      "gid": 1,
      "name": "西湖",
      "level": "5A",
      "所属省份": "浙江省",
      "所属城市": "杭州市",
      "coordinates_wgs84": [120.15, 30.25],
      "coordinates_gcj02": [120.156, 30.254],
      "coordinates_bd09": [120.162, 30.260]
    }
  ],
  "count": 19,
  "message": "查询成功",
  "sql": "SELECT json_agg(row_to_json(t)) FROM (SELECT * FROM a_sight WHERE 所属省份='浙江省' AND level='5A' LIMIT 10) t",
  "execution_time": 2.35
}
```

#### Python 示例

```python
import requests

response = requests.post(
    "http://localhost:8001/query",
    json={
        "query": "查询浙江省的5A景区",
        "limit": 10,
        "include_sql": True
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Agent回答: {result['answer']}")
    print(f"找到 {result['count']} 条结果")
    for item in result['data']:
        print(f"- {item['name']} ({item['level']})")
else:
    print(f"错误: {response.status_code}")
```

### 2. GeoJSON 查询

**端点**: `POST /query/geojson`

**用途**: 返回 GeoJSON FeatureCollection 格式，可直接用于地图可视化。

#### 请求参数

```json
{
  "query": "string (必需)",              // 自然语言查询
  "coordinate_system": "wgs84",         // 坐标系：wgs84, gcj02, bd09
  "limit": 100,                         // 结果数量限制，1-1000，默认100
  "include_properties": true            // 是否包含属性信息，默认true
}
```

#### 坐标系说明

| 坐标系 | 说明 | 适用地图 |
|--------|------|----------|
| `wgs84` | WGS-84 (EPSG:4326) GPS标准 | Google Maps, Mapbox, Leaflet |
| `gcj02` | GCJ-02 国测局火星坐标系 | 高德地图, 腾讯地图 |
| `bd09` | BD-09 百度坐标系 | 百度地图 |

#### 响应格式

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 1,
      "geometry": {
        "type": "Point",
        "coordinates": [120.15, 30.25]
      },
      "properties": {
        "name": "西湖",
        "level": "5A",
        "所属省份": "浙江省",
        "所属城市": "杭州市"
      }
    }
  ],
  "metadata": {
    "count": 19,
    "skipped": 0,
    "coordinate_system": "wgs84",
    "source_coordinate_system": "wgs84",
    "execution_time": 1.82,
    "query": "查询浙江省的5A景区"
  }
}
```

#### 示例

**请求**:
```bash
curl -X POST "http://localhost:8001/query/geojson" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查找杭州市的景区",
    "coordinate_system": "gcj02",
    "limit": 100
  }'
```

#### JavaScript + OpenLayers 示例

```javascript
// 查询 GeoJSON 数据
const response = await fetch('http://localhost:8001/query/geojson', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: '查找杭州市的景区',
    coordinate_system: 'gcj02',
    limit: 100
  })
});

const geojson = await response.json();

// 在 OpenLayers 中使用
import VectorSource from 'ol/source/Vector';
import VectorLayer from 'ol/layer/Vector';
import GeoJSON from 'ol/format/GeoJSON';

const vectorSource = new VectorSource({
  features: new GeoJSON().readFeatures(geojson)
});

const vectorLayer = new VectorLayer({
  source: vectorSource
});

map.addLayer(vectorLayer);
```

#### Leaflet 示例

```javascript
// 查询 GeoJSON
const response = await fetch('http://localhost:8001/query/geojson', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: '查找杭州市的景区',
    coordinate_system: 'gcj02'
  })
});

const geojson = await response.json();

// 在 Leaflet 中使用
L.geoJSON(geojson, {
  onEachFeature: function (feature, layer) {
    if (feature.properties) {
      layer.bindPopup(`
        <h3>${feature.properties.name}</h3>
        <p>等级: ${feature.properties.level}</p>
      `);
    }
  }
}).addTo(map);
```

### 3. 思维链查询

**端点**: `POST /query/thought-chain`

**用途**: 展示 Agent 的完整推理过程，用于调试和学习。

#### 请求参数

```json
{
  "query": "string (必需)",        // 自然语言查询
  "verbose": true                  // 是否返回详细步骤，默认true
}
```

#### 响应格式

```json
{
  "status": "success",
  "final_answer": "浙江省共有18个4A景区",
  "thought_chain": [
    {
      "step": 1,
      "type": "action",
      "action": "sql_db_list_tables",
      "action_input": "",
      "log": "思考过程...",
      "observation": "a_sight, tourist_spot",
      "status": "completed"
    },
    {
      "step": 2,
      "type": "action",
      "action": "sql_db_query",
      "action_input": "SELECT COUNT(*) FROM a_sight WHERE level='4A' AND 所属省份='浙江省'",
      "observation": "[(18,)]",
      "status": "completed"
    },
    {
      "step": 3,
      "type": "final_answer",
      "content": "浙江省共有18个4A景区",
      "status": "completed"
    }
  ],
  "step_count": 3,
  "sql_queries": [
    {
      "sql": "SELECT COUNT(*) FROM a_sight WHERE level='4A' AND 所属省份='浙江省'",
      "result": "[(18,)]",
      "step": 2,
      "status": "completed"
    }
  ]
}
```

#### 示例

**请求**:
```bash
curl -X POST "http://localhost:8001/query/thought-chain" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "统计浙江省有多少个4A景区",
    "verbose": true
  }'
```

#### Python 调试示例

```python
import requests
import json

response = requests.post(
    "http://localhost:8001/query/thought-chain",
    json={
        "query": "统计浙江省有多少个4A景区",
        "verbose": True
    }
)

result = response.json()

print(f"最终答案: {result['final_answer']}")
print(f"\n推理过程 ({result['step_count']} 步):\n")

for step in result['thought_chain']:
    if step['type'] == 'action':
        print(f"步骤 {step['step']}: {step['action']}")
        print(f"  输入: {step['action_input']}")
        print(f"  结果: {step.get('observation', 'N/A')}\n")
    else:
        print(f"步骤 {step['step']}: 最终答案")
        print(f"  {step['content']}\n")

print(f"\n执行的 SQL 查询:")
for query in result['sql_queries']:
    print(f"  {query['sql']}")
    print(f"  结果: {query['result']}\n")
```

### 4. 健康检查

**端点**: `GET /health`

**用途**: 检查服务状态。

#### 响应格式

```json
{
  "status": "healthy",              // healthy, degraded
  "message": "All systems operational",
  "agent_status": "initialized",    // initialized, not_initialized
  "database_status": "connected",   // connected, error, unknown
  "version": "1.0.0"
}
```

#### 示例

```bash
curl "http://localhost:8001/health"
```

### 5. 数据库信息

**端点**: `GET /database/info`

**用途**: 获取数据库详细信息。

#### 响应格式

```json
{
  "status": "success",
  "database_name": "WGP_db",
  "postgres_version": "PostgreSQL 15.2",
  "postgis_version": "3.3.2",
  "table_count": 5,
  "spatial_table_count": 2,
  "tables": [
    {
      "table_name": "a_sight",
      "geometry_column": "geom",
      "geometry_type": "Point",
      "srid": 4326,
      "row_count": 1500
    }
  ]
}
```

#### 示例

```bash
curl "http://localhost:8001/database/info"
```

## 错误处理

### 错误响应格式

```json
{
  "error": "ValidationError",
  "message": "查询文本不能为空",
  "details": "Field required: query",
  "status": "error"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用（Agent 未初始化） |

### 常见错误

#### 1. Agent 未初始化

**错误**:
```json
{
  "error": "Service Unavailable",
  "message": "SQL Query Agent 未初始化，请检查配置"
}
```

**解决**: 检查 `.env` 中的数据库和 LLM 配置。

#### 2. 查询包含危险关键词

**错误**:
```json
{
  "error": "ValidationError",
  "message": "查询包含潜在危险关键词: drop table"
}
```

**解决**: 避免使用 DDL 语句关键词（DROP, DELETE, TRUNCATE 等）。

#### 3. 数据库连接失败

**错误**:
```json
{
  "error": "Database Error",
  "message": "无法连接到数据库"
}
```

**解决**: 检查 `DATABASE_URL` 配置和数据库服务状态。

## 最佳实践

### 1. 查询优化

✅ **推荐**:
```json
{
  "query": "查询浙江省杭州市的5A景区",
  "limit": 10
}
```

❌ **不推荐**:
```json
{
  "query": "查询所有景区",  // 过于宽泛
  "limit": 10000           // 限制过大
}
```

### 2. 坐标系选择

根据使用的地图服务选择正确的坐标系：

```javascript
// 高德地图
const response = await fetch('/query/geojson', {
  body: JSON.stringify({
    query: "...",
    coordinate_system: "gcj02"  // 高德使用 GCJ-02
  })
});

// Google Maps / Mapbox
const response = await fetch('/query/geojson', {
  body: JSON.stringify({
    query: "...",
    coordinate_system: "wgs84"  // 国际标准
  })
});
```

### 3. 错误处理

```python
import requests

try:
    response = requests.post(
        "http://localhost:8001/query",
        json={"query": "查询浙江省的5A景区"},
        timeout=30  # 设置超时
    )
    response.raise_for_status()  # 检查 HTTP 错误

    result = response.json()

    if result['status'] == 'success':
        print(f"成功: {result['answer']}")
    else:
        print(f"查询失败: {result['message']}")

except requests.exceptions.Timeout:
    print("请求超时")
except requests.exceptions.ConnectionError:
    print("无法连接到服务器")
except requests.exceptions.HTTPError as e:
    print(f"HTTP 错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 4. 批量查询

```python
queries = [
    "查询浙江省的5A景区",
    "查询江苏省的4A景区",
    "查询上海市的景区"
]

results = []
for query in queries:
    response = requests.post(
        "http://localhost:8001/query",
        json={"query": query, "limit": 10}
    )
    if response.status_code == 200:
        results.append(response.json())

# 处理结果
for result in results:
    print(f"{result['answer']} - {result['count']} 条结果")
```

### 5. 性能优化

- 使用适当的 `limit` 限制结果数量
- 避免过于复杂的自然语言查询
- 使用 `/query/geojson` 时考虑数据量
- 生产环境启用连接池和缓存

### 6. 调试技巧

使用思维链端点了解 Agent 的行为：

```python
# 先用思维链调试
debug_response = requests.post(
    "http://localhost:8001/query/thought-chain",
    json={"query": "复杂查询", "verbose": True}
)

# 查看 SQL 执行情况
for query in debug_response.json()['sql_queries']:
    print(f"SQL: {query['sql']}")
    print(f"结果: {query['result']}")

# 确认无误后用标准端点
final_response = requests.post(
    "http://localhost:8001/query",
    json={"query": "复杂查询"}
)
```

## 附录

### A. 查询示例集合

**基础查询**:
- "查询浙江省的5A景区"
- "查找杭州市的所有景区"
- "显示评分最高的10个景区"

**统计查询**:
- "统计浙江省有多少个4A景区"
- "按城市统计景区数量"
- "计算平均门票价格"

**空间查询**:
- "查找距离杭州西湖10公里内的景区"
- "查询钱塘江沿岸的景区"
- "显示浙江省范围内的所有景区"

**复杂查询**:
- "查找杭州市评分大于4.5且门票低于100的景区"
- "统计每个省份的5A景区数量，按数量降序排列"
- "查询既有自然风光又有历史文化的景区"

### B. 数据库表结构

**a_sight 表**:
```sql
CREATE TABLE a_sight (
    gid SERIAL PRIMARY KEY,
    name VARCHAR(255),
    level VARCHAR(10),
    所属省份 VARCHAR(50),
    所属城市 VARCHAR(50),
    coordinates_wgs84 DOUBLE PRECISION[],
    coordinates_gcj02 DOUBLE PRECISION[],
    coordinates_bd09 DOUBLE PRECISION[],
    geom GEOMETRY(Point, 4326)
);
```

**tourist_spot 表**:
```sql
CREATE TABLE tourist_spot (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    链接 VARCHAR(500),
    地址 VARCHAR(500),
    评分 DOUBLE PRECISION,
    门票 VARCHAR(100),
    开放时间 VARCHAR(200)
);
```

---

**更新日期**: 2025-10-04
**版本**: 1.0.0
**维护者**: Sight Server Development Team
