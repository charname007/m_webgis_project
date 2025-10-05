# LLM 自主决策能力增强总结

**日期**: 2025-10-04
**版本**: 2.1.0
**状态**: ✅ 已完成

---

## 📋 概述

本次增强旨在让 LLM 能够根据查询意图**自主判断**并选择最佳的 SQL 生成策略，无需人工干预。

### 核心目标
1. ✅ **自主选择最佳 JOIN 策略**（UNION ALL / LEFT JOIN）
2. ✅ **根据查询意图自动调整 SQL 结构**（Query vs Summary）
3. ✅ **智能处理数据完整性问题**（获取所有数据，不遗漏记录）
4. ✅ **自动应用安全防护**（评分字段的 CASE 处理）
5. ✅ **修复 UNION ALL 策略的 FROM 子句错误**（外层字段引用问题）

---

## 🎯 实施内容

### 1. 增强提示词 - 添加智能决策系统

**文件**: `core/prompts.py`
**位置**: 第 92-314 行

#### 新增内容：

##### 🤖 智能 SQL 生成决策系统

**决策流程图**：
```
用户查询
  ↓
【步骤1】判断查询类型
  ├─ 包含"统计/计数/多少/数量"等关键词？
  │  ├─ YES → 统计查询（不用 json_agg，直接返回 COUNT/SUM）
  │  └─ NO → 数据查询（使用 json_agg）
  ↓
【步骤2】判断数据需求（仅数据查询）
  ├─ 包含"附近/距离/周边/范围内"等空间关键词？
  │  ├─ YES → 策略B（LEFT JOIN，必须有坐标）
  │  └─ NO → 继续判断
  ├─ 强调"评分/门票/详细信息/推荐/热门"？
  │  ├─ YES → 策略C（重点详情）
  │  └─ NO → 策略A（UNION ALL，完整数据）⭐ 默认推荐
  ↓
【步骤3】应用安全防护
  ├─ 评分字段 → 必须使用 CASE 处理
  ├─ 坐标字段 → 使用 COALESCE 和 CASE
  └─ _dataSource → 添加数据来源标识
  ↓
【步骤4】生成最终 SQL
```

##### 📊 策略A：UNION ALL 三段式（⭐ 默认推荐）

**何时使用**：
- 用户要求"所有"、"全部"、"列出"景区
- 需要返回景区列表（不限定必须有坐标）
- 通用查询场景（默认策略）

**SQL 结构**（✅ 已修复外层字段引用问题）：
```sql
SELECT json_agg(
    json_build_object(
        -- ✅ 直接使用字段名（从 combined_data 中获取），不使用 a. 或 t.
        'gid', gid,
        'name', name,
        'level', level,
        'province', "所属省份",
        'city', COALESCE("所属城市", "城市"),
        '评分', CASE
            WHEN "评分" IS NULL OR "评分" = '' OR "评分" = '--' THEN NULL
            WHEN "评分" ~ '^[0-9.]+$' THEN "评分"
            ELSE NULL
        END,
        'coordinates', CASE
            WHEN lng_wgs84 IS NOT NULL THEN ARRAY[lng_wgs84, lat_wgs84]
            WHEN geom IS NOT NULL THEN ARRAY[
                ST_X(ST_Transform(geom, 4326)),
                ST_Y(ST_Transform(geom, 4326))
            ]
            ELSE NULL
        END,
        '_dataSource', CASE
            WHEN id IS NULL THEN 'a_sight_only'
            WHEN gid IS NULL THEN 'tourist_spot_only'
            ELSE 'joined'
        END
    )
) as result
FROM (
    -- 子查询1：只在 a_sight 中的数据
    SELECT a.gid, a.name, a.level, ... FROM a_sight a
    LEFT JOIN tourist_spot t ON ... WHERE t.name IS NULL

    UNION ALL

    -- 子查询2：只在 tourist_spot 中的数据
    SELECT NULL::integer as gid, ... FROM tourist_spot t
    LEFT JOIN a_sight a ON ... WHERE a.gid IS NULL

    UNION ALL

    -- 子查询3：两表都有的数据
    SELECT a.gid, a.name, ... FROM a_sight a
    INNER JOIN tourist_spot t ON ...
) combined_data
WHERE [条件]
LIMIT 10
```

**✅ 优点**：
- 获取所有数据（不会遗漏仅在某一个表中的记录）
- 避免 PostgreSQL FULL OUTER JOIN 限制
- 明确标识数据来源（_dataSource 字段）
- 外层字段引用正确（不使用 a. 或 t.）

##### 📍 策略B：LEFT JOIN（用于空间查询）

