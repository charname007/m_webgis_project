# Schema 注入增强 - Database Schema 信息传递到 LLM

## 📋 问题描述

**发现时间**: 2025-10-04

**问题现象**:
用户发现 LLM 生成 SQL 时并不知道数据库表的字段和类型信息，导致可能生成错误的字段名或使用错误的数据类型。

**问题根源**:
虽然 `fetch_schema` 节点已经获取了完整的数据库 Schema 信息（包括表结构、字段类型、主外键等），并存储在 `state["database_schema"]` 中，但这个信息**没有传递给 SQL 生成的 Prompt**。

之前的实现中：
- `base_prompt` 只包含一般性的提示词（如 `SCENIC_QUERY_PROMPT`）
- SQL 生成时使用的三个 prompt 模板（`sql_generation_prompt`, `followup_query_prompt`, `fix_sql_with_error`）都没有包含 `database_schema` 参数
- LLM 只能依靠 prompt 中的硬编码表名和字段名示例，无法知道实际的字段类型

---

## ✅ 解决方案

### 1. 核心思路

**将 `database_schema` 信息注入到所有 SQL 生成相关的 Prompt 中**，让 LLM 能够：
- 知道确切的表名和字段名（避免拼写错误）
- 了解字段的数据类型（如 `varchar(100)`, `numeric(3,1)`, `geometry(Point, 4326)` 等）
- 理解表之间的关系（主键、外键）
- 识别空间表和空间列

### 2. 修改内容

#### 修改 1: `sql_generation_prompt` 模板（初始 SQL 生成）

**文件**: `core/processors/sql_generator.py` (lines 36-90)

**变更**:
```python
# ❌ 修改前
template="""你是一个精通 PostgreSQL 和 PostGIS 的 SQL 专家。

{base_prompt}

**用户查询**: {query}
...
"""
input_variables=["base_prompt", "query", "intent_type", "is_spatial", "confidence", "keywords_matched"]

# ✅ 修改后
template="""你是一个精通 PostgreSQL 和 PostGIS 的 SQL 专家。

{base_prompt}

**数据库Schema信息**（完整字段类型供你参考）:
{database_schema}

**用户查询**: {query}
...
### 2. 数据获取策略
   - 需要从哪些表获取数据？（参考上方Schema信息中的表结构）
   ...
   - 如何处理可能的 NULL 值和数据类型问题？（参考Schema中的字段类型）
...
"""
input_variables=["base_prompt", "database_schema", "query", "intent_type", "is_spatial", "confidence", "keywords_matched"]
```

**效果**:
- LLM 能看到完整的表结构和字段类型
- 在生成 SQL 时可以参考实际的字段名和类型
- 减少字段名拼写错误和类型转换错误

---

#### 修改 2: `followup_query_prompt` 模板（补充查询 SQL 生成）

**文件**: `core/processors/sql_generator.py` (lines 92-153)

**变更**:
```python
# ❌ 修改前
template="""你是一个擅长优化和补充查询的 SQL 专家。

{base_prompt}

**用户原始需求**: {original_query}
...
"""
input_variables=["base_prompt", "original_query", "previous_sql", "record_count", "missing_fields"]

# ✅ 修改后
template="""你是一个擅长优化和补充查询的 SQL 专家。

{base_prompt}

**数据库Schema信息**（完整字段类型供你参考）:
{database_schema}

**用户原始需求**: {original_query}
...
1. **数据完整性分析**
   - 哪些字段缺失了？
   - 这些字段通常在哪个表中？（参考上方Schema信息中的表结构和字段类型）
...
"""
input_variables=["base_prompt", "database_schema", "original_query", "previous_sql", "record_count", "missing_fields"]
```

**效果**:
- 在补充查询时能准确知道缺失字段在哪个表中
- 避免因字段名错误导致补充查询失败

---

#### 修改 3: `fix_sql_with_error` 方法（错误修复 SQL 生成）

**文件**: `core/processors/sql_generator.py` (lines 408-508)

