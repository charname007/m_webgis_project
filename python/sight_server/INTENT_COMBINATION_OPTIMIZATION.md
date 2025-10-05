# 意图组合优化总结

## 修复日期
2025-10-04

## 问题描述

### 原始问题
"武汉市景区的空间分布" 查询返回结果不符合预期：

**实际返回：**
```json
{
  "intent_type": "summary",
  "is_spatial": true,
  "data": [{"count": 56}]  // ❌ 只有总数，无法显示空间分布
}
```

**用户期望：**
```json
{
  "data": [
    {"district": "武昌区", "count": 15, "center_lng": 114.296, "center_lat": 30.546},
    {"district": "洪山区", "count": 12, "center_lng": 114.385, "center_lat": 30.553},
    // ... 按区域分组的统计数据
  ]
}
```

### 根本原因
**Summary + Spatial 组合查询**的 SQL 生成逻辑不完善：
- LLM 只生成简单的 `COUNT(*)` 查询
- 没有包含空间维度的统计信息（如区域分组、坐标中心等）

---

## 修复方案

### 1. 添加意图组合决策表

**位置：** `core/processors/sql_generator.py:55-68`

```
┌─────────────┬─────────────┬──────────────────────────────┬────────────────────────────┐
│ intent_type │ is_spatial  │ 查询示例                     │ SQL 结构要求               │
├─────────────┼─────────────┼──────────────────────────────┼────────────────────────────┤
│ query       │ False       │ "查询浙江省的5A景区"         │ json_agg + 完整字段        │
│ query       │ True        │ "距离西湖10公里内的景区"     │ json_agg + 坐标 + 空间过滤 │
│ summary     │ False       │ "统计浙江省有多少景区"       │ COUNT/AVG + 可选GROUP BY   │
│ summary     │ True ⭐     │ "武汉市景区的空间分布"       │ GROUP BY + 空间字段        │
└─────────────┴─────────────┴──────────────────────────────┴────────────────────────────┘
```

**作用：** 为 LLM 提供清晰的决策指南

---

### 2. 优化 Summary + Spatial 提示词示例

**位置：** `core/processors/sql_generator.py:98-171`

#### 示例1：按行政区分组统计（⭐ 推荐）
```sql
SELECT
  COALESCE(a."所属行政区", '未知') as district,
  COUNT(*) as count,
  AVG(a.lng_wgs84) as center_lng,  -- ⭐ 区域中心经度
  AVG(a.lat_wgs84) as center_lat   -- ⭐ 区域中心纬度
FROM a_sight a
WHERE a."所属城市" = '武汉市'
  AND a.lng_wgs84 IS NOT NULL
  AND a.lat_wgs84 IS NOT NULL
GROUP BY a."所属行政区"
ORDER BY count DESC
```

#### 示例2：按景区等级分组
```sql
SELECT
  a.level,
  COUNT(*) as count,
  AVG(a.lng_wgs84) as center_lng,
  AVG(a.lat_wgs84) as center_lat
FROM a_sight a
WHERE a."所属城市" = '武汉市'
  AND a.lng_wgs84 IS NOT NULL
GROUP BY a.level
ORDER BY a.level
```

#### 示例3：空间范围统计（边界框）
```sql
SELECT
  COUNT(*) as total_count,
  MIN(lng_wgs84) as bbox_min_lng,  -- 西边界
  MAX(lng_wgs84) as bbox_max_lng,  -- 东边界
  MIN(lat_wgs84) as bbox_min_lat,  -- 南边界
  MAX(lat_wgs84) as bbox_max_lat,  -- 北边界
  AVG(lng_wgs84) as center_lng,    -- 中心点经度
  AVG(lat_wgs84) as center_lat     -- 中心点纬度
FROM a_sight
WHERE "所属城市" = '武汉市' AND lng_wgs84 IS NOT NULL
```

