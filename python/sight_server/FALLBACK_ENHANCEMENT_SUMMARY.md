# Fallback 机制增强实现总结

## 已完成的工作 ✅

### 1. AgentState 数据模型更新
**文件**: `core/schemas.py`

**新增字段**：
```python
# 错误上下文
error_context: Optional[Dict[str, Any]]  # 完整错误上下文信息

# 日志追踪
query_id: str  # 唯一查询ID（UUID，用于日志追踪）
query_start_time: str  # 查询开始时间（ISO格式）
node_execution_logs: Annotated[List[Dict[str, Any]], add]  # 节点执行日志
```

**error_context 结构**：
```python
{
    "failed_sql": str,              # 出错的SQL语句
    "error_message": str,           # 完整错误信息
    "error_code": str,              # PostgreSQL错误码（如 "42P01"）
    "error_position": int,          # 错误位置（字符偏移）
    "failed_at_step": int,          # 出错步骤
    "query_context": {...},         # 查询上下文
    "database_context": {...},      # 数据库上下文
    "execution_context": {...}      # 执行上下文
}
```

### 2. 结构化日志系统创建
**文件**: `core/logging/structured_logger.py`

**核心功能**：
- JSON格式日志输出（JSONL）
- 8种日志类型（query_start, query_end, sql_execution, error_occurred等）
- 5种日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- 快捷方法：`log_query_start()`, `log_sql_execution()`, `log_error()`等

**日志示例**：
```json
{
  "timestamp": "2025-10-04T12:00:00",
  "type": "sql_execution",
  "level": "INFO",
  "query_id": "uuid-123",
  "sql": "SELECT ...",
  "step": 1,
  "status": "success",
  "duration_ms": 15.5,
  "rows_returned": 19
}
```

---

## 剩余实现步骤（待完成）

### 3. 修改 execute_sql 节点
**文件**: `core/graph/nodes.py` → `AgentNodes.execute_sql()`

**任务**：
1. 提取PostgreSQL错误码（使用正则从error中提取）
2. 提取表名（从SQL中解析）
3. 构建完整error_context
4. 添加结构化日志记录

**示例代码**：
```python
def execute_sql(self, state: AgentState) -> Dict[str, Any]:
    query_id = state.get("query_id", "unknown")
    start_time = time.time()

    try:
        # ... 执行SQL ...

        if execution_result["status"] == "error":
            # ✅ 构建错误上下文
            error_context = {
                "failed_sql": current_sql,
                "error_message": execution_result["error"],
                "error_code": self._extract_pg_error_code(execution_result["error"]),
                "error_position": self._extract_error_position(execution_result["error"]),
                "failed_at_step": current_step,
                "query_context": {
                    "original_query": state["query"],
                    "enhanced_query": state["enhanced_query"],
                    "intent_type": state.get("query_intent"),
                    "requires_spatial": state.get("requires_spatial", False)
                },
                "database_context": {
                    "schema_used": state.get("database_schema"),
                    "tables_accessed": self._extract_tables_from_sql(current_sql)
                },
                "execution_context": {
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "rows_affected": 0,
                    "timestamp": datetime.now().isoformat()
                }
            }

            # ✅ 记录错误日志
            if self.slog:
                self.slog.log_error(
                    query_id=query_id,
                    error_type="sql_execution_error",
                    error_message=execution_result["error"],
                    failed_sql=current_sql,
                    retry_count=state.get("retry_count", 0)
                )

            return {
                "error": execution_result["error"],
                "error_context": error_context,  # ✅ 传递完整上下文
                "should_continue": False
            }
    # ...
```