**何时使用**：
- 查询包含空间关键词：附近、距离、周边、范围内、最近
- 必须有坐标才能返回的场景
- 需要使用 PostGIS 函数（ST_DWithin, ST_Distance等）

**SQL 模板**：
```sql
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'distance_km', ST_Distance(...) / 1000,
        '评分', CASE
            WHEN t."评分" ~ '^[0-9.]+$' THEN t."评分"
            ELSE NULL
        END
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'
WHERE ST_DWithin(a.geom::geography, ..., [距离米数])
ORDER BY distance_km
LIMIT 10
```

##### ⭐ 策略C：详情优先查询

**何时使用**：
- 查询重点是景点详细信息（评分、门票、介绍等）
- 强调"评分高"、"门票便宜"、"推荐"、"热门"

**SQL 模板**：
```sql
SELECT json_agg(
    json_build_object(
        'name', COALESCE(a.name, TRIM(SPLIT_PART(t.name, ' ', 1))),
        '评分', CASE WHEN t."评分" ~ '^[0-9.]+$' THEN t."评分" ELSE NULL END,
        '门票', t."门票"
    )
) as result
FROM tourist_spot t
LEFT JOIN a_sight a ON t.name LIKE a.name || '%'
WHERE t."评分" IS NOT NULL
ORDER BY t."评分"::numeric DESC
LIMIT 10
```

---

### 2. 增强 SQL 生成器 - 传递意图信息

**文件**: `core/processors/sql_generator.py`
**修改内容**:

#### 修改1：更新 sql_generation_prompt

**新增参数**（第 63 行）：
```python
input_variables=["base_prompt", "query", "intent_type", "is_spatial", "confidence", "keywords_matched"]
```

**新增意图提示**（第 44-53 行）：
```python
✅ 查询意图分析结果（请根据此信息自主选择最佳策略）：
- 查询类型: {intent_type} (query=数据查询需要json_agg / summary=统计查询直接COUNT)
- 空间查询: {is_spatial} (True=包含空间条件使用LEFT JOIN / False=普通查询使用UNION ALL)
- 置信度: {confidence}
- 匹配关键词: {keywords_matched}

🎯 策略选择指南（请严格遵守）：
1. 如果 intent_type == "summary" → 使用 COUNT/SUM/AVG 等聚合函数，❌不要使用 json_agg
2. 如果 is_spatial == True → 使用策略B（FROM a_sight a LEFT JOIN tourist_spot t），确保有坐标
3. 如果 intent_type == "query" 且 is_spatial == False → 使用策略A（UNION ALL三段式）获取完整数据⭐默认
```

#### 修改2：更新 generate_initial_sql 方法签名

**新增参数**（第 108-111 行）：
```python
def generate_initial_sql(
    self,
    query: str,
    intent_info: Optional[Dict[str, Any]] = None  # ✅ 新增参数：意图信息
) -> str:
```

**提取意图信息**（第 128-150 行）：
```python
# ✅ 提取意图信息（如果提供）
intent_type = "query"  # 默认值
is_spatial = False
confidence = 0.0
keywords_matched = []

if intent_info:
    intent_type = intent_info.get("intent_type", "query")
    is_spatial = intent_info.get("is_spatial", False)
    confidence = intent_info.get("confidence", 0.0)
    keywords_matched = intent_info.get("keywords_matched", [])

# 格式化关键词列表
keywords_str = ", ".join(keywords_matched) if keywords_matched else "无"

# 构建提示词（✅ 传递意图信息）
prompt_text = self.sql_generation_prompt.format(
    base_prompt=self.base_prompt,
    query=query,
    intent_type=intent_type,
    is_spatial=is_spatial,
    confidence=f"{confidence:.2f}",
    keywords_matched=keywords_str
)
```

---

### 3. 更新工作流节点 - 传递意图信息

**文件**: `core/graph/nodes.py`
**位置**: 第 333-338 行

**修改内容**：
```python
elif current_step == 0:
    # 初始查询
    intent_info = state.get("intent_info")  # ✅ 获取意图信息
    self.logger.info(f"Using intent info: {intent_info}")
    sql = self.sql_generator.generate_initial_sql(
        enhanced_query,
        intent_info=intent_info  # ✅ 传递意图信息到生成器
    )
```

---

### 4. 关键修复 - UNION ALL 策略的 FROM 子句错误

#### 🐛 问题描述

**错误信息**：
```
错误: 对于表"a"，丢失FROM子句项
LINE 3: 'name', COALESCE(a.name, TRIM(SPLIT_PART(t.name, ' ', 1))) ...
```

