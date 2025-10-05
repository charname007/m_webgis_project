# Sight Server - 项目架构与逻辑说明

## 项目概述

**Sight Server** 是一个基于 LangGraph 的智能 SQL 查询 Agent，专门用于自然语言查询旅游景区数据库（PostgreSQL + PostGIS）。

### 核心功能
- 自然语言转 SQL 查询
- 多步迭代查询（自动补充缺失信息）
- 智能错误重试（Fallback 机制）
- 数据库 Schema 自动获取
- PostGIS 空间查询支持
- 思维链完整记录
- **查询意图分析**（Query vs Summary，Spatial vs Non-Spatial）
- **意图驱动的数据返回**（Summary 类型不返回完整数据）

### 最近更新（2025-10-04）
- ✅ 优化查询意图分析（100%测试通过率）
- ✅ 添加 intent_info 到 API 返回结果
- ✅ 修复 FROM 子句错误（三层防护机制）
- ✅ 更新 FULL OUTER JOIN 策略
- ✅ 增强 SQL 生成提示词和验证机制

---

## 技术栈

| 组件 | 技术 |
|------|------|
| AI 框架 | LangChain + LangGraph |
| LLM | DeepSeek API |
| 数据库 | PostgreSQL 14+ with PostGIS 3.2+ |
| 连接器 | psycopg2 + SQLAlchemy |
| Web 框架 | FastAPI |
| 语言 | Python 3.11+ |

---

## 核心架构

### 1. LangGraph 工作流

```mermaid
graph TD
    START[开始] --> A[fetch_schema: 获取数据库Schema]
    A --> B[analyze_intent: 分析查询意图]
    B --> C[enhance_query: 增强查询文本]
    C --> D[generate_sql: 生成SQL]
    D --> E[execute_sql: 执行SQL]
    E --> F{should_retry_or_fail}
    F -->|有错误| G[handle_error: 错误处理]
    G --> D
    F -->|无错误| H[check_results: 检查结果完整性]
    H --> I{should_continue_querying}
    I -->|数据不完整| D
    I -->|数据完整| J[generate_answer: 生成答案]
    J --> END[结束]
```

### 2. 目录结构

```
sight_server/
├── core/                          # 核心模块
│   ├── agent.py                   # SQLQueryAgent 主类
│   ├── database.py                # 数据库连接器
│   ├── llm.py                     # LLM 封装
│   ├── schemas.py                 # 数据模型定义
│   ├── prompts.py                 # 提示词管理
│   ├── memory.py                  # Memory 机制
│   ├── checkpoint.py              # Checkpoint 机制
│   │
│   ├── processors/                # 处理器模块
│   │   ├── sql_generator.py       # SQL 生成器
│   │   ├── sql_executor.py        # SQL 执行器
│   │   ├── result_parser.py       # 结果解析器
│   │   ├── answer_generator.py    # 答案生成器
│   │   └── schema_fetcher.py      # Schema 获取器
│   │
│   └── graph/                     # LangGraph 工作流
│       ├── nodes.py               # 节点函数（8个节点）
│       ├── edges.py               # 条件边函数
│       └── builder.py             # 图构建器
│
├── api/                           # FastAPI 接口
│   ├── routes.py                  # 路由定义
│   └── models.py                  # API 数据模型
│
├── config.py                      # 配置文件
├── main.py                        # 主入口
└── tests/                         # 测试文件
```

---

## 核心组件详解

### 1. AgentState（状态模型）

定义了工作流中传递的完整状态：

