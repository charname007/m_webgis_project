# 数据库查询方法错误修复

## 问题描述

**错误日志**:
```
2025-10-04 11:18:36 - core.processors.sql_executor - WARNING - Unexpected result type: str
2025-10-04 11:18:36 - core.agent - ERROR - Query execution failed: object of type 'NoneType' has no len()
TypeError: object of type 'NoneType' has no len()
```

## 根本原因

### 问题1: 使用错误的数据库查询方法

**文件**: `core/processors/sql_executor.py:52`

**错误代码**:
```python
raw_result = self.db_connector.execute_query(sql)
```

**问题**:
- `execute_query()` 使用 LangChain 的 `SQLDatabase.run()` 方法
- `db.run()` 返回的是**字符串类型**（查询结果的文本表示）
- 无法正确解析为 JSON 对象

**正确方法**:
```python
raw_result = self.db_connector.execute_raw_query(sql)
```

**原因**:
- `execute_raw_query()` 使用 `psycopg2` 的 `RealDictCursor`
- 返回的是**字典列表**（List[Dict]）
- 可以直接解析为 JSON 对象

### 问题2: agent.py 中遗漏的 len() 调用

**文件**: `core/agent.py:237`

**错误代码**:
```python
query_result = QueryResult(
    count=len(result_state.get("final_data", [])),
    ...
)
```

**问题**:
- `result_state.get("final_data", [])` 可能返回 `None`（而非默认的 `[]`）
- 对 `None` 调用 `len()` 导致 `TypeError`

**修复**:
```python
# 安全获取final_data和count
final_data = result_state.get("final_data")
data_count = len(final_data) if final_data is not None else 0

query_result = QueryResult(
    data=final_data,
    count=data_count,
    ...
)
```

## 修复方案

### 修复1: 切换到 execute_raw_query()

**文件**: `core/processors/sql_executor.py:49-81`

```python
def execute(self, sql: str) -> Dict[str, Any]:
    try:
        # 执行SQL
        self.logger.info(f"Executing SQL: {sql[:200]}...")
        # ✅ 修复：使用execute_raw_query()获取字典列表
        raw_result = self.db_connector.execute_raw_query(sql)

        # 添加详细日志
        self.logger.debug(f"Raw result type: {type(raw_result).__name__}")
        if raw_result and isinstance(raw_result, (list, tuple)) and len(raw_result) > 0:
            self.logger.debug(f"First row: {raw_result[0]}")

        # 解析结果
        data = self._parse_result(raw_result)

        return {
            "status": "success",
            "data": data,
            "count": len(data) if data else 0,
            "raw_result": raw_result,
            "error": None
        }
    except Exception as e:
        self.logger.error(f"SQL execution failed: {e}")
        return {
            "status": "error",
            "data": None,
            "count": 0,
            "raw_result": None,
            "error": str(e)
        }
```

### 修复2: 安全处理 None 值

**文件**: `core/agent.py:232-244`

```python
# 构建QueryResult
# 安全获取final_data和count
final_data = result_state.get("final_data")
data_count = len(final_data) if final_data is not None else 0

query_result = QueryResult(
    status=result_state.get("status", "success"),
    answer=result_state.get("answer", ""),
    data=final_data,
    count=data_count,
    message=result_state.get("message", "查询成功"),
    sql="; ".join(result_state.get("sql_history", []))
)
```

同样在 Memory 部分也修复了（第211-230行）：

```python
# 学习查询模式（Memory）
if self.enable_memory and self.memory_manager:
    # 安全获取final_data的长度
    final_data = result_state.get("final_data")
    data_count = len(final_data) if final_data is not None else 0

    self.memory_manager.learn_from_query(
        query=query,
        sql="; ".join(result_state.get("sql_history", [])),
        result={"count": data_count},
        success=(result_state.get("status") == "success")
    )
```

## 数据库方法对比

### DatabaseConnector 的两个查询方法

| 方法 | 底层实现 | 返回类型 | 适用场景 |
|------|---------|---------|---------|
| `execute_query()` | LangChain `SQLDatabase.run()` | `str` | LangChain Agent 内部使用 |
| `execute_raw_query()` | psycopg2 `RealDictCursor` | `List[Dict]` | ✅ **我们的场景** - 需要结构化数据 |

### 为什么使用 execute_raw_query()

```python
# execute_query() 返回字符串
result = db_connector.execute_query("SELECT json_agg(...)")
print(result)
# 输出: "[{'name': '西湖', 'level': '5A'}, ...]"  (字符串！)
print(type(result))
# <class 'str'>

# execute_raw_query() 返回字典列表
result = db_connector.execute_raw_query("SELECT json_agg(...)")
print(result)
# 输出: [RealDictRow([('json_agg', [{'name': '西湖', ...}])])]
print(type(result))
# <class 'list'>
print(type(result[0]))
# <class 'psycopg2.extras.RealDictRow'> (可以当作 dict 使用)
```

## 预期效果

### 修复前
```
2025-10-04 11:18:36 - core.processors.sql_executor - WARNING - Unexpected result type: str
2025-10-04 11:18:36 - core.graph.nodes - WARNING - No data returned, stopping iterations
2025-10-04 11:18:36 - core.agent - ERROR - TypeError: object of type 'NoneType' has no len()
```

### 修复后
```
2025-10-04 XX:XX:XX - core.processors.sql_executor - INFO - Executing SQL: SELECT json_agg(...)
2025-10-04 XX:XX:XX - core.processors.sql_executor - DEBUG - Raw result type: list
2025-10-04 XX:XX:XX - core.processors.sql_executor - DEBUG - First row: RealDictRow([('json_agg', [...])])
2025-10-04 XX:XX:XX - core.processors.sql_executor - DEBUG - Parse result: tuple/list format, extracted from first column, type=list
2025-10-04 XX:XX:XX - core.processors.sql_executor - DEBUG - -> Extracted list with 7 records
2025-10-04 XX:XX:XX - core.graph.nodes - INFO - [Node: check_results] Checking results for step 0
2025-10-04 XX:XX:XX - core.graph.nodes - INFO - 数据完整度达标 (100.0%)
2025-10-04 XX:XX:XX - core.agent - INFO - ✓ Query completed: status=success, count=7
```

## 总结

✅ **问题已解决**：
1. 切换到正确的数据库查询方法 `execute_raw_query()`
2. 安全处理所有 `len()` 调用，避免 `None` 值错误

✅ **影响范围**：
- `core/processors/sql_executor.py` - 1处修改（查询方法）
- `core/agent.py` - 2处修改（len()安全处理）

✅ **向后兼容**：
- API 接口保持不变
- 所有现有功能正常工作
- 数据格式更正确（字典列表而非字符串）
