# SQL历史记录缺失修复

## 问题描述

用户报告查询结果中 `sql: null`，SQL语句没有被记录。

## 根本原因

### 问题：SQL记录逻辑混乱

**原设计**:
- `generate_sql` 节点：生成SQL并添加到 `sql_history`
- `execute_sql` 节点：只执行SQL，不记录历史

**问题**:
1. 当 `generate_sql` 返回 `current_sql: None` 时（跳过生成的情况），SQL不会被记录
2. SQL在生成时就记录，但如果执行失败，历史中会有未执行的SQL
3. 职责不清：生成和记录耦合在一起

## 修复方案

### 新设计：职责分离

**原则**:
- `generate_sql` 节点：只负责生成SQL，设置到 `current_sql`
- `execute_sql` 节点：执行SQL后，将其添加到 `sql_history`

### 修复1: generate_sql 节点不记录历史

**文件**: `core/graph/nodes.py:230-244`

**修复前**:
```python
return {
    "current_sql": sql,
    "sql_history": [sql],  # ❌ 在生成时就记录
    "thought_chain": [thought_step]
}
```

**修复后**:
```python
# ✅ 修复：不在generate_sql中添加到sql_history，让execute_sql统一处理
return {
    "current_sql": sql,
    "thought_chain": [thought_step]
}
```

### 修复2: execute_sql 节点记录历史

**文件**: `core/graph/nodes.py:333-340`

**修复前**:
```python
return {
    "current_result": current_result,
    "final_data": final_data,
    "execution_results": [current_result],
    # ❌ 缺少 sql_history
    "thought_chain": [thought_step]
}
```

**修复后**:
```python
# ✅ 修复：确保SQL被记录到sql_history
return {
    "current_result": current_result,
    "final_data": final_data,
    "execution_results": [current_result],
    "sql_history": [current_sql],  # ✅ 执行后记录SQL
    "thought_chain": [thought_step]
}
```

## 工作流程

### 修复前
```
generate_sql → 生成SQL → 记录到sql_history
                ↓
execute_sql → 执行SQL → (无记录)
```

**问题**:
- 如果生成SQL但跳过执行，SQL会被记录但未执行
- 如果执行失败，历史中有失败的SQL但无错误标记

### 修复后
```
generate_sql → 生成SQL → 设置current_sql
                ↓
execute_sql → 执行SQL → 记录到sql_history
```

**优势**:
- ✅ 只有成功执行的SQL才会被记录
- ✅ 职责清晰：生成与记录分离
- ✅ 历史准确：sql_history 只包含实际执行过的SQL

## AgentState 中的 sql_history

**定义**: `core/schemas.py:62`
```python
sql_history: Annotated[List[str], add]  # 所有执行过的 SQL
```

**说明**:
- `Annotated[List[str], add]` 使用 LangGraph 的 `add` reducer
- 每次节点返回 `{"sql_history": [sql]}` 时，会自动追加到列表中
- 不会覆盖，只会累积

## 预期效果

### 修复前
```json
{
  "status": "success",
  "count": 0,
  "sql": null,  // ❌ SQL未被记录
  "data": null
}
```

### 修复后
```json
{
  "status": "success",
  "count": 7,
  "sql": "SELECT json_agg(json_build_object('name', a.name, ...)) FROM a_sight a LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%' WHERE a.city = '杭州' AND a.level = '5A'",  // ✅ SQL正确记录
  "data": [...]
}
```

## 测试验证

**测试场景**:
1. ✅ 正常查询 → SQL被记录
2. ✅ 查询返回空数据 → SQL仍被记录
3. ✅ 多步查询 → 所有SQL都被记录（用分号连接）
4. ✅ 查询失败 → SQL不会被记录（因为未执行成功）

## 总结

✅ **问题已解决**：SQL现在会正确记录到历史中

✅ **架构优化**：
- 生成与记录职责分离
- 只记录成功执行的SQL
- 更清晰的数据流

✅ **影响范围**：
- `core/graph/nodes.py` - 2处修改
  - `generate_sql` 节点：移除 sql_history 记录
  - `execute_sql` 节点：添加 sql_history 记录