#### 示例4：高级空间分析（ST_GeoHash）
```sql
SELECT
  ST_GeoHash(lng_wgs84, lat_wgs84, 4) as grid_id,
  COUNT(*) as count,
  AVG(lng_wgs84) as center_lng,
  AVG(lat_wgs84) as center_lat
FROM a_sight
WHERE "所属城市" = '武汉市'
  AND lng_wgs84 IS NOT NULL
GROUP BY ST_GeoHash(lng_wgs84, lat_wgs84, 4)
ORDER BY count DESC
```

#### 错误示例（明确禁止）
```sql
-- ❌ 错误："空间分布"查询不能只返回总数
SELECT COUNT(*) as count
FROM a_sight
WHERE "所属城市" = '武汉市'
```

---

### 3. 增强 SQL 验证规则

**位置：** `core/processors/sql_generator.py:800-898`

#### 支持的空间统计方式
- ✅ `AVG(lng_wgs84)`, `AVG(lat_wgs84)` - 中心点坐标
- ✅ `MIN/MAX(lng_wgs84/lat_wgs84)` - 边界框范围
- ✅ `ROUND(lng_wgs84)` - 密度分析
- ✅ `ST_GeoHash`, `ST_Collect`, `ST_Centroid` - PostGIS 函数
- ✅ `GROUP BY 行政区/level/province` - 分组统计

#### 验证逻辑
```python
# 空间统计查询必须包含空间维度
if is_spatial:
    # 1. 检查是否包含空间字段（经纬度）
    has_spatial_fields = any(keyword in sql_lower for keyword in
                             ['lng_wgs84', 'lat_wgs84', ...])

    # 2. 检查是否包含空间聚合或分组
    spatial_aggregation_patterns = [
        r'avg\(.*?lng',           # AVG(lng_wgs84)
        r'avg\(.*?lat',           # AVG(lat_wgs84)
        r'min\(.*?lng',           # MIN(lng_wgs84)
        r'max\(.*?lng',           # MAX(lng_wgs84)
        r'group by.*?行政区',     # GROUP BY 行政区
        ...
    ]

    # 3. 严格禁止：只有 COUNT(*) 而没有空间维度
    if 'count(*)' in sql_lower:
        # 必须同时包含空间聚合字段或 GROUP BY
        if not has_spatial_agg_fields and not has_group_by:
            return (False, "空间统计查询不能只返回 COUNT(*)")
```

---

### 4. 修复的 Bug

**Bug：** 提示词模板中的 Python 语法错误

**位置：** `core/processors/sql_generator.py:68`

**错误代码：**
```python
**当前查询属于**: {intent_type} + {"空间" if is_spatial else "非空间"} → ...
```

**修复后：**
```python
**当前查询属于**: {intent_type} + {spatial_type} → ...
```

**变更：**
1. 将 Python 条件表达式改为模板变量 `{spatial_type}`
2. 在 `input_variables` 中添加 `spatial_type`
3. 在 `.format()` 调用时传递 `spatial_type = "空间" if is_spatial else "非空间"`

---

## 测试结果

### 测试文件
`tests/test_summary_spatial_validation.py`

### 测试用例（7个，全部通过✅）

| # | 测试类型 | 测试内容 | 结果 |
|---|---------|---------|------|
| 1 | 正确 SQL | 按行政区分组 + 空间中心 | ✅ 通过 |
| 2 | 正确 SQL | 按等级分组 + 空间中心 | ✅ 通过 |
| 3 | 正确 SQL | 空间范围统计（边界框） | ✅ 通过 |
| 4 | 正确 SQL | 高级空间分析（ST_GeoHash） | ✅ 通过 |
| 5 | 错误 SQL | 只有 COUNT(*)（应被拒绝） | ✅ 通过 |
| 6 | 错误 SQL | 没有空间字段（应被拒绝） | ✅ 通过 |
| 7 | 普通统计 | 非空间统计查询 | ✅ 通过 |