```python
class AgentState(TypedDict):
    # 输入查询
    query: str                          # 原始查询
    enhanced_query: str                 # 增强后的查询
    query_intent: Optional[str]         # 查询意图（"query" 或 "summary"）
    requires_spatial: bool              # 是否需要空间查询
    intent_info: Optional[Dict]         # ✅ 完整的意图分析信息（新增）

    # 数据库 Schema
    database_schema: Optional[Dict]     # 数据库结构信息
    schema_fetched: bool                # Schema 是否已获取

    # 多步查询历史（累积）
    sql_history: Annotated[List[str], add]
    execution_results: Annotated[List[Dict], add]
    thought_chain: Annotated[List[Dict], add]

    # 当前步骤状态
    current_step: int                   # 当前迭代步数
    current_sql: Optional[str]          # 当前 SQL
    current_result: Optional[Dict]      # 当前结果

    # 控制流程
    should_continue: bool               # 是否继续查询
    should_return_data: bool            # ✅ 是否返回完整数据（新增）
    max_iterations: int                 # 最大迭代次数（默认10）
    error: Optional[str]                # 错误信息

    # Fallback 重试机制
    retry_count: int                    # 重试次数
    max_retries: int                    # 最大重试次数（默认5）
    last_error: Optional[str]           # 最后错误
    error_history: Annotated[List[Dict], add]
    fallback_strategy: Optional[str]    # 回退策略
    error_type: Optional[str]           # 错误类型

    # 最终输出
    final_data: Optional[List[Dict]]    # 合并后的数据
    answer: str                         # 自然语言回答
    status: str                         # 状态
    message: str                        # 消息
```

---

## 查询意图分析系统（2025-10-04 新增）

### 1. 意图分析功能

**核心方法**：`PromptManager.analyze_query_intent(query: str)`
**位置**：`core/prompts.py`

#### 分析维度

```python
{
    "intent_type": "query" | "summary",    # 查询类型
    "is_spatial": bool,                    # 是否空间查询
    "prompt_type": "scenic_query" | "spatial_query" | "general_query",
    "keywords_matched": List[str],         # 匹配的关键词
    "description": str,                    # 意图描述
    "confidence": float,                   # 置信度 (0-1)
    "analysis_details": {
        "summary_score": float,            # 统计查询得分
        "spatial_score": float,            # 空间查询得分
        "scenic_score": float,             # 景区查询得分
        "matched_patterns": List[str]      # 匹配的模式
    }
}
```

### 2. 关键词库（优化版）

#### Summary 关键词（31个）
```python
SUMMARY_KEYWORDS = [
    # 强统计：'统计', '总结', '汇总', '计数', '总数', '总计', '一共', '总共', '共有', '合计'
    # 数量：'多少', '数量', '个数', '有几个', '有多少', '几个'
    # 聚合：'分布', '平均', '最多', '最少', '排名', '分析', '占比', '百分比', '比例'
    # 英文：'count', 'sum', 'average', 'max', 'min', 'total', 'percentage', ...
]
```

#### Spatial 关键词（36个）
```python
SPATIAL_KEYWORDS = [
    # 强空间：'距离', '附近', '周围', '范围内', '最近', '周边', '临近', '靠近', '邻近'
    # 中等：'路径', '路线', '附近的', '周围的', '旁边', '边上'
    # PostGIS：'相交', '包含', '在内', '边界', '缓冲', '缓冲区'
    # 英文：'distance', 'near', 'nearby', 'around', 'within', 'surrounding', ...
]
```

### 3. 意图判断规则

#### Summary 判断（阈值 0.25）
```python
# 强关键词（+0.4）：'统计', '计数', '一共', '总共'
# 中等关键词（+0.25）：'汇总', '总结', '个数'
# 正则模式（+0.5）：'有多少个?', '一共.*?多少'
# 动词加成（+0.3）：'统计', '计算', '汇总'
# Query动词折扣（×0.4）：'查询', '查找', '列出'

if summary_score >= 0.25:
    intent_type = "summary"
```

#### Spatial 判断（阈值 0.2）
```python
# 强关键词（+0.3）：'距离', '附近', '周边', '临近'
# 中等关键词（+0.2）：'附近的', '周围的', '旁边'
# 正则模式（+0.5）：'距离.{0,10}?公里', '附近.{0,20}?景区'

if spatial_score >= 0.2:
    is_spatial = True
```

#### 排除规则
```python
# 排除模式（不计入统计得分）：
exclusion_patterns = [
    r'这几个',    # "这几个景区"是指代
    r'那几个',    # 同上
    r'前\d+个',   # "前10个"是排序
]
```

