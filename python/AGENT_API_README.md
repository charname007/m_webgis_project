# 智能代理API接口文档

## 概述

这是一个通用型REST API接口，用户与agent对话，agent智能判断查询类型（是否需要执行SQL查询、是否从数据库中总结数据、是否查询空间表），并返回标准化格式的结果。

## API端点

### 1. 健康检查
```
GET /
```
返回服务器状态信息

### 2. 智能代理查询（POST方式）
```
POST /agent/query
```
**请求参数：**
```json
{
  "question": "自然语言查询文本",
  "chat_history": [], // 可选，聊天历史记录
  "execute_sql": true, // 可选，是否执行SQL查询，默认为true
  "return_geojson": true // 可选，是否返回GeoJSON格式，默认为true
}
```

**响应格式：**
```json
{
  "status": "success|error",
  "question": {
    "text": "原始查询文本",
    "type": "spatial|summary|sql|general",
    "analysis": {
      "query_type": "spatial|summary|sql|general",
      "priority": 1|2|3|4,
      "is_spatial": true|false,
      "is_summary": true|false,
      "is_sql": true|false,
      "spatial_keywords_found": [],
      "summary_keywords_found": [],
      "sql_keywords_found": []
    }
  },
  "answer": {
    "text": "代理的回答文本",
    "analysis": {}, // 查询分析信息
    "feature_count": 10, // 如有GeoJSON，要素数量
    "query_result": {} // 如有SQL执行结果
  },
  "sql": ["SQL查询语句1", "SQL查询语句2"], // 生成的SQL查询列表
  "geojson": {} // 如有空间数据，GeoJSON格式
}
```

### 3. 智能代理查询（GET方式）
```
GET /agent/query/{question}
```
URL编码的自然语言查询文本

### 4. 查询类型分析
```
POST /agent/analyze
```
**请求参数：**
```json
{
  "question": "自然语言查询文本"
}
```

## 查询类型识别

### 空间查询（优先级1）
**关键词：** 距离、附近、周围、范围内、路径、路线、最短、最近、相交、包含、在内、边界、面积、长度、周长、点、线、面、多边形、几何、空间、地理、坐标、经纬度等

**示例：**
- "查找距离珞珈山最近的点"
- "查询武汉大学周围的建筑"
- "显示所有道路数据"

### 数据总结查询（优先级2）
**关键词：** 总结、统计、汇总、分析、报告、概况、总数、平均、最大、最小、分布、趋势、比例等

**示例：**
- "统计whupoi表中的数据总数"
- "分析道路类型的分布情况"
- "总结建筑数据的特征"

### 普通SQL查询（优先级3）
**关键词：** 查询、查找、搜索、获取、显示、列出等

**示例：**
- "查询所有表名"
- "显示数据库信息"

### 通用查询（优先级4）
其他类型的查询

## 使用示例

### Python客户端示例

```python
import requests
import json

BASE_URL = "http://localhost:8003"

# 1. 测试健康检查
response = requests.get(f"{BASE_URL}/")
print(response.json())

# 2. 分析查询类型
analysis = requests.post(f"{BASE_URL}/agent/analyze", json={
    "question": "查找距离珞珈山最近的点"
})
print(json.dumps(analysis.json(), indent=2, ensure_ascii=False))

# 3. 执行智能查询
result = requests.post(f"{BASE_URL}/agent/query", json={
    "question": "查找距离珞珈山最近的点",
    "execute_sql": True,
    "return_geojson": True
})
data = result.json()

print(f"查询类型: {data['question']['type']}")
print(f"SQL查询: {data['sql']}")
if data.get('geojson'):
    print(f"GeoJSON要素数量: {len(data['geojson']['features'])}")
```

### cURL示例

```bash
# 健康检查
curl http://localhost:8003/

# 查询类型分析
curl -X POST http://localhost:8003/agent/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "查找距离珞珈山最近的点"}'

# 智能查询
curl -X POST http://localhost:8003/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "查找距离珞珈山最近的点",
    "execute_sql": true,
    "return_geojson": true
  }'
```

## 技术特性

### 1. 智能查询类型判断
- 基于关键词分析自动识别查询意图
- 优先级：空间查询 > 数据总结 > 普通SQL查询 > 通用查询
- 支持中英文混合查询

### 2. 空间数据处理
- 自动生成包含PostGIS函数的SQL查询
- 支持GeoJSON格式输出
- 包含几何数据转换和坐标系处理

### 3. 错误处理
- 输入验证和安全性检查
- SQL注入防护
- 详细的错误信息和状态码

### 4. 性能优化
- 连接池管理
- 查询缓存
- 异步处理支持

## 部署说明

### 启动服务器
```bash
cd python
python server.py --port 8003
```

### 测试API
```bash
cd python
python test_agent_api.py
```

## 依赖组件

- **FastAPI**: Web框架
- **SQLQueryAgent**: SQL查询代理
- **EnhancedSpatialSQLQueryAgent**: 增强空间查询代理
- **PostgreSQL + PostGIS**: 空间数据库
- **GeoJSONGenerator**: GeoJSON数据生成器

## 故障排除

### 常见问题

1. **端口占用**: 使用不同的端口启动服务器
2. **数据库连接失败**: 检查数据库配置和连接字符串
3. **SQL查询错误**: 检查数据库表结构和权限
4. **GeoJSON生成失败**: 检查几何数据格式和坐标系

### 日志查看
服务器启动时会显示详细的日志信息，包括：
- 数据库连接状态
- PostGIS版本信息
- 可用表列表
- 查询处理过程

## 版本信息

- API版本: 1.0.0
- 支持格式: JSON/GeoJSON
- 协议: HTTP/HTTPS
- 编码: UTF-8