**测试结果：** 7 通过, 0 失败 🎉

---

## 预期效果

### 修复前
```json
{
  "intent_type": "summary",
  "is_spatial": true,
  "data": [{"count": 56}]  // ❌ 只有总数
}
```

### 修复后
```json
{
  "intent_type": "summary",
  "is_spatial": true,
  "data": [
    {"district": "武昌区", "count": 15, "center_lng": 114.296, "center_lat": 30.546},
    {"district": "洪山区", "count": 12, "center_lng": 114.385, "center_lat": 30.553},
    {"district": "江岸区", "count": 10, "center_lng": 114.301, "center_lat": 30.598},
    {"district": "江汉区", "count": 8, "center_lng": 114.273, "center_lat": 30.603},
    // ... 其他区域
  ]
}
```

✅ **前端现在可以在地图上正确显示每个区域的景区分布了！**

---

## 修改的文件

### 1. `core/processors/sql_generator.py`

**变更内容：**
- 添加意图组合决策表（第55-68行）
- 优化 Summary + Spatial 提示词示例（第98-171行）
- 增强 SQL 验证规则（第800-898行）
- 修复模板语法错误（第68行、273行、377-392行）

**变更行数：** 约 150 行

### 2. `tests/test_summary_spatial_validation.py` （新增）

**内容：**
- 7 个测试用例验证修复效果
- 测试正确的空间统计 SQL
- 测试错误的空间统计 SQL
- 测试普通统计 SQL

**代码行数：** 233 行

---

## 4 种意图组合完整支持

| intent_type | is_spatial | 查询示例 | SQL 结构 | 状态 |
|-------------|------------|----------|----------|------|
| query | False | "查询浙江省的5A景区" | `json_agg + 完整字段` | ✅ 已优化 |
| query | True | "距离西湖10公里内的景区" | `json_agg + 坐标 + 空间过滤` | ✅ 已优化 |
| summary | False | "统计浙江省有多少景区" | `COUNT/AVG + 可选GROUP BY` | ✅ 已优化 |
| summary | True | "武汉市景区的空间分布" | `GROUP BY + 空间字段` | ✅ **本次修复** |

---

## 关键要点

### 1. Summary + Spatial 查询的核心原则
- ✅ **必须返回空间维度的统计**（不能只有总数）
- ✅ **推荐使用 GROUP BY + 空间字段**（按区域/等级分组）
- ✅ **必须包含空间信息**（中心坐标、边界范围等）
- ❌ **禁止只返回简单的 COUNT(*)**

### 2. 验证规则的灵活性
支持多种空间统计方式：
- 按区域分组（行政区、城市、省份）
- 按属性分组（景区等级、类型）
- 空间范围统计（边界框、中心点）
- 高级空间分析（地理网格、密度分析）

### 3. 错误处理
- 自动验证生成的 SQL 结构
- 检测并拒绝不符合规则的 SQL
- 提供清晰的错误信息

---

## 后续优化建议

### 1. 前端展示优化
- 按区域分组的数据可用于：
  - **地图热力图**（各区域景区密度）
  - **分区显示**（每个区域的中心点 marker）
  - **统计图表**（柱状图、饼图等）

### 2. 更多空间分析功能
- 距离矩阵分析
- 空间聚类（K-means、DBSCAN）
- 路径规划优化
- 可达性分析

### 3. 性能优化
- 对于大数据集，考虑使用物化视图
- 缓存常用的空间统计结果
- 使用空间索引加速查询

---

## 参考文档

1. **项目架构文档：** `CLAUDE.md`
2. **查询意图分析：** `INTENT_OPTIMIZATION_SUMMARY.md`
3. **测试用例：** `tests/test_summary_spatial_validation.py`
4. **SQL 生成器：** `core/processors/sql_generator.py`

---

*文档版本：1.0*
*创建日期：2025-10-04*
*作者：Claude Code*