### 4. 测试结果（100%通过）

**32个测试用例全部通过**：
- Summary 基础统计：6/6 ✅
- Summary 容易误判：3/3 ✅
- Query 基础查询：6/6 ✅
- Spatial 基础查询：6/6 ✅
- Spatial 高级查询：4/4 ✅
- Summary + Spatial 组合：3/3 ✅
- 边界 Case：4/4 ✅

**典型案例**：
- "浙江省景区有几个" → summary (0.35 ≥ 0.25) ✅
- "查询杭州附近的景区" → query + spatial (0.90 ≥ 0.2) ✅
- "西湖周边的景区" → query + spatial (0.70，新增"周边") ✅
- "这几个景区" → query (排除规则生效) ✅

### 5. 意图驱动的数据返回

**节点**：`generate_answer`
**位置**：`core/graph/nodes.py`

```python
# 根据查询意图决定是否返回完整数据
should_return_data = (query_intent != "summary")

return {
    "answer": answer,
    "should_return_data": should_return_data,  # ✅ 标记
    ...
}
```

**Agent 处理**：`core/agent.py`
```python
should_return_data = result_state.get("should_return_data", True)

if not should_return_data:
    final_data = None  # Summary 类型不返回完整数据
```

### 6. API 返回结果

**模型**：`models/api_models.py` → `QueryResponse`

```python
class QueryResponse(BaseModel):
    status: QueryStatus
    answer: str
    data: Optional[List[Dict]]      # Summary类型时为None
    count: int
    message: str
    sql: Optional[str]
    execution_time: Optional[float]
    intent_info: Optional[Dict]     # ✅ 新增意图信息
```

**示例返回**：
```json
{
  "status": "success",
  "answer": "浙江省共有19个5A级景区",
  "data": null,  // Summary 类型不返回数据
  "count": 19,
  "intent_info": {
    "intent_type": "summary",
    "is_spatial": false,
    "confidence": 0.70,
    "keywords_matched": ["统计", "数量"]
  }
}
```

---

## SQL 生成与验证系统（2025-10-04 更新）

### 1. FULL OUTER JOIN 策略

**决策树**：
```
1. 是否是空间查询？（如"附近"、"距离XX公里"）
   ✅ YES → FROM a_sight a LEFT JOIN tourist_spot t（必须有坐标）
   ❌ NO → 继续判断

2. 是否需要完整数据？
   ✅ YES → FROM a_sight a FULL OUTER JOIN tourist_spot t（包含两表所有数据）
   ❌ NO → 默认 FULL OUTER JOIN
```

**关键要点**：
- FULL OUTER JOIN：获取两表所有数据
- LEFT JOIN：仅用于空间查询（确保有坐标）
- 使用 COALESCE 处理 NULL 字段
- 添加 _dataSource 标识数据来源

### 2. FROM 子句错误三层防护

**问题**：LLM 可能反复生成缺少 FROM 子句的 SQL

#### 第1层：增强提示词
**位置**：`core/processors/sql_generator.py`

```python
template="""
🚨 绝对必需的SQL结构（按顺序）：
1. SELECT json_agg(...) as result
2. FROM 表名 别名   ← 必须有这一行！
3. WHERE 条件

❌ 错误示例（缺少FROM子句）：
SELECT json_agg(...) WHERE a.level = '5A'

✅ 正确示例（完整的FROM子句）：
SELECT json_agg(...) as result
FROM a_sight a
WHERE a.level = '5A'
"""
```

#### 第2层：SQL结构验证
**新增方法**：`_validate_sql_structure(sql: str) -> bool`

```python
def _validate_sql_structure(self, sql: str) -> bool:
    # 1. 检查是否包含FROM关键字
    if 'from' not in sql_lower:
        return False

    # 2. 检查别名a是否已定义
    if 使用了a. but FROM中没有'a_sight a':
        return False

    # 3. 检查别名t是否已定义
    if 使用了t. but FROM中没有'tourist_spot t':
        return False

    return True
```

#### 第3层：自动修复机制
**新增方法**：`_add_from_clause_if_missing(sql: str, query: str) -> str`

