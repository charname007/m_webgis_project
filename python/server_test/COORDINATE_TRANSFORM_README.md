# 坐标转换功能修改说明

## 修改目标
确保每次空间查询将坐标通过ST_Transform转为WGS84坐标系下的坐标（SRID为4326）

## 修改的文件

### 1. spatial_sql_prompt.py
**修改内容：**
- 更新了所有提示词，要求AI生成的SQL查询必须包含`ST_AsGeoJSON(ST_Transform(geom, 4326))`
- 更新了示例查询模式，所有示例都包含坐标转换
- 修改了查询编写指南，明确要求使用WGS84坐标系

**具体修改：**
- `SPATIAL_SQL_SYSTEM_PROMPT`：添加了坐标转换要求
- `SQL_AGENT_SPATIAL_PROMPT`：更新了核心要求
- `SPATIAL_SYSTEM_PROMPT_SIMPLE`：简化提示词也包含转换要求
- 示例查询：所有示例都使用`ST_Transform(geom, 4326)`

### 2. geojson_utils.py
**修改内容：**
- 在`table_to_geojson`方法中添加了智能SRID检测
- 根据几何列的SRID自动决定是否使用ST_Transform
- 如果SRID不是4326且不是0（未知），则使用ST_Transform转换
- 如果SRID已经是4326或未知(0)，则直接使用ST_AsGeoJSON

**智能转换逻辑：**
```python
# 检查几何列的SRID
srid = 获取几何列的SRID

if srid and srid != 4326 and srid != 0:
    # 使用ST_Transform转换到WGS84
    geometry_expression = f"ST_AsGeoJSON(ST_Transform({geometry_column}, 4326))"
else:
    # 如果SRID已经是4326或未知(0)，直接使用ST_AsGeoJSON
    geometry_expression = f"ST_AsGeoJSON({geometry_column})"
```

### 3. server.py
**修改内容：**
- 更新了自然语言查询提示，明确要求包含坐标转换
- 修改了默认查询示例，确保包含`ST_Transform(geom, 4326)`
- 修复了代码缩进错误

**具体修改：**
- `natural_language_to_geojson`函数中的提示词更新
- `extract_sql_from_result`函数中的默认查询示例更新

## 功能验证

### 测试结果
1. **提示词修改验证**：✓ 所有提示词已正确包含坐标转换要求
2. **SQL生成验证**：✓ AI生成的SQL查询包含`ST_Transform(geom, 4326)`
3. **智能转换验证**：✓ 系统能根据SRID自动决定是否转换

### 测试脚本
使用`test_coordinate_transform.py`进行验证：
```bash
cd python
python test_coordinate_transform.py
```

## 处理特殊情况

### 1. 未知SRID（SRID=0）
当几何数据的SRID为0（未知）时，系统会：
- 直接使用`ST_AsGeoJSON(geom)`而不进行转换
- 避免`ST_Transform`错误

### 2. 不同几何列名
系统能处理不同的几何列名（如`geom`、`element_location`等）

### 3. 已为WGS84的数据
如果几何数据已经是WGS84坐标系（SRID=4326），系统会：
- 直接使用`ST_AsGeoJSON(geom)`而不进行不必要的转换

## 使用示例

### 自然语言查询
```python
# 查询会自动包含坐标转换
result = natural_language_to_geojson("查询所有建筑")
# 生成的SQL会包含：ST_AsGeoJSON(ST_Transform(geom, 4326))
```

### 直接表查询
```python
# 自动智能转换
generator = GeoJSONGenerator(connection_string)
geojson = generator.table_to_geojson("whupoi", limit=10)
```

## 注意事项

1. **SRID检测**：系统会先检测几何列的SRID，再决定是否转换
2. **错误处理**：如果转换失败，系统会回退到直接使用原始几何数据
3. **性能优化**：避免对已经是WGS84的数据进行不必要的转换

## 总结

通过本次修改，系统现在能够：
- 智能检测几何数据的坐标系
- 自动将非WGS84坐标转换为WGS84（SRID 4326）
- 确保所有空间查询结果都使用标准的地理坐标系
- 提供一致的GeoJSON输出格式