**变更**:
```python
# ❌ 修改前
def fix_sql_with_error(
    self,
    sql: str,
    error: str,
    query: str
) -> str:
    ...
    fix_prompt = f"""你是一个精通 PostgreSQL 和 PostGIS 的 SQL 专家。

**用户需求**: {query}

**生成的 SQL**:
...
**数据库结构**:
- `a_sight`: 景区基础信息表（含坐标、等级等）
- `tourist_spot`: 景区详细信息表（含评分、门票、介绍等）
...
"""

# ✅ 修改后
def fix_sql_with_error(
    self,
    sql: str,
    error: str,
    query: str,
    database_schema: Optional[str] = None  # ✅ 新增参数
) -> str:
    ...
    schema_str = database_schema if database_schema else "(Schema信息未加载)"

    fix_prompt = f"""你是一个精通 PostgreSQL 和 PostGIS 的 SQL 专家。

**数据库Schema信息**（完整字段类型供你参考）:
{schema_str}

**用户需求**: {query}
...
2. **问题分析**
   ...
   - 参考上方Schema信息，字段类型是否正确使用？
...
"""
```

**效果**:
- 修复 SQL 时能参考实际的字段类型，避免类型转换错误
- 能正确识别字段是否存在、类型是否匹配

---

#### 修改 4: `generate_initial_sql` 方法

**文件**: `core/processors/sql_generator.py` (lines 155-229)

**变更**:
```python
# ❌ 修改前
def generate_initial_sql(
    self,
    query: str,
    intent_info: Optional[Dict[str, Any]] = None
) -> str:
    ...
    prompt_text = self.sql_generation_prompt.format(
        base_prompt=self.base_prompt,
        query=query,
        intent_type=intent_type,
        is_spatial=is_spatial,
        confidence=f"{confidence:.2f}",
        keywords_matched=keywords_str
    )

# ✅ 修改后
def generate_initial_sql(
    self,
    query: str,
    intent_info: Optional[Dict[str, Any]] = None,
    database_schema: Optional[str] = None  # ✅ 新增参数
) -> str:
    ...
    schema_str = database_schema if database_schema else "(Schema信息未加载)"

    prompt_text = self.sql_generation_prompt.format(
        base_prompt=self.base_prompt,
        database_schema=schema_str,  # ✅ 传递Schema
        query=query,
        intent_type=intent_type,
        is_spatial=is_spatial,
        confidence=f"{confidence:.2f}",
        keywords_matched=keywords_str
    )
```

---

#### 修改 5: `generate_followup_sql` 方法

**文件**: `core/processors/sql_generator.py` (lines 231-273)

**变更**:
```python
# ❌ 修改前
def generate_followup_sql(
    self,
    original_query: str,
    previous_sql: str,
    record_count: int,
    missing_fields: List[str]
) -> str:
    ...
    prompt_text = self.followup_query_prompt.format(
        base_prompt=self.base_prompt,
        original_query=original_query,
        previous_sql=previous_sql,
        record_count=record_count,
        missing_fields=", ".join(missing_fields)
    )

# ✅ 修改后
def generate_followup_sql(
    self,
    original_query: str,
    previous_sql: str,
    record_count: int,
    missing_fields: List[str],
    database_schema: Optional[str] = None  # ✅ 新增参数
) -> str:
    ...
    schema_str = database_schema if database_schema else "(Schema信息未加载)"

    prompt_text = self.followup_query_prompt.format(
        base_prompt=self.base_prompt,
        database_schema=schema_str,  # ✅ 传递Schema
        original_query=original_query,
        previous_sql=previous_sql,
        record_count=record_count,
        missing_fields=", ".join(missing_fields)
    )
```

---

#### 修改 6: `generate_sql` 节点（核心调用点）

**文件**: `core/graph/nodes.py` (lines 296-389)