**原因**：
在外层 SELECT 中使用了 `a.name`, `t.name` 等表别名，但这些别名只存在于子查询内部，在外层是不可见的。外层只能看到 `combined_data` 这个别名。

#### ✅ 修复方案

**修改前**（❌ 错误）：
```sql
SELECT json_agg(
    json_build_object(
        'name', COALESCE(a.name, TRIM(SPLIT_PART(t.name, ' ', 1))),  -- ❌ a 和 t 在外层不存在
        'level', a.level,  -- ❌
        'city', COALESCE(a."所属城市", t."城市", '')  -- ❌
    )
) as result
FROM (
    -- UNION ALL 子查询
) combined_data
```

**修改后**（✅ 正确）：
```sql
SELECT json_agg(
    json_build_object(
        -- ✅ 直接使用字段名（从 combined_data 中获取）
        'name', name,  -- ✅
        'level', level,  -- ✅
        'city', COALESCE("所属城市", "城市")  -- ✅
    )
) as result
FROM (
    -- UNION ALL 子查询已经统一了所有字段名
) combined_data
```

**关键点**：
1. ✅ 外层不再引用 `a.` 或 `t.` 这样的表别名
2. ✅ 所有字段直接从 `combined_data` 中获取
3. ✅ 子查询已经统一了所有字段名，外层直接使用即可

---

## 🔄 工作流程

### 完整的 SQL 生成流程

```
1. 用户输入查询
   ↓
2. analyze_intent 节点分析查询意图
   → 输出: intent_info {
       intent_type: "query" | "summary",
       is_spatial: bool,
       confidence: float,
       keywords_matched: List[str]
   }
   ↓
3. enhance_query 节点增强查询
   ↓
4. generate_sql 节点
   ├─ 获取 intent_info
   ├─ 传递给 sql_generator.generate_initial_sql()
   │  ├─ 提取意图参数
   │  ├─ 构建增强提示词（包含意图信息）
   │  ├─ LLM 根据意图自主选择策略
   │  │  ├─ summary? → 使用 COUNT/SUM
   │  │  ├─ spatial? → 使用 LEFT JOIN
   │  │  └─ 默认 → 使用 UNION ALL
   │  └─ 生成 SQL
   └─ 返回 SQL
   ↓
5. execute_sql 节点执行查询
   ↓
6. 返回结果
```

---

## ✅ 预期效果

### 效果1：自动选择正确的 JOIN 策略

#### 示例1：通用查询
**查询**: "查询浙江省所有5A景区"
**LLM 判断**:
- 类型: query（数据查询）
- 空间: False
- 策略: **UNION ALL**（获取完整数据）

**生成 SQL**：
```sql
SELECT json_agg(json_build_object(...)) as result
FROM (
    SELECT ... FROM a_sight a LEFT JOIN tourist_spot t WHERE t.name IS NULL
    UNION ALL
    SELECT ... FROM tourist_spot t LEFT JOIN a_sight a WHERE a.gid IS NULL
    UNION ALL
    SELECT ... FROM a_sight a INNER JOIN tourist_spot t
) combined_data
WHERE level = '5A' AND "所属省份" = '浙江省'
LIMIT 10
```

#### 示例2：空间查询
**查询**: "查询杭州西湖附近5公里的景区"
**LLM 判断**:
- 类型: query
- 空间: True
- 策略: **LEFT JOIN**（必须有坐标）

**生成 SQL**：
```sql
SELECT json_agg(json_build_object(...)) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'
WHERE ST_DWithin(
    a.geom::geography,
    ST_SetSRID(ST_MakePoint(120.15, 30.28), 4326)::geography,
    5000
)
LIMIT 10
```

#### 示例3：统计查询
**查询**: "统计浙江省5A景区有多少个"
**LLM 判断**:
- 类型: summary
- 策略: **直接 COUNT**（不用 json_agg）

**生成 SQL**：
```sql
SELECT
    '浙江省' as province,
    '5A' as level,
    COUNT(*) as count
FROM a_sight
WHERE "所属省份" = '浙江省' AND level = '5A'
```

### 效果2：自动应用安全防护

评分字段始终使用 CASE 处理，防止 `"--"` 导致的 numeric 错误：
```sql
'评分', CASE
    WHEN "评分" IS NULL OR "评分" = '' OR "评分" = '--' THEN NULL
    WHEN "评分" ~ '^[0-9.]+$' THEN "评分"
    ELSE NULL
END
```

### 效果3：不会遗漏数据

使用 UNION ALL 策略，能够获取：
- ✅ 仅在 a_sight 中的景区（有坐标，无详细信息）
- ✅ 仅在 tourist_spot 中的景点（有详细信息，无坐标）
- ✅ 两表都有的完整数据

