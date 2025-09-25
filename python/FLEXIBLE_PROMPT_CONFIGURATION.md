# 灵活的空间数据库提示词配置

## 概述

本项目成功实现了灵活的空间数据库提示词配置系统，使得SQL查询代理能够知道它正在访问的是一个空间数据库，并且能够充分利用PostGIS及其扩展提供的查询和功能。

## 实现的功能

### 1. 重构SQLQueryAgent以支持可配置的系统提示词

- 修改了 `sql_query_agent.py`，使其支持传入自定义的系统提示词
- 保持了向后兼容性，不传入提示词时使用默认配置
- 支持灵活的系统提示词配置

### 2. 创建专门的空间数据库查询代理子类

- 在 `spatial_sql_prompt.py` 中创建了 `SpatialSQLQueryAgent` 类
- 提供了专门的空间数据库提示词配置
- 包含完整的PostGIS函数说明和查询指南

### 3. 修改server.py以使用新的配置方式

- 添加了配置选项 `USE_SPATIAL_PROMPT = True`
- 修改了 `initialize_agent()` 函数，根据配置选择使用空间数据库提示词或默认提示词
- 支持两种使用方式：
  - 方式1：使用空间数据库查询代理子类
  - 方式2：直接在SQLQueryAgent中传入空间提示词

### 4. 提供多种提示词配置

#### 详细的空间数据库提示词 (SPATIAL_SQL_SYSTEM_PROMPT)
- 完整的PostGIS功能说明
- 详细的查询编写指南
- 丰富的示例查询模式

#### 简化的空间提示词 (SPATIAL_SYSTEM_PROMPT_SIMPLE)
- 适合直接在server.py中使用
- 简洁明了的核心要求
- 包含必要的空间数据库信息

#### SQL代理专用提示词 (SQL_AGENT_SPATIAL_PROMPT)
- 专门为SQL查询代理设计
- 强调空间查询的核心要求
- 确保生成的SQL包含几何数据

## 配置方式

### 在server.py中配置

```python
# 配置选项：是否使用空间数据库提示词
USE_SPATIAL_PROMPT = True  # 设置为True使用空间数据库提示词，False使用默认提示词

def initialize_agent() -> bool:
    if USE_SPATIAL_PROMPT:
        # 方式1：使用空间数据库查询代理子类
        # sql_query_agent = SpatialSQLQueryAgent()
        
        # 方式2：直接在SQLQueryAgent中传入空间提示词
        sql_query_agent = SQLQueryAgent(system_prompt=SPATIAL_SYSTEM_PROMPT_SIMPLE)
    else:
        # 使用默认提示词
        sql_query_agent = SQLQueryAgent()
```

### 直接使用空间数据库代理

```python
from spatial_sql_prompt import SpatialSQLQueryAgent

agent = SpatialSQLQueryAgent()
result = agent.run("查询包含几何数据的表")
```

### 自定义提示词配置

```python
from sql_query_agent import SQLQueryAgent
from spatial_sql_prompt import SQL_AGENT_SPATIAL_PROMPT

agent = SQLQueryAgent(system_prompt=SQL_AGENT_SPATIAL_PROMPT)
result = agent.run("查询包含几何数据的表")
```

## 空间数据库提示词内容

### 数据库环境信息
- 数据库类型：PostgreSQL with PostGIS extension
- 数据库名称：WGP_db
- 主要包含空间数据表，如whupoi等
- 几何列通常命名为"geom"

### PostGIS功能说明
- 几何转换函数（ST_AsGeoJSON, ST_AsText等）
- 空间关系函数（ST_Intersects, ST_Contains等）
- 几何操作函数（ST_Area, ST_Length等）
- 几何属性函数（ST_GeometryType, ST_SRID等）

### 查询编写指南
1. 空间查询必须包含几何数据
2. 处理不同类型的几何（点、线、面）
3. 空间分析查询（距离、关系、缓冲区等）
4. 性能优化建议

## 测试验证

创建了测试脚本 `test_flexible_config.py` 来验证新的配置方式：

1. 测试默认提示词配置
2. 测试空间数据库提示词配置
3. 测试空间数据库查询代理子类
4. 测试简化空间提示词

测试结果显示所有配置方式都能正常工作，并且能够正确识别空间数据库相关内容。

## 优势

1. **灵活性**：支持多种配置方式，可根据需求选择
2. **专业性**：提供专门的空间数据库提示词，提高查询质量
3. **兼容性**：保持向后兼容，不影响现有功能
4. **可扩展性**：易于添加新的提示词配置
5. **易用性**：简单的配置选项，易于理解和修改

## 使用建议

1. 对于空间数据库查询，建议启用 `USE_SPATIAL_PROMPT = True`
2. 可以根据具体需求选择合适的提示词配置
3. 定期更新提示词内容以反映数据库结构的变化
4. 监控查询结果，确保空间数据库功能被正确使用

## 文件结构

```
python/
├── sql_query_agent.py          # 重构的支持可配置提示词的SQL查询代理
├── spatial_sql_prompt.py       # 空间数据库专用的提示词配置
├── server.py                   # 修改后的服务器，支持灵活配置
├── test_flexible_config.py     # 测试脚本
└── FLEXIBLE_PROMPT_CONFIGURATION.md  # 本文档
```

通过这个灵活的配置系统，SQL查询代理现在能够充分了解它正在访问的是一个空间数据库，并能够利用PostGIS的强大功能来生成更准确、更高效的空间查询。
