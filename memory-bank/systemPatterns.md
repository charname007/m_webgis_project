# 系统架构与设计模式

## 系统架构概述
本项目采用前后端分离的微服务架构，分为三个主要组件：
1. **前端应用** (Vue.js 3) - 提供用户界面和地图交互
2. **后端服务** (Spring Boot) - 处理业务逻辑和数据处理
3. **Python Sight Server** (FastAPI) - AI智能查询服务和地理数据处理

## 关键技术决策
- **前端框架**: Vue.js 3 + Composition API - 选择基于其响应式系统和组件化优势
- **地图引擎**: OpenLayers - 选择基于其开源特性和丰富的地理功能
- **后端框架**: Spring Boot - 选择基于其成熟的企业级支持和 RESTful 能力
- **AI服务框架**: FastAPI + LangGraph - 选择基于其高性能和现代AI架构
- **数据格式**: GeoJSON + WKT - 标准地理数据格式确保互操作性

## 设计模式应用

### 前端模式
- **组件化架构**: 使用 Vue 组件实现模块化开发
- **状态管理**: Pinia 用于全局状态管理
- **依赖注入**: 通过 provide/inject 实现组件间通信
- **地图工具模式**: 独立的 mapUtils.js 提供地图操作工具函数

### 后端模式
- **分层架构**: Controller-Service-Repository 分层
- **RESTful API**: 遵循 REST 原则设计接口
- **数据访问**: MyBatis 用于数据库操作
- **动态表处理**: 支持动态空间表查询

### Sight Server AI架构
- **LangGraph工作流**: 基于状态机的多步查询处理
- **处理器模式**: 分离SQL生成、执行、解析、答案生成等职责
- **Memory机制**: 短期和长期记忆支持会话上下文
- **Checkpoint机制**: 断点续传和状态持久化
- **Fallback策略**: 智能错误处理和重试机制

## Sight Server核心架构

### 工作流节点设计
```python
# LangGraph工作流节点序列
fetch_schema → analyze_intent → enhance_query → generate_sql → 
execute_sql → check_results → generate_answer → handle_error
```

### 关键组件关系
```
SQLQueryAgent (主控制器)
├── AgentNodes (工作流节点)
│   ├── fetch_schema - 获取数据库Schema
│   ├── analyze_intent - 分析查询意图
│   ├── enhance_query - 增强查询文本
│   ├── generate_sql - 生成SQL查询
│   ├── execute_sql - 执行SQL查询
│   ├── check_results - 检查结果完整性
│   ├── generate_answer - 生成最终答案
│   └── handle_error - 错误处理和重试
├── Processors (处理器组件)
│   ├── SQLGenerator - SQL生成器
│   ├── SQLExecutor - SQL执行器
│   ├── ResultParser - 结果解析器
│   ├── AnswerGenerator - 答案生成器
│   └── SchemaFetcher - Schema获取器
├── MemoryManager - 记忆管理器
└── CheckpointManager - 检查点管理器
```

### Fallback机制设计
系统实现智能错误处理和重试机制：
- **错误分类**: 自动识别SQL语法错误、超时错误、连接错误等
- **重试策略**: 
  - `retry_sql`: 基于错误信息重新生成SQL
  - `simplify_query`: 简化查询避免超时
  - `retry_execution`: 直接重试执行
- **最大重试**: 默认5次重试，避免无限循环
- **错误信息利用**: 将错误信息包含在重新生成SQL的输入中

## 组件关系图
```
前端 (Vue App)
  ├── 地图组件 (OpenLayers)
  ├── 数据查询组件
  ├── AI 查询组件 (AgentQuery.vue)
  └── UI 组件库
        ↓ HTTP API
后端 (Spring Boot)
  ├── 控制器层 (REST endpoints)
  ├── 服务层 (业务逻辑)
  └── 数据访问层 (数据库操作)
        ↓ 数据存储
数据库 (PostGIS/MySQL)
        ↓ 数据交换
Python Sight Server (FastAPI)
  ├── SQLQueryAgent (主Agent)
  ├── LangGraph工作流
  ├── Memory管理系统
  ├── Checkpoint系统
  └── Fallback重试机制
```

## 关键接口定义
- **地图数据接口**: `/api/map/data` - 获取地理数据
- **空间查询接口**: `/api/query/spatial` - 执行空间查询
- **数据管理接口**: `/api/data/manage` - CRUD 操作
- **AI 查询接口**: `/api/agent/query` - 自然语言空间查询
- **景区数据接口**: `/api/tourist-spots` - 旅游景点 CRUD 操作
- **坐标范围查询接口**: `/postgis/WGP_db/tables/SpatialTables/{tableName}/geojson/extent` - 根据坐标范围查询空间数据
- **要素详情接口**: `/api/feature-detail/{tableName}/{id}` - 获取空间要素详细信息
- **空间表查询接口**: `/postgis/WGP_db/tables/SpatialTables/{tableName}/geojson` - 查询空间表数据
- **Sight Server API**: 
  - `GET /query` - 自然语言查询 (GET)
  - `POST /query` - 自然语言查询 (POST)
  - `POST /query/geojson` - GeoJSON格式查询
  - `POST /query/thought-chain` - 思维链查询
  - `GET /tables` - 获取数据表列表
  - `GET /database/info` - 获取数据库信息

## 性能优化策略
- **前端懒加载**: 按需加载地图图层
- **后端缓存**: Redis 用于频繁访问数据
- **数据库索引**: 空间索引优化查询性能
- **AI 查询缓存**: 缓存常见查询结果
- **地图集群**: 使用 OpenLayers 集群功能优化大量要素显示
- **视图范围查询**: 基于当前视图范围动态请求数据
- **Checkpoint机制**: 支持长时间查询的断点续传
- **Memory优化**: 学习查询模式，提高重复查询效率

## 核心文件结构
- `m_WGP_vue3/` - Vue.js 前端应用
- `be/` - Spring Boot 后端服务
- `python/sight_server/` - Sight Server AI服务
  - `core/agent.py` - SQLQueryAgent主类
  - `core/graph/` - LangGraph工作流定义
  - `core/processors/` - 处理器组件
  - `core/memory.py` - 记忆管理器
  - `core/checkpoint.py` - 检查点管理器
  - `main.py` - FastAPI应用入口
- `memory-bank/` - 项目文档和记忆库

## Sight Server技术特性
- **多步迭代查询**: 支持最多10次迭代，逐步完善查询结果
- **智能意图分析**: 自动识别查询类型（query/summary）和空间需求
- **思维链捕获**: 完整记录Agent推理过程，支持调试和学习
- **PostGIS集成**: 原生支持空间查询和地理分析
- **会话管理**: 基于conversation_id的会话上下文维护
- **状态持久化**: Checkpoint机制支持查询状态保存和恢复
- **错误恢复**: 智能Fallback机制确保查询成功率