```python
def _add_from_clause_if_missing(self, sql: str, query: str) -> str:
    # 1. 检测使用了哪些表别名
    uses_a = bool(re.search(r'\ba\.', sql))
    uses_t = bool(re.search(r'\bt\.', sql))

    # 2. 构建合适的FROM子句
    if uses_a and uses_t:
        from_clause = "FROM a_sight a FULL OUTER JOIN tourist_spot t ON ..."
    elif uses_a:
        from_clause = "FROM a_sight a"

    # 3. 智能插入FROM子句（在WHERE前或SQL末尾）
    ...
```

**完整防护流程**：
```
生成SQL → 验证结构 → 发现缺少FROM → 自动添加 → 再次验证 → 成功 ✅
如果仍失败 → 增强提示词重试 → 验证修复 → 成功 ✅
```

### 3. 错误分类器增强

**位置**：`core/graph/nodes.py` → `_classify_error()`

```python
# ✅ 新增：FROM子句错误识别
elif any(keyword in error_lower for keyword in
    ["from子句", "丢失from", "missing from", "from-clause"]):
    return "sql_syntax_error"
```

**已识别的错误类型**：
1. `sql_syntax_error` - 语法错误、聚合函数错误、FROM子句错误
2. `field_error` - 字段/表不存在
3. `execution_timeout` - 超时
4. `connection_error` - 连接错误
5. `permission_error` - 权限错误
6. `data_format_error` - 数据格式错误
7. `unknown_error` - 未知错误

---

## AgentState（状态模型）

定义了工作流中传递的完整状态：

```python
class AgentState(TypedDict):

    # 数据库 Schema
    database_schema: Optional[Dict]     # 数据库结构信息
    schema_fetched: bool                # Schema 是否已获取

    # 多步查询历史（累积）
    sql_history: Annotated[List[str], add]
    execution_results: Annotated[List[Dict], add]
    thought_chain: Annotated[List[Dict], add]

    # 当前步骤状态
    current_step: int                   # 当前迭代步数
    current_sql: Optional[str]          # 当前 SQL
    current_result: Optional[Dict]      # 当前结果

    # 控制流程
    should_continue: bool               # 是否继续查询
    max_iterations: int                 # 最大迭代次数（默认10）
    error: Optional[str]                # 错误信息

    # Fallback 重试机制
    retry_count: int                    # 重试次数
    max_retries: int                    # 最大重试次数（默认5）
    last_error: Optional[str]           # 最后错误
    error_history: Annotated[List[Dict], add]
    fallback_strategy: Optional[str]    # 回退策略
    error_type: Optional[str]           # 错误类型

    # 最终输出
    final_data: Optional[List[Dict]]    # 合并后的数据
    answer: str                         # 自然语言回答
    status: str                         # 状态
    message: str                        # 消息
```

---

### 2. 8个核心节点

#### 节点0: fetch_schema
- **功能**：获取数据库 Schema（表结构、字段类型、主外键等）
- **实现**：`SchemaFetcher.fetch_schema()`
- **输出**：`database_schema`（包含所有表的详细信息）
- **缓存**：支持 Schema 缓存，避免重复查询

#### 节点1: analyze_intent
- **功能**：分析查询意图（query/summary）和是否涉及空间查询
- **实现**：`PromptManager.analyze_query_intent()`
- **输出**：`query_intent`, `requires_spatial`

#### 节点2: enhance_query
- **功能**：增强查询文本（添加空间提示等）
- **实现**：`PromptManager.build_enhanced_query()`
- **输出**：`enhanced_query`

#### 节点3: generate_sql
- **功能**：生成 SQL 查询
- **模式**：
  - 首次查询：`generate_initial_sql()`
  - 后续查询：`generate_followup_sql()`（补充缺失字段）
  - Fallback：`fix_sql_with_error()` 或 `simplify_sql()`
