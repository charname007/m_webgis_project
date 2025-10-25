# 当前活跃上下文

## 当前开发重点
项目目前主要专注于以下领域：
- **Sight Server AI服务完善** - 完善基于LangGraph的多步查询Agent
- **AI 智能查询功能开发** - 完善自然语言空间查询功能
- **地图工具函数优化** - 优化 mapUtils.js 中的地图操作工具
- **前后端数据集成** - 确保 Vue 前端与 Spring Boot 后端的数据同步
- **Python AI 代理完善** - 优化空间 SQL 智能代理的准确性和性能
- **视图范围获取功能** - 新增获取当前视图坐标范围的工具函数
- **GeoJSON 数据合并功能** - 新增 addGeoJsonToLayer 函数用于将 GeoJSON 要素添加到现有图层
- **地图范围限制功能** - 新增中国范围限制功能，限制地图显示在中国境内
- **记忆库维护** - 保持项目文档的准确性和完整性
- **集群功能优化** - 完善地图要素集群显示和交互功能

## 近期变更
**2025-10-25** - 记忆库更新：
- 完成记忆库全面检查和更新
- 验证所有记忆库文件的完整性和准确性
- 更新项目状态和进展信息
- 确保技术文档与当前实现保持一致

**2025-10-10** - 记忆库更新：
- 完成记忆库全面检查和更新
- 验证所有记忆库文件的完整性和准确性
- 更新项目状态和进展信息
- 确保技术文档与当前实现保持一致

**2025-10-09** - Sight Server 功能增强：
- 优化了 LangGraph 工作流节点和边定义
- 完善了意图分析、SQL生成、SQL执行、验证等核心节点
- 增强了错误处理和重试机制
- 优化了提示词模板和配置
- 创建了多个测试脚本验证功能完整性

**2025-10-05** - 缓存管理器修复：
- 启用语义搜索功能（`enable_semantic_search=True`）
- 为 GET `/query` 端点添加缓存逻辑，与 POST 端点保持一致
- 新增缓存统计 API 端点：`GET /cache/stats` 和 `DELETE /cache/clear`
- 修复缓存键生成策略，支持跨会话共享缓存
- 创建缓存功能测试脚本 `test_cache_functionality.py`
- 优化缓存命中日志输出，便于调试和监控

**2025-10-04** - FULL OUTER JOIN 错误修复：
- 修复 PostgreSQL FULL OUTER JOIN 限制问题："错误: 只有在合并连接或哈希连接的查询条件中才支持FULL JOIN"
- 修改提示词模板，移除强制使用 FULL OUTER JOIN 的要求
- 实现多策略查询方案，使用 UNION ALL 策略替代 FULL OUTER JOIN
- 更新查询决策树，根据查询意图动态选择最佳连接策略
- 创建测试脚本验证修复效果
- 更新所有查询示例，使用 UNION ALL 策略获取完整数据

**2025-10-02** - 智能景区图层功能实现：
- 在 `OlMap.vue` 组件中实现智能景区图层功能
- 根据地图缩放级别动态请求和显示不同等级的景区数据
- 支持5A到1A共5个等级的景区，根据缩放级别自动显示/隐藏
- 实现地图移动结束和缩放结束时的自动数据请求
- 创建测试脚本验证缩放级别与景区等级对应关系
- 实现防抖处理避免频繁请求（300ms延迟）
- 添加美观的景区样式设计（不同等级使用不同颜色和大小）

**2025-10-02** - TouristSpot 完整 CRUD 架构实现：
- 创建 `TouristSpot` 模型类，使用 JPA 注解映射数据库字段
- 实现 `TouristSpotMapper` 数据访问层，支持完整 CRUD 操作
- 创建 `TouristSpotService` 业务逻辑层接口和实现类
- 实现 `TouristSpotController` REST API 控制器
- 提供两种名称查询方式：路径参数和查询参数，均支持模糊匹配
- 完整的错误处理和 HTTP 状态码返回
- 支持跨域访问，便于前端调用

**2025-10-04** - 记忆库更新：
- 完成记忆库全面检查和更新
- 验证所有记忆库文件的完整性和准确性
- 更新项目状态和进展信息
- 确保技术文档与当前实现保持一致

**2025-10-03** - TouristSpotSearch 组件名称匹配问题修复：
- 修复景点名称格式不匹配问题：景点搜索结果为"中文英文"格式（如"武汉博物馆Wuhan Museum"），而asight空间表为纯中文格式
- 实现 `extractChineseName` 函数，使用正则表达式从混合名称中提取中文字符
- 修改 `handleSpotClick` 函数，使用提取的中文名称匹配asight空间表
- 修复 JSON.parse 错误，添加类型检查避免解析对象错误
- 移除高亮功能，解决高亮图层不会消失的问题
- 添加双重匹配策略：先尝试中文名称匹配，失败后回退到原始名称匹配
- 增强错误处理和详细日志输出

**2025-10-02** - TouristSpotSearch 组件实现：
- 创建 `TouristSpotSearch.vue` 组件，提供景区搜索功能
- 支持输入名称查询景区，返回分页的查询结果
- 显示景区详细信息，包括地址、评分、门票、开放时间等
- 点击景区项自动跳转到地图对应位置
- 集成 `ASightController` 获取景区坐标数据
- 与 `mapUtils` 集成进行地图跳转和缩放
- 实现防抖搜索和分页控制

