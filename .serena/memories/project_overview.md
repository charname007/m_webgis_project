# WebGIS Project - 项目概览

## 项目目的
这是一个先进的WebGIS应用程序，结合了AI驱动的自然语言查询与空间数据可视化功能。项目主要面向景区旅游数据分析和查询。

## 技术栈

### 后端 (Python)
- **Web框架**: FastAPI 0.109.0
- **AI/LLM**: LangChain 0.1.6, LangGraph
- **数据库**: PostgreSQL + PostGIS, SQLAlchemy 2.0.25
- **配置管理**: Pydantic 2.5.3, pydantic-settings 2.1.0
- **开发工具**: pytest, black, flake8 (注释状态)

### 前端 (Vue3)
- **框架**: Vue 3.5.18 + Vite 7.0.6
- **地图**: OpenLayers 10.6.1, Mapbox GL 3.15.0
- **图表**: ECharts 5.4.3
- **HTTP客户端**: Axios 1.12.2

## 核心架构特性

### AI驱动的查询系统
- LangGraph多步工作流
- 意图分析（空间vs非空间，查询vs摘要）
- 查询验证和错误恢复
- 会话管理和记忆持久化

### 缓存策略
- 语义相似性搜索
- 混合缓存（内存+数据库）
- 外部缓存支持

### 空间数据支持
- PostgreSQL + PostGIS
- GeoJSON转换
- 坐标系统转换

## 项目结构
```
m_webgis_project/
├── m_WGP_vue3/          # Vue3前端
├── python/sight_server/ # FastAPI后端
├── memory-bank/         # 项目文档
├── cache/               # 缓存数据
└── checkpoints/         # LangGraph检查点
```