### 效果4：外层字段引用正确

✅ 不再出现"丢失FROM子句项"错误
✅ 所有字段直接从 `combined_data` 获取
✅ SQL 结构清晰，易于维护

---

## 📊 修改文件清单

| 文件 | 修改内容 | 行数变化 |
|------|---------|---------|
| `core/prompts.py` | 添加智能决策系统章节 | +222 行 |
| `core/processors/sql_generator.py` | 支持传递 intent_info | +28 行 |
| `core/graph/nodes.py` | 传递 intent_info 到生成器 | +3 行 |
| **总计** | | **+253 行** |

---

## 🧪 测试建议

### 测试用例1：通用查询（UNION ALL）
```python
query = "查询浙江省的5A景区"
intent_info = {
    "intent_type": "query",
    "is_spatial": False,
    "confidence": 0.85
}
# 预期：使用 UNION ALL 策略
```

### 测试用例2：空间查询（LEFT JOIN）
```python
query = "查询杭州西湖附近的景区"
intent_info = {
    "intent_type": "query",
    "is_spatial": True,
    "confidence": 0.90
}
# 预期：使用 LEFT JOIN 策略
```

### 测试用例3：统计查询（COUNT）
```python
query = "浙江省有多少个5A景区"
intent_info = {
    "intent_type": "summary",
    "is_spatial": False,
    "confidence": 0.70
}
# 预期：直接使用 COUNT，不用 json_agg
```

### 测试用例4：评分字段安全性
```python
# 数据库中包含 "评分" = "--" 的记录
query = "查询评分高的景区"
# 预期：评分字段使用 CASE 处理，"--" 转换为 NULL，不报错
```

---

## 🎯 性能与安全

### 性能考虑

1. **UNION ALL 性能**：
   - 三次表扫描，可能比单个 JOIN 慢
   - 建议在 a_sight.name 和 tourist_spot.name 上添加索引
   - 监控查询时间，必要时调整策略

2. **空间查询优化**：
   - 确保 a_sight.geom 有 GIST 索引
   - 使用 `ST_DWithin` 而不是 `ST_Distance`（更快）

### 安全防护

1. **评分字段**：CASE 处理防止 numeric 转换错误
2. **坐标字段**：CASE 处理防止空值错误
3. **FROM 子句**：三层防护机制（提示词 + 验证 + 自动修复）
4. **外层字段引用**：不使用子查询中的表别名，避免作用域错误

---

## 📝 后续改进建议

### 短期（1-2周）
1. ✅ 监控 LLM 策略选择的准确率
2. ✅ 收集用户反馈，调整决策规则
3. ✅ 添加策略选择的日志记录

### 中期（1-2月）
1. 实现策略选择的自动评估和调整
2. 添加查询性能监控
3. 优化 UNION ALL 查询性能

### 长期（3-6月）
1. 实现基于历史查询的策略学习
2. 添加查询计划分析
3. 实现动态索引建议

---

## ❌ 已知限制

1. **UNION ALL 性能**：对于大数据集可能较慢
2. **LLM 判断**：依赖 LLM 的理解能力，可能存在误判
3. **字段统一**：子查询需要返回完全相同的字段列表

---

## 🎓 学习要点

### 关键技术点

1. **SQL 作用域**：
   - 子查询中的表别名（a, t）在外层不可见
   - 外层只能引用子查询的别名（combined_data）或字段名

2. **UNION ALL 要求**：
   - 所有子查询必须返回相同数量和类型的字段
   - 使用 `NULL::type` 显式声明空值类型

3. **LLM 提示工程**：
   - 明确的决策流程图
   - 具体的策略选择条件
   - 丰富的示例和反例

4. **意图驱动设计**：
   - 先分析意图，再生成 SQL
   - 意图信息贯穿整个工作流
   - 基于意图选择最佳策略

---

## 📚 相关文档

- `PRODUCTION_ERROR_FIXES.md` - 生产环境错误修复（评分字段处理）
- `REFACTORING_REPORT.md` - 代码重构报告（继承优化）
- `INTENT_OPTIMIZATION_SUMMARY.md` - 查询意图分析优化（32个测试用例）
- `FROM_CLAUSE_FIX_FINAL.md` - FROM 子句错误三层防护
- `CLAUDE.md` - 项目架构与逻辑说明

---

**完成时间**: 2025-10-04
**测试状态**: ⏳ 待测试
**影响等级**: 🟢 高（核心功能增强）
**向后兼容**: ✅ 是（intent_info 参数可选）

---

*本文档记录了 LLM 自主决策能力增强的完整实施过程，包括设计思路、实现细节、修复过程和预期效果。*