- **逻辑**：
  ```python
  if fallback_strategy == "retry_sql":
      sql = fix_sql_with_error(previous_sql, error)
  elif fallback_strategy == "simplify_query":
      sql = simplify_sql(previous_sql, max_limit=50)
  elif current_step == 0:
      sql = generate_initial_sql(query)
  else:
      # 分析缺失信息
      missing = analyze_missing_info(previous_data)
      if not missing["has_missing"]:
          return {"current_sql": None, "should_continue": False}
      sql = generate_followup_sql(missing_fields)
  ```

#### 节点4: execute_sql
- **功能**：执行 SQL 并解析结果
- **特殊处理**：
  - 如果 `current_sql` 为 `None`，跳过执行（不报错）
  - 成功后重置 `retry_count` 和 `fallback_strategy`
  - 多步查询结果自动合并
- **连接模式**：使用 `autocommit=True` 避免事务阻塞

#### 节点5: check_results
- **功能**：评估结果完整性
- **判断逻辑**：
  ```python
  if no data:
      should_continue = False
  elif current_step >= max_iterations:
      should_continue = False
  elif completeness_score >= 0.9:
      should_continue = False
  elif missing_ratio > 0.5:
      should_continue = False  # 数据源本身不完整
  else:
      should_continue = True   # 继续补充查询
  ```

#### 节点6: generate_answer
- **功能**：根据查询结果生成自然语言回答
- **实现**：`AnswerGenerator.generate()`
- **输出**：`answer`, `status`, `message`

#### 节点7: handle_error
- **功能**：错误分类和智能重试
- **错误类型**（7种）：
  - `sql_syntax_error` → 策略：`retry_sql`
  - `field_error` → 策略：`retry_sql`
  - `execution_timeout` → 策略：`simplify_query`
  - `connection_error` → 策略：`retry_execution`（带指数退避）
  - `permission_error` → 策略：`fail`
  - `data_format_error` → 策略：`retry_sql` → `fail`
  - `unknown_error` → 策略：`retry_sql` → `fail`

---

### 3. 条件边函数

#### should_retry_or_fail
```python
def should_retry_or_fail(state) -> Literal["handle_error", "check_results"]:
    if not error:
        return "check_results"
    if retry_count >= max_retries:
        return "check_results"  # 重试次数用尽
    return "handle_error"       # 进入错误处理
```

#### should_continue_querying
```python
def should_continue_querying(state) -> Literal["generate_sql", "generate_answer"]:
    if error:
        return "generate_answer"
    if current_step >= max_iterations:
        return "generate_answer"
    if not should_continue:
        return "generate_answer"
    return "generate_sql"       # 继续查询
```

---

## 关键技术实现

### 1. 多步迭代查询

**问题**：用户查询"查询5A景区"，但结果可能缺少评分、门票等信息。

**解决方案**：
1. 首次查询 `a_sight` 表获取基础信息
2. `check_results` 发现缺少字段（如"评分"、"门票"）
3. `generate_sql` 生成补充查询 `LEFT JOIN tourist_spot`
4. `execute_sql` 执行并合并结果
5. 重复直到数据完整或达到最大迭代次数（10次）

**实现细节**：
```python
# ResultParser.evaluate_completeness()
expected_fields = ['name', 'level', 'address', 'coordinates',
                   '评分', '门票', '介绍', '图片链接']
missing_fields = [f for f in expected_fields if not has_value(data[f])]
completeness_score = 1 - len(missing_fields) / len(expected_fields)
```

---

### 2. Fallback 错误重试机制

**流程**：
```
execute_sql (失败)
  → error 被设置
  → should_retry_or_fail 检测到 error
  → handle_error (分类错误、决定策略、清除 error)
  → generate_sql (根据 fallback_strategy 修复或简化SQL)
  → execute_sql (重试)
  → retry_count 被重置（如果成功）
```

**关键点**：
- `handle_error` 必须清除 `error` 字段（避免无限循环）
- `execute_sql` 成功后重置 `retry_count` 和 `fallback_strategy`
- 最多重试 5 次（`max_retries=5`）

---

### 3. 数据库 Schema 自动获取

**目的**：为 LLM 提供准确的表结构信息，避免字段名错误。