**变更**:
```python
# ✅ 在生成 SQL 之前，获取并格式化 Schema
database_schema_dict = state.get("database_schema")
database_schema_str = None
if database_schema_dict:
    database_schema_str = self.schema_fetcher.format_schema_for_llm(database_schema_dict)
    self.logger.debug(f"Formatted schema length: {len(database_schema_str)} chars")

# ✅ 所有 SQL 生成调用都传递 database_schema_str

# 1. Fallback retry_sql 策略
if fallback_strategy == "retry_sql" and last_error:
    if previous_sql:
        sql = self.sql_generator.fix_sql_with_error(
            sql=previous_sql,
            error=last_error,
            query=enhanced_query,
            database_schema=database_schema_str  # ✅ 传递Schema
        )
    else:
        sql = self.sql_generator.generate_initial_sql(
            enhanced_query,
            database_schema=database_schema_str  # ✅ 传递Schema
        )

# 2. Fallback simplify_query 策略
elif fallback_strategy == "simplify_query":
    if not previous_sql:
        sql = self.sql_generator.generate_initial_sql(
            enhanced_query,
            database_schema=database_schema_str  # ✅ 传递Schema
        )

# 3. 初始查询
elif current_step == 0:
    intent_info = state.get("intent_info")
    sql = self.sql_generator.generate_initial_sql(
        enhanced_query,
        intent_info=intent_info,
        database_schema=database_schema_str  # ✅ 传递Schema
    )

# 4. 补充查询
else:
    sql = self.sql_generator.generate_followup_sql(
        original_query=enhanced_query,
        previous_sql=previous_sql,
        record_count=len(previous_data) if previous_data else 0,
        missing_fields=missing_analysis["missing_fields"],
        database_schema=database_schema_str  # ✅ 传递Schema
    )
```

**关键点**:
- 使用 `self.schema_fetcher.format_schema_for_llm(database_schema_dict)` 将字典格式的 Schema 转换为 LLM 可读的字符串格式
- 在所有 SQL 生成场景（初始查询、补充查询、错误修复、Fallback 策略）都传递 Schema 信息

---

## 📊 修改总结

### 文件修改清单

| 文件 | 修改内容 | 行数变化 |
|------|----------|----------|
| `core/processors/sql_generator.py` | 三个 Prompt 模板添加 `database_schema` 参数 | ~30 行 |
| `core/processors/sql_generator.py` | `generate_initial_sql` 方法添加参数 | ~5 行 |
| `core/processors/sql_generator.py` | `generate_followup_sql` 方法添加参数 | ~5 行 |
| `core/processors/sql_generator.py` | `fix_sql_with_error` 方法添加参数 | ~5 行 |
| `core/graph/nodes.py` | `generate_sql` 节点添加 Schema 格式化和传递 | ~10 行 |

### 关键变更点

1. **三个 Prompt 模板**全部添加 `{database_schema}` 占位符
2. **三个生成方法**全部添加 `database_schema: Optional[str] = None` 参数
3. **generate_sql 节点**在所有调用点传递格式化后的 Schema 字符串
4. **保持向后兼容**：所有新参数都是可选的（`Optional`），默认值为 `None`，未提供时使用 `"(Schema信息未加载)"`

---

## 🎯 预期效果

### 1. 字段名准确性提升
- LLM 能看到实际的字段名（如 `"评分"`, `"门票"`, `"介绍"`, `"图片链接"`）
- 减少因字段名拼写错误导致的 SQL 执行失败

### 2. 数据类型正确性提升
- LLM 知道 `"评分"` 是 `numeric(3,1)` 类型
- 知道 `name` 是 `varchar(100)` 类型
- 知道 `geom` 是 `geometry(Point, 4326)` 类型
- 减少类型转换错误

### 3. 表结构理解增强
- LLM 能看到主键、外键关系
- 知道哪些表是空间表
- 了解表之间的关联方式

### 4. 错误修复能力提升
- 在修复 SQL 时能参考实际的字段类型
- 能更准确地诊断类型不匹配错误
- 配合启发式 Prompt，能自动修复更多类型的错误

### 5. GROUP BY 错误自动修复
- LLM 现在知道所有字段的类型和名称
- 配合启发式 Prompt 中的 PostgreSQL 聚合规则提示
- 能自动识别哪些字段应该在 GROUP BY 中
- 预期能解决之前反复出现的 GROUP BY 错误

---

## 🧪 测试建议

### 1. 基础功能测试
```python
# 测试查询：验证 Schema 是否正确传递
query = "查询浙江省的5A景区"
# 检查生成的 SQL 是否使用了正确的字段名和类型
```

