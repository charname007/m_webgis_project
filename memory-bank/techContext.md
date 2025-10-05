# 技术上下文

## 技术栈概述
本项目采用全栈 JavaScript + Java + Python 技术栈，专注于地理信息处理和高性能 Web 应用，集成 AI 技术增强用户体验。

### 前端技术
- **框架**: Vue.js 3 + Composition API
- **地图引擎**: OpenLayers 9.x
- **构建工具**: Vite
- **包管理器**: npm
- **状态管理**: Pinia
- **UI 组件**: 自定义组件
- **语言**: JavaScript
- **关键组件**: 
  - `OlMap.vue` - 主地图组件
  - `AgentQuery.vue` - AI 查询组件
  - `mapUtils.js` - 地图工具函数

### 后端技术
- **框架**: Spring Boot 3.x
- **语言**: Java 17+
- **数据库**: PostgreSQL with PostGIS 扩展
- **ORM**: MyBatis
- **JPA**: Jakarta Persistence API
- **API 文档**: Swagger/OpenAPI
- **构建工具**: Maven
- **关键组件**:
  - `MapController.java` - 地图数据接口
  - `QueryController.java` - 查询接口
  - `DynamicTableController.java` - 动态表处理
  - `TouristSpotController.java` - 旅游景点 CRUD 接口
  - `FeatureDetailController.java` - 要素详情接口
  - `SpatialTableController.java` - 空间表查询接口

### Sight Server AI服务技术
- **语言**: Python 3.x
- **Web 框架**: FastAPI - 高性能异步Web框架
- **AI 框架**: LangChain + LangGraph - 构建多步AI工作流
- **数据库**: PostgreSQL with PostGIS - 空间数据库支持
- **关键组件**:
  - `SQLQueryAgent` - 主Agent类，集成LangGraph工作流
  - `AgentNodes` - 工作流节点定义
  - `GraphEdges` - 状态转换边定义
  - `Processors` - 处理器组件（SQL生成、执行、解析等）
  - `MemoryManager` - 记忆管理器
  - `CheckpointManager` - 检查点管理器
- **核心特性**:
  - 多步迭代查询（最多10次迭代）
  - 智能意图分析和查询增强
  - 思维链捕获和调试支持
  - 智能Fallback错误处理机制
  - 会话管理和状态持久化

### 数据处理技术
- **语言**: Python 3.x
- **地理处理库**: GeoPandas, Shapely, Fiona
- **数据格式**: GeoJSON, WKT, Shapefile
- **关键组件**:
  - `geojson_utils.py` - GeoJSON 处理工具

### 开发环境
- **IDE**: VS Code (前端) + IntelliJ IDEA (后端)
- **版本控制**: Git + GitHub
- **操作系统**: Windows/Linux/macOS 跨平台支持
- **数据库管理**: pgAdmin 或 DBeaver

### 依赖管理
- **前端依赖**: 通过 package.json 管理
- **后端依赖**: 通过 pom.xml 管理
- **Python 依赖**: 通过 requirements.txt

### 工具和配置
- **代码格式化**: Prettier + ESLint (前端)
- **代码质量**: SonarQube 或类似工具
- **持续集成**: GitHub Actions
- **部署**: Docker + Kubernetes (计划中)

### 关键配置
- **地图配置**: OpenLayers 视图设置、投影系统
- **API 配置**: CORS 设置、安全配置
- **数据库配置**: 连接池、空间索引优化
- **AI 配置**: LangChain 代理配置、提示工程
- **环境配置**: 开发/生产环境自动切换，零硬编码后端地址

### 开发实践
- **代码风格**: 遵循 Airbnb JavaScript 风格指南
- **提交规范**: Conventional Commits
- **测试策略**: Jest (前端) + JUnit (后端) + pytest (Python)
- **文档**: JSDoc + JavaDoc + Markdown

### 关键技术特性
- **空间索引**: 使用 PostGIS 空间索引优化查询性能
- **坐标转换**: 支持多种坐标系统转换
- **AI 查询解析**: 自然语言到空间 SQL 的智能转换
- **动态表处理**: 支持动态空间数据表的查询和管理
- **GeoJSON 标准化**: 确保地理数据格式的统一性
- **地图集群**: 使用 OpenLayers 集群功能优化大量要素显示
- **视图范围查询**: 基于当前视图范围动态请求数据
- **智能图层管理**: 根据缩放级别动态显示不同等级的数据