**实现**：
```python
# DatabaseConnector.get_detailed_schema()
for table in all_tables:
    columns = get_table_columns(table)        # 字段信息
    primary_keys = get_primary_keys(table)    # 主键
    foreign_keys = get_foreign_keys(table)    # 外键
    constraints = get_table_constraints(table) # 约束

    if is_spatial_table(table):
        spatial_info = get_spatial_columns(table)  # 几何列
        spatial_indexes = get_spatial_indexes(table)
```

**格式化**：
```python
# SchemaFetcher.format_schema_for_llm()
"""
=== 数据库Schema信息 ===
数据库: PostgreSQL 14.0
PostGIS: 3.2.0
表数量: 3

--- 表结构 ---
表名: a_sight [空间表]
  字段:
    - gid: integer NOT NULL [PK]
    - name: character varying(100) NOT NULL
    - level: character varying(10) NULL
  空间列: geom (Point, SRID=4326)
  主键: gid
  外键: (无)
"""
```

---

### 4. PostgreSQL 事务错误防护

**问题**：SQL 失败后，事务进入 "aborted" 状态，后续 SQL 全部被忽略。

**解决方案**：启用 `autocommit` 模式
```python
# database.py: _connect()
self.raw_connection = psycopg2.connect(connection_string)
self.raw_connection.autocommit = True  # ✅ 每个查询自动提交
```

**优点**：
- SQL 失败后连接自动恢复
- 无需手动 `commit()` 或 `rollback()`
- 适合只读查询场景

---

## 数据库表结构

### 核心表

#### a_sight（景区基础表）
```sql
CREATE TABLE a_sight (
    gid SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    level VARCHAR(10),           -- 景区等级（如 '5A'）
    "所属省份" VARCHAR(50),
    "所属城市" VARCHAR(50),
    geom GEOMETRY(Point, 4326)
);
CREATE INDEX idx_a_sight_geom ON a_sight USING GIST(geom);
```

#### tourist_spot（景区详细信息表）
```sql
CREATE TABLE tourist_spot (
    name VARCHAR(100) PRIMARY KEY,
    "评分" NUMERIC(3, 1),
    "门票" VARCHAR(50),
    "介绍" TEXT,
    "图片链接" TEXT,
    "城市" VARCHAR(50)
);
```

**关系**：通过 `name` 字段关联（模糊匹配：`a.name LIKE t.name || '%'`）

---

## API 接口

### POST /query

**请求**：
```json
{
  "query": "查询浙江省的5A景区",
  "conversation_id": "uuid-123"  // 可选
}
```

**响应**：
```json
{
  "status": "success",
  "answer": "找到浙江省的5A景区共15个，包括杭州西湖、乌镇、普陀山等...",
  "data": [
    {
      "gid": 1,
      "name": "西湖",
      "level": "5A",
      "province": "浙江省",
      "city": "杭州市",
      "coordinates": [120.15, 30.28],
      "评分": 4.8,
      "门票": "免费",
      "介绍": "...",
      "图片链接": "http://..."
    }
  ],
  "count": 15,
  "message": "查询成功",
  "sql": "SELECT json_agg(...) FROM a_sight LEFT JOIN tourist_spot ..."
}
```

---

## 配置说明

### config.py

```python
class Settings:
    # LLM 配置
    LLM_PROVIDER = "deepseek"
    DEEPSEEK_API_KEY = "sk-..."
    DEEPSEEK_MODEL = "deepseek-chat"
    LLM_TEMPERATURE = 0.0

    # 数据库配置
    DATABASE_URL = "postgresql://user:pass@localhost:5432/dbname"
    DB_POOL_SIZE = 5
    DB_MAX_OVERFLOW = 10
    DB_POOL_TIMEOUT = 30
    DB_POOL_RECYCLE = 3600
    DB_CONNECT_TIMEOUT = 10

    # Agent 配置
    MAX_ITERATIONS = 10      # 最大迭代次数
    MAX_RETRIES = 5          # 最大重试次数
    ENABLE_SPATIAL = True    # 启用空间查询
    ENABLE_MEMORY = True     # 启用 Memory
    ENABLE_CHECKPOINT = True # 启用 Checkpoint

    # API 配置
    API_HOST = "0.0.0.0"
    API_PORT = 5001
    CORS_ORIGINS = ["http://localhost:5173"]
```