### 2. 字段类型测试
```python
# 测试查询：验证类型敏感的字段处理
query = "评分大于4.5的景区"
# 检查是否正确处理 numeric 类型的比较
```

### 3. 空间查询测试
```python
# 测试查询：验证空间字段识别
query = "查询杭州附近10公里的景区"
# 检查是否正确使用 geometry 类型的空间函数
```

### 4. 错误修复测试
```python
# 测试场景：故意触发 GROUP BY 错误
# 观察是否能在第一次 retry 时自动修复
# 检查日志中 Schema 信息是否被正确传递
```

### 5. Schema 缺失测试
```python
# 测试场景：模拟 Schema 获取失败
# 验证是否能正确使用 fallback 提示 "(Schema信息未加载)"
# 系统是否仍能正常工作（降级模式）
```

---

## 📝 注意事项

### 1. Schema 格式化开销
- 每次生成 SQL 都会调用 `format_schema_for_llm()`
- 格式化后的字符串可能较长（数千字符）
- **建议**: 后续可以考虑在 `generate_sql` 节点开始时格式化一次，缓存整个会话使用

### 2. Token 消耗增加
- 每个 SQL 生成请求的 Prompt 都会增加 Schema 信息
- 预估每次请求增加 2000-5000 tokens
- **影响**: API 调用成本略有增加，但换来更高的准确率

### 3. 向后兼容性
- 所有新参数都设置为 `Optional[str] = None`
- 未提供 Schema 时使用 `"(Schema信息未加载)"` 作为 fallback
- **保证**: 现有测试代码无需修改即可运行

### 4. Schema 更新频率
- 当前 Schema 在每次会话开始时获取一次
- 如果数据库结构发生变化，需要重启 Agent 或清除缓存
- **建议**: 后续可以考虑添加 Schema 刷新机制

---

## 🚀 后续优化方向

### 1. Schema 缓存优化
```python
# 当前：每次调用 format_schema_for_llm()
# 优化：在 generate_sql 节点缓存格式化结果
class AgentNodes:
    def __init__(self, ...):
        self._formatted_schema_cache = None

    def generate_sql(self, state):
        if not self._formatted_schema_cache:
            self._formatted_schema_cache = self.schema_fetcher.format_schema_for_llm(...)
        database_schema_str = self._formatted_schema_cache
```

### 2. 动态 Schema 选择
```python
# 根据查询意图只传递相关表的 Schema
if "景区" in query:
    schema_str = format_tables_only(["a_sight", "tourist_spot"])
else:
    schema_str = format_all_tables()
```

### 3. Schema 压缩
```python
# 压缩 Schema 表示，减少 Token 消耗
# 例如：只传递字段名和类型，省略描述和约束
def format_schema_compact(schema_dict):
    return "\n".join([
        f"{table}: {', '.join(f'{col}:{type}' for col, type in columns)}"
        for table, columns in schema_dict.items()
    ])
```

---

## 📚 相关文档

- `HEURISTIC_PROMPT_TRANSFORMATION.md` - 启发式 Prompt 设计理念
- `FROM_CLAUSE_FIX_FINAL.md` - FROM 子句错误三层防护机制
- `INTENT_OPTIMIZATION_SUMMARY.md` - 查询意图分析优化
- `CLAUDE.md` (项目说明) - 完整的项目架构说明

---

## ✅ 验证清单

- [x] 三个 Prompt 模板已添加 `{database_schema}` 占位符
- [x] `generate_initial_sql` 方法已添加 `database_schema` 参数
- [x] `generate_followup_sql` 方法已添加 `database_schema` 参数
- [x] `fix_sql_with_error` 方法已添加 `database_schema` 参数
- [x] `generate_sql` 节点已在所有调用点传递 Schema
- [x] 保持向后兼容性（所有参数可选）
- [ ] 运行测试验证功能正常
- [ ] 观察 GROUP BY 错误是否能自动修复
- [ ] 检查 Token 消耗是否在可接受范围

---

*文档创建时间: 2025-10-04*
*版本: 1.0*
*状态: ✅ 实现完成，待测试验证*
