# 空间数据库和PostGIS系统提示词配置

## 概述

本项目已成功配置了专门针对空间数据库和PostGIS的系统提示词，使得SQL查询代理能够理解并处理地理空间数据。

## 配置文件

### 1. 空间数据库提示词文件 (`spatial_sql_prompt.py`)

包含两个主要的提示词配置：

#### SPATIAL_SQL_SYSTEM_PROMPT
- 详细的系统提示词，包含PostGIS函数说明、查询编写指南、示例查询模式
- 涵盖了几何转换、空间关系、几何操作、几何属性等PostGIS核心功能
- 提供了性能优化建议和最佳实践

#### SQL_AGENT_SPATIAL_PROMPT
- 简化的提示词，专门用于SQL查询代理
- 强调空间查询必须包含几何数据和使用PostGIS函数

### 2. 修改的SQL查询代理 (`sql_query_agent.py`)

已修改SQLQueryAgent类，使其使用专门的空间数据库提示词：

```python
# 创建包含空间数据库知识的系统提示词
spatial_system_prompt = ChatPromptTemplate.from_messages([
    ("system", SQL_AGENT_SPATIAL_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

# 重新配置LLM的提示词
self.llm.prompt = spatial_system_prompt
```

## 功能特性

### 已实现的功能

1. **空间数据库识别**：代理能够识别包含几何数据的表
2. **PostGIS函数使用**：代理会使用ST_AsGeoJSON、ST_Distance、ST_Intersects等PostGIS函数
3. **几何数据处理**：代理理解点、线、面等几何类型
4. **空间查询生成**：能够生成包含几何数据的SQL查询

### 支持的PostGIS功能

- **几何转换**：ST_AsGeoJSON, ST_AsText, ST_GeomFromText
- **空间关系**：ST_Intersects, ST_Contains, ST_Within, ST_Distance
- **几何操作**：ST_Area, ST_Length, ST_Centroid, ST_Buffer
- **几何属性**：ST_GeometryType, ST_SRID, ST_NumGeometries

## 测试验证

通过测试脚本验证了以下功能：

1. ✅ 代理能够识别空间数据表（county, edges, faces, state, tract, zcta5等）
2. ✅ 代理使用PostGIS函数进行空间查询
3. ✅ 代理理解几何数据类型和空间参考系统
4. ✅ 代理能够生成包含几何数据的SQL查询

## 使用示例

### 自然语言查询示例

- "查询所有的点数据"
- "查找距离某个点1000米范围内的所有要素"
- "查询包含几何数据的表"
- "生成一个包含ST_AsGeoJSON的查询"

### 生成的SQL查询示例

```sql
-- 基本空间查询
SELECT gid, name, ST_AsGeoJSON(geom) as geometry 
FROM whupoi 
WHERE geom IS NOT NULL 
LIMIT 10

-- 距离查询
SELECT gid, name, ST_Distance(geom, ST_GeomFromText('POINT(114.0 30.5)')) as distance
FROM whupoi 
WHERE ST_DWithin(geom, ST_GeomFromText('POINT(114.0 30.5)'), 1000)
ORDER BY distance ASC
LIMIT 10
```

## 数据库连接信息

- **数据库类型**：PostgreSQL with PostGIS extension
- **数据库名称**：WGP_db
- **连接字符串**：postgresql://sagasama:cznb6666@localhost:5432/WGP_db
- **主要空间表**：whupoi, whupois, edges, county, state等

## 注意事项

1. **几何列命名**：默认几何列名为"geom"，部分表使用"the_geom"
2. **空间参考系统**：部分表使用SRID 4269（NAD83），部分表使用SRID 0（未定义）
3. **查询性能**：对于大数据集，建议使用空间索引和合理的LIMIT限制

## 后续优化建议

1. 添加更多空间分析功能的提示词
2. 优化复杂空间查询的性能提示
3. 增加对特定业务场景的空间查询模板
4. 完善错误处理和边界情况处理

这个配置使得SQL查询代理具备了专业的空间数据库查询能力，能够有效地处理地理空间数据相关的自然语言查询。