**2025-10-01** - FeatureDetail功能实现：
- 重命名DynamicTable相关组件为SpatialTable（Controller、Service、Mapper）
- 新增FeatureDetail功能模块，专门用于查询空间要素的详细信息
- 创建FeatureDetailRequest和FeatureDetailResponse数据模型
- 实现FeatureDetailMapper接口和XML配置，支持要素详情查询
- 实现FeatureDetailService业务逻辑层，包含图片URL自动提取功能
- 实现FeatureDetailController REST API 控制器
- 支持通过路径参数和请求体两种方式查询要素详情
- 自动检测和提取图片URL，支持前端直接加载图片

**2025-10-01** - 坐标范围查询功能实现：
- 新增 `SpatialExtentRequest` 模型类，用于处理坐标范围查询请求
- 实现后端坐标范围查询 API 端点：`POST /postgis/WGP_db/tables/SpatialTables/{tableName}/geojson/extent`
- 新增 Service 层方法 `getSpatialTableGeojsonByExtent`，包含表名验证和坐标范围验证
- 实现 Mapper 层 SQL 查询，使用 PostGIS 的 `ST_Intersects` 和 `ST_MakeEnvelope` 函数
- 支持动态几何字段检测（map_elements 表使用 element_location，其他表使用 geom）
- 添加坐标范围合理性检查，防止查询范围过大

**2025-10-01** - 环境配置系统实现：
- 完成开发环境和生产环境的自动切换配置
- 前端：优化 `.env.development` 和 `.env.production` 配置文件
- 后端：完善 `application-dev.properties` 和 `application-prod.properties` 配置
- 实现零硬编码后端地址，全部通过环境变量配置
- 开发环境使用 `localhost:8081`，生产环境使用服务器公网IP
- 创建部署指南文档和测试脚本

**2025-10-01** - 记忆库更新：
- 完成记忆库系统全面检查和更新
- 验证所有记忆库文件的完整性和准确性
- 更新项目状态和进展信息
- 确保技术文档与当前实现保持一致

**2025-09-30** - 项目状态更新：
- 基础项目架构已搭建完成
- 前端 Vue.js 3 应用结构已创建
- 后端 Spring Boot 服务基础框架已实现
- Python AI 查询代理组件已开发
- 记忆库文档系统已建立

## 当前挑战
1. **AI 查询准确性** - 需要提高自然语言到空间 SQL 的转换准确率
2. **地图性能优化** - 优化 OpenLayers 地图加载和渲染性能
3. **数据格式统一** - 确保前后端地理数据格式的一致性
4. **组件集成** - 将 AI 查询功能无缝集成到前端界面
5. **文档维护** - 保持记忆库与项目进展同步
6. **缓存管理器优化** - 确保语义搜索缓存正常工作

## 下一步计划
1. **完善 AI 查询功能** - 优化 Python 空间 SQL 代理的提示工程
2. **前端组件开发** - 完成 AgentQuery.vue 组件的功能实现
3. **地图工具增强** - 扩展 mapUtils.js 中的地图操作功能
4. **API 接口测试** - 测试前后端接口的完整性和稳定性
5. **性能基准测试** - 建立系统性能基准指标
6. **记忆库维护** - 定期更新项目文档和进展

## 技术动态
- **AI 技术集成** - 正在使用 LangChain 和 LangGraph 构建智能查询代理
- **空间数据处理** - 使用 PostGIS 进行高效空间查询
- **前端地图交互** - 基于 OpenLayers 实现丰富的地图交互功能
- **模块化架构** - 采用前后端分离的微服务架构
- **文档自动化** - 建立记忆库维护流程

## 关键关注点
⚠️ **AI 查询准确性** - 需要持续优化提示工程和查询解析
⚠️ **地图性能** - 需要监控地图加载和渲染性能
⚠️ **数据一致性** - 确保前后端数据格式和坐标系统一致
⚠️ **用户体验** - 提供流畅的自然语言查询体验
⚠️ **文档同步** - 保持记忆库与项目进展实时同步

## 近期里程碑
- **本周内**: 完成 AI 查询功能的基本集成
- **下周**: 实现完整的前后端数据流
- **下下周**: 进行系统集成测试和性能优化
- **持续**: 定期更新记忆库文档

## 项目架构确认
通过全面浏览项目，确认以下架构细节：

### Sight Server 架构
- **核心组件**: `SQLQueryAgent` 基于 LangGraph 的多步查询Agent
- **工作流**: fetch_schema → analyze_intent → enhance_query → generate_sql → execute_sql → check_results → generate_answer → handle_error
- **关键特性**: Memory机制、Checkpoint机制、Fallback重试机制、缓存管理
- **API端点**: `/query`, `/query/geojson`, `/query/thought-chain`, `/tables`, `/database/info`

### Vue 前端架构
- **核心组件**: `OlMap.vue` (主地图组件), `AgentQuery.vue` (AI查询组件), `TouristSpotSearch.vue` (景区搜索组件)
- **地图引擎**: OpenLayers 9.x 集成
- **状态管理**: 使用 Vue 3 Composition API 和 provide/inject
- **图片缓存**: 实现图片加载和缓存系统，支持景区图片显示

### Spring Boot 后端架构
- **技术栈**: Spring Boot 3.5.5 + Java 21 + MyBatis + PostgreSQL + PostGIS
- **核心控制器**: MapController, QueryController, SpatialTableController, TouristSpotController, FeatureDetailController
- **数据访问**: 使用 MyBatis 和 JPA 进行数据库操作
- **空间查询**: 集成 PostGIS 支持空间查询和坐标范围查询

### 项目文件结构确认
- `m_WGP_vue3/` - Vue.js 3 前端应用
- `be/` - Spring Boot 后端服务  
- `python/sight_server/` - Sight Server AI服务
- `memory-bank/` - 项目文档和记忆库
- `cache/` - 缓存数据
- `checkpoints/` - LangGraph 检查点数据
- `logs/` - 系统日志