---

## 常见问题与解决方案

### 1. 递归限制错误（GraphRecursionError）

**原因**：工作流中出现无限循环。

**解决方案**：
- `handle_error` 必须清除 `error` 字段
- `execute_sql` 遇到 `current_sql=None` 时不报错，直接跳过
- `generate_sql` 发现数据完整时设置 `should_continue=False`

### 2. 事务被终止错误

**原因**：SQL 失败后事务进入 aborted 状态。

**解决方案**：启用 `autocommit` 模式。

### 3. SQL 生成字段名错误

**原因**：LLM 不知道准确的字段名。

**解决方案**：通过 `fetch_schema` 节点提供完整 Schema 信息。

### 4. 结果不完整

**原因**：`a_sight` 表缺少详细信息。

**解决方案**：多步迭代查询，自动 `LEFT JOIN tourist_spot` 补充。

---

## 开发指南

### 运行服务器
```bash
cd sight_server
python main.py
# 访问 http://localhost:5001/docs 查看 API 文档
```

### 运行测试
```bash
# Fallback 机制测试
python tests/test_fallback_mechanism.py

# 完整测试（需要数据库连接）
pytest tests/
```

### 添加新节点
1. 在 `core/graph/nodes.py` 的 `AgentNodes` 类中添加方法
2. 在 `core/graph/builder.py` 中添加节点到 workflow
3. 更新 `core/schemas.py` 的 `AgentState`（如需要新字段）

### 调试技巧
```python
# 查看思维链
result = agent.run_with_thought_chain(query)
for step in result["thought_chain"]:
    print(f"{step['step']}: {step['type']} - {step['status']}")

# 查看 SQL 历史
print("SQL History:", result["sql_history"])
```

---

## 性能优化建议

1. **Schema 缓存**：首次获取后缓存，避免重复查询
2. **连接池**：使用 SQLAlchemy 连接池（`pool_size=5`）
3. **限制结果集**：Fallback 简化查询时添加 `LIMIT 50`
4. **空间索引**：确保几何列有 GIST 索引
5. **LLM 并发**：使用异步调用（FastAPI + async/await）

---

## 未来改进方向

- [x] ~~支持更多数据库（MySQL、MongoDB）~~
- [x] ~~实现 RAG（检索增强生成）~~
- [x] ✅ **查询意图分析**（已完成，100%准确率）
- [x] ✅ **意图驱动的数据返回**（已完成）
- [x] ✅ **FROM子句错误三层防护**（已完成）
- [x] ✅ **FULL OUTER JOIN策略**（已完成）
- [ ] 添加查询缓存机制
- [ ] 支持多轮对话上下文
- [ ] 实现 SQL 查询优化器
- [ ] 添加权限控制和审计日志
- [ ] 支持流式输出（SSE）

---

## 重要文档索引

### 功能文档
- `INTENT_OPTIMIZATION_SUMMARY.md` - 查询意图分析优化详解（32个测试用例，100%通过）
- `INTENT_INFO_IN_RESPONSE.md` - API返回结果中的intent_info字段说明
- `FROM_CLAUSE_FIX_FINAL.md` - FROM子句错误三层防护机制
- `PROMPTS_UPDATE_SUMMARY.md` - FULL OUTER JOIN策略更新说明

### 测试文件
- `test_intent_optimization.py` - 意图分析测试（32个用例）
- `test_analyze_intent_only.py` - 意图分析单元测试
- `verify_prompts.py` - 提示词验证
- `final_check.py` - 完整性检查

---

## 许可证

MIT License

---

## 联系方式

项目维护者：Sight Server Team
GitHub：[项目仓库链接]

---

*最后更新：2025-10-04*
*版本：2.0.0*
*重大更新：查询意图分析系统 + FROM子句错误防护*
