# Sight Server 🗺️

基于 LangChain Agent 的景区数据自然语言查询 API 服务

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green)
![LangChain](https://img.shields.io/badge/LangChain-0.1.6-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-blue)
![PostGIS](https://img.shields.io/badge/PostGIS-3.0%2B-lightblue)

## 📖 项目简介

Sight Server 是一个智能的景区数据查询服务，能够将自然语言查询转换为 SQL 并执行，支持空间查询、多坐标系转换和 GeoJSON 输出。

### 核心特性

- 🤖 **自然语言查询** - 使用自然语言查询景区数据，无需编写 SQL
- 🗺️ **空间查询支持** - 支持 PostGIS 空间查询（距离、范围、包含等）
- 🌍 **多坐标系** - 支持 WGS84、GCJ02、BD09 三种坐标系转换
- 📊 **GeoJSON 输出** - 直接输出 GeoJSON 用于地图可视化
- 🔍 **思维链展示** - 完整展示 Agent 的推理过程
- ⚡ **高性能** - FastAPI 异步框架，连接池优化
- 📝 **完整日志** - 详细的日志记录和错误追踪

## 🚀 快速开始

### 前置要求

- Python 3.9+
- PostgreSQL 13+ with PostGIS 3.0+
- DeepSeek API Key（或其他兼容 OpenAI 的 LLM）

### 安装步骤

1. **克隆项目**
```bash
cd sight_server
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

必需的环境变量：
```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/database

# LLM 配置
DEEPSEEK_API_KEY=your_api_key_here
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=1.3

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8001
DEBUG=false
```

5. **启动服务**
```bash
python main.py
```

或使用 uvicorn：
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

6. **访问 API 文档**
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 📚 API 端点

### 查询相关

#### `POST /query` - 标准查询
自然语言查询，返回 JSON 格式数据和自然语言回答。

**请求示例：**
```json
{
  "query": "查询浙江省的5A景区",
  "limit": 10,
  "include_sql": false
}
```

**响应示例：**
```json
{
  "status": "success",
  "answer": "浙江省共有19个5A级景区，包括杭州西湖、普陀山、雁荡山等著名景点。",
  "data": [
    {
      "name": "西湖",
      "level": "5A",
      "province": "浙江省",
      "city": "杭州市",
      "coordinates_wgs84": [120.15, 30.25]
    }
  ],
  "count": 19,
  "message": "查询成功",
  "execution_time": 2.35
}
```

#### `POST /query/geojson` - GeoJSON 查询
返回 GeoJSON FeatureCollection 格式，适合地图可视化。

**请求示例：**
```json
{
  "query": "查找杭州市的景区",
  "coordinate_system": "wgs84",
  "limit": 100,
  "include_properties": true
}
```

**响应示例：**
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
        "province": "浙江省"
      }
    }
  ],
  "metadata": {
    "count": 10,
    "coordinate_system": "wgs84",
    "execution_time": 1.82
  }
}
```

#### `POST /query/thought-chain` - 思维链查询
展示 Agent 的完整推理过程，用于调试和学习。

**请求示例：**
```json
{
  "query": "统计浙江省有多少个4A景区",
  "verbose": true
}
```

**响应示例：**
```json
{
  "status": "success",
  "final_answer": "浙江省共有18个4A景区",
  "thought_chain": [
    {
      "step": 1,
      "type": "action",
      "action": "sql_db_query",
      "action_input": "SELECT COUNT(*) FROM a_sight WHERE level='4A' AND province='浙江省'"
    }
  ],
  "step_count": 3,
  "sql_queries": [
    {
      "sql": "SELECT COUNT(*) FROM a_sight WHERE level='4A'",
      "result": "18",
      "step": 1
    }
  ]
}
```

### 系统相关

#### `GET /` - 健康检查
```json
{
  "status": "healthy",
  "message": "Sight Server is running",
  "agent_status": "initialized",
  "database_status": "connected",
  "version": "1.0.0"
}
```

#### `GET /health` - 详细健康检查
详细的系统状态检查。

#### `GET /tables` - 获取表列表
返回数据库中所有可用的表名。

#### `GET /database/info` - 数据库信息
返回 PostgreSQL 和 PostGIS 版本信息。

## 🗂️ 项目结构

```
sight_server/
├── main.py                 # FastAPI 应用主文件
├── config.py              # 配置管理
├── requirements.txt       # 依赖列表
├── .env                   # 环境变量（不提交）
├── .env.example          # 环境变量示例
├── README.md             # 项目文档
├── core/                 # 核心模块
│   ├── __init__.py
│   ├── llm.py           # LLM 基础类
│   ├── database.py      # 数据库连接器
│   ├── prompts.py       # 提示词管理器
│   └── agent.py         # SQL 查询 Agent
├── models/              # 数据模型
│   ├── __init__.py
│   └── api_models.py    # API 请求/响应模型
└── utils/               # 工具类
    ├── __init__.py
    └── geojson_utils.py # GeoJSON 转换工具
```

## 🔧 配置说明

### 数据库配置

确保你的 PostgreSQL 数据库已安装 PostGIS 扩展：

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

数据表要求：
- `a_sight` - 景区基础信息表
  - 必需字段：`gid`, `name`, `level`, `所属省份`, `所属城市`
  - 坐标字段：`coordinates_wgs84`, `coordinates_gcj02`, `coordinates_bd09`
- `tourist_spot` - 景区详细信息表（可选）

### LLM 配置

支持任何兼容 OpenAI API 的 LLM 服务：

```env
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_API_BASE=https://api.deepseek.com
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=1.3
```

### 服务器配置

```env
SERVER_HOST=0.0.0.0      # 监听地址
SERVER_PORT=8001         # 端口
SERVER_RELOAD=false      # 开发模式热重载
DEBUG=false              # 调试模式
```

## 🎯 使用示例

### Python 客户端

```python
import requests

# 标准查询
response = requests.post("http://localhost:8001/query", json={
    "query": "查询浙江省的5A景区",
    "limit": 10
})
result = response.json()
print(f"回答: {result['answer']}")
print(f"数据: {result['data']}")

# GeoJSON 查询
response = requests.post("http://localhost:8001/query/geojson", json={
    "query": "查找杭州市的景区",
    "coordinate_system": "gcj02"
})
geojson = response.json()
# 可直接用于 OpenLayers, Leaflet 等地图库
```

### JavaScript 客户端

```javascript
// 使用 fetch API
const response = await fetch('http://localhost:8001/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: '查询浙江省的5A景区',
    limit: 10
  })
});

const result = await response.json();
console.log('回答:', result.answer);
console.log('数据:', result.data);
```

### cURL

```bash
# 标准查询
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "查询浙江省的5A景区", "limit": 10}'

# GeoJSON 查询
curl -X POST "http://localhost:8001/query/geojson" \
  -H "Content-Type: application/json" \
  -d '{"query": "查找杭州市的景区", "coordinate_system": "wgs84"}'
```

## 🌟 查询示例

### 基础查询
- "查询浙江省的5A景区"
- "查找杭州市的所有景区"
- "显示评分最高的10个景区"

### 统计查询
- "统计浙江省有多少个4A景区"
- "按城市统计景区数量"
- "计算平均门票价格"

### 空间查询
- "查找距离杭州10公里内的景区"
- "查询西湖周边5公里的景区"
- "显示浙江省边界内的所有景区"

### 复杂查询
- "查找杭州市评分大于4.5且门票低于100的景区"
- "统计每个省份的5A景区数量"
- "查询既有博物馆标签又有历史遗迹标签的景区"

## 🐛 调试与日志

### 日志级别

在 `.env` 中设置：
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 查看详细日志

启动时会显示：
```
2025-10-04 12:00:00 - __main__ - INFO - 🚀 Starting Sight Server...
2025-10-04 12:00:01 - core.agent - INFO - ✓ DatabaseConnector initialized
2025-10-04 12:00:02 - core.agent - INFO - ✓ BaseLLM initialized
2025-10-04 12:00:03 - core.agent - INFO - ✓ SQL Agent created successfully
```

### 使用思维链调试

使用 `/query/thought-chain` 端点查看 Agent 的完整推理过程。

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

## 📄 许可证

MIT License

## 👥 作者

Sight Server Development Team

## 🔗 相关链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [LangChain 文档](https://python.langchain.com/)
- [PostGIS 文档](https://postgis.net/documentation/)
- [DeepSeek API](https://platform.deepseek.com/docs)

---

**注意**: 本项目用于景区数据查询服务，请确保遵守相关数据使用规范。