**辅助方法**（需要添加到AgentNodes类）：
```python
def _extract_pg_error_code(self, error_message: str) -> Optional[str]:
    """从PostgreSQL错误信息中提取错误码"""
    # 示例：ERROR:  column "xxx" does not exist
    # SQLSTATE: 42703
    pattern = r'SQLSTATE:\s*([0-9A-Z]{5})'
    match = re.search(pattern, error_message)
    return match.group(1) if match else None

def _extract_error_position(self, error_message: str) -> Optional[int]:
    """提取错误位置"""
    pattern = r'LINE\s+(\d+):|at character\s+(\d+)'
    match = re.search(pattern, error_message)
    if match:
        return int(match.group(1) or match.group(2))
    return None

def _extract_tables_from_sql(self, sql: str) -> List[str]:
    """从SQL中提取表名"""
    tables = []
    # FROM table1, FROM table1 JOIN table2
    pattern = r'FROM\s+([a-z_]+)|JOIN\s+([a-z_]+)'
    matches = re.findall(pattern, sql, re.IGNORECASE)
    for match in matches:
        tables.extend([t for t in match if t])
    return list(set(tables))
```

---

### 4. 修改 handle_error 节点
**文件**: `core/graph/nodes.py` → `AgentNodes.handle_error()`

**任务**：保留error_context并传递给下一步

**示例代码**：
```python
def handle_error(self, state: AgentState) -> Dict[str, Any]:
    error_context = state.get("error_context", {})  # ✅ 获取错误上下文

    # ... 错误分析 ...

    return {
        "retry_count": retry_count + 1,
        "last_error": error,
        "error_context": error_context,  # ✅ 保留完整上下文
        "fallback_strategy": strategy,
        "current_sql": None,  # 清空当前SQL（但error_context中保留了原始SQL）
        "error": None  # 清除错误标志，允许重试
    }
```

---

### 5. 修改 generate_sql 节点
**文件**: `core/graph/nodes.py` → `AgentNodes.generate_sql()`

**任务**：使用error_context中的failed_sql进行精准修复

**示例代码**：
```python
def generate_sql(self, state: AgentState) -> Dict[str, Any]:
    fallback_strategy = state.get("fallback_strategy")
    error_context = state.get("error_context", {})

    if fallback_strategy == "retry_sql":
        # ✅ 使用完整错误上下文修复SQL
        sql = self.sql_generator.fix_sql_with_context(
            failed_sql=error_context.get("failed_sql"),
            error_message=error_context.get("error_message"),
            error_code=error_context.get("error_code"),
            error_position=error_context.get("error_position"),
            query_context=error_context.get("query_context"),
            database_schema=state["database_schema"]
        )
        return {"current_sql": sql}
    # ...
```

---

### 6. 在 sql_generator.py 中添加 fix_sql_with_context 方法
**文件**: `core/processors/sql_generator.py` → `SQLGenerator`

**任务**：添加基于完整上下文的SQL修复方法

**示例代码**：
```python
def fix_sql_with_context(
    self,
    failed_sql: str,
    error_message: str,
    error_code: Optional[str] = None,
    error_position: Optional[int] = None,
    query_context: Optional[Dict] = None,
    database_schema: Optional[Dict] = None
) -> str:
    """
    使用完整错误上下文修复SQL

    Args:
        failed_sql: 出错的SQL
        error_message: 错误信息
        error_code: PostgreSQL错误码
        error_position: 错误位置
        query_context: 查询上下文
        database_schema: 数据库schema

    Returns:
        修复后的SQL
    """
    prompt = f"""你是PostgreSQL专家，需要修复以下SQL错误：

**出错SQL**:
{failed_sql}

**错误信息**:
{error_message}

**PostgreSQL错误码**: {error_code or '未知'}
**错误位置**: 字符偏移 {error_position or '未知'}

**查询上下文**:
- 原始查询: {query_context.get('original_query') if query_context else '未知'}
- 查询意图: {query_context.get('intent_type') if query_context else '未知'}
- 是否空间查询: {query_context.get('requires_spatial') if query_context else False}

**数据库Schema**:
{database_schema or '未提供'}

请修复SQL并直接返回修复后的完整SQL语句（不要解释）。
"""

    fixed_sql = self.llm.invoke(prompt)
    return self._clean_sql(fixed_sql)
```

---

### 7. 添加结构化日志到所有8个节点
**文件**: `core/graph/nodes.py`

为每个节点添加日志记录：

```python
# 示例：在 fetch_schema 节点中
def fetch_schema(self, state: AgentState) -> Dict[str, Any]:
    query_id = state.get("query_id", "unknown")
    start_time = time.time()

    try:
        # ... 执行逻辑 ...

        # ✅ 记录节点执行日志
        if self.slog:
            self.slog.log_node_execution(
                query_id=query_id,
                node_name="fetch_schema",
                step=0,
                duration_ms=(time.time() - start_time) * 1000,
                status="completed" if schema else "failed"
            )

        return {...}
```

对所有8个节点重复此模式。

---

### 8. 创建日志查询 API
**新文件**: `api/log_routes.py`

（代码见之前的设计方案）

---

### 9. 更新 agent.py 集成结构化日志
**文件**: `core/agent.py`

**任务**：
1. 初始化 StructuredLogger
2. 传递给 AgentNodes
3. 生成 query_id
4. 记录查询开始/结束

**示例代码**：
```python
from .logging import StructuredLogger
import uuid
from datetime import datetime

class SQLQueryAgent:
    def __init__(self, ...):
        # ✅ 初始化结构化日志器
        self.slog = StructuredLogger(
            log_file="logs/sight_server.jsonl",
            enable_console=True
        )

        # 传递给节点
        self.nodes = AgentNodes(
            ...,
            structured_logger=self.slog  # ✅ 传递日志器
        )

    def run(self, query: str) -> Dict:
        # ✅ 生成查询ID和开始时间
        query_id = str(uuid.uuid4())
        query_start_time = datetime.now().isoformat()
        start_time = time.time()

        # ✅ 记录查询开始
        self.slog.log_query_start(
            query=query,
            query_id=query_id
        )

        # 初始化state
        state = {
            "query": query,
            "query_id": query_id,  # ✅ 添加query_id
            "query_start_time": query_start_time,  # ✅ 添加开始时间
            "error_context": None,  # ✅ 初始化error_context
            ...
        }

        # 执行workflow
        result = self.workflow.invoke(state)

        # ✅ 记录查询结束
        duration_ms = (time.time() - start_time) * 1000
        self.slog.log_query_end(
            query_id=query_id,
            status=result["status"],
            duration_ms=duration_ms,
            count=len(result.get("final_data") or [])
        )

        return result
```

---

## 测试建议

### 测试场景1：SQL语法错误恢复
```python
# 输入查询：
query = "查询不存在字段xxx的景区"

# 预期行为：
# 1. SQL生成错误（SELECT xxx FROM a_sight）
# 2. execute_sql 构建 error_context（包含failed_sql, error_code: 42703）
# 3. handle_error 保留 error_context
# 4. generate_sql 使用 fix_sql_with_context() 修复
# 5. 修复后SQL成功执行

# 日志记录：
# - sql_execution (error)
# - error_occurred
# - error_retry
# - sql_execution (success)
# - error_recovered
```

### 测试场景2：日志查询API
```bash
# 启动服务器
python main.py

# 查询特定query_id的完整链路
curl http://localhost:5001/logs/query/{query_id}

# 查询最近24小时的错误
curl http://localhost:5001/logs/errors?hours=24

# 查询性能统计
curl http://localhost:5001/logs/performance?node_name=generate_sql
```

---

## 关键改进点总结

### 原问题1：错误SQL丢失 ✅
**解决**：通过 `error_context.failed_sql` 完整保留出错SQL

### 原问题2：日志不完整 ✅
**解决**：通过 `StructuredLogger` + `query_id` 实现完整链路追踪

### 核心优势
1. **精准SQL修复**：LLM获得完整SQL + 错误码 + 位置，修复成功率提升
2. **完整链路追踪**：通过query_id追踪从开始到结束的所有步骤
3. **错误可视化**：通过API查看错误统计、恢复率、高频错误类型
4. **性能优化**：识别慢节点，针对性优化

---

## 下一步行动

按照顺序完成剩余步骤（3-9），每步完成后测试验证，确保功能正常。
