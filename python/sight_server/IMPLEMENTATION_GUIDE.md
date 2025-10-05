# Fallback 机制增强 - 详细实现指南

本文档提供剩余步骤的详细实现代码和说明。

---

## 步骤1：在 nodes.py 中添加辅助方法

**文件**：`core/graph/nodes.py`

在 `AgentNodes` 类中添加以下辅助方法（在类的末尾，`handle_error` 方法之后）：

```python
    # ==================== 辅助方法（用于错误上下文构建）====================

    def _extract_pg_error_code(self, error_message: str) -> Optional[str]:
        """
        从PostgreSQL错误信息中提取错误码

        Args:
            error_message: 错误信息

        Returns:
            错误码（如 "42P01"）或 None
        """
        import re

        # 方法1：从SQLSTATE中提取
        pattern1 = r'SQLSTATE:\s*([0-9A-Z]{5})'
        match = re.search(pattern1, error_message)
        if match:
            return match.group(1)

        # 方法2：从错误信息中推断常见错误码
        error_lower = error_message.lower()
        if 'does not exist' in error_lower:
            if 'column' in error_lower:
                return "42703"  # undefined_column
            elif 'table' in error_lower or 'relation' in error_lower:
                return "42P01"  # undefined_table
        elif 'syntax error' in error_lower:
            return "42601"  # syntax_error
        elif 'permission denied' in error_lower:
            return "42501"  # insufficient_privilege

        return None

    def _extract_error_position(self, error_message: str) -> Optional[int]:
        """
        从错误信息中提取错误位置

        Args:
            error_message: 错误信息

        Returns:
            错误位置（字符偏移）或 None
        """
        import re

        # 提取LINE或at character
        pattern = r'LINE\s+(\d+):|at character\s+(\d+)'
        match = re.search(pattern, error_message)
        if match:
            return int(match.group(1) or match.group(2))

        return None

    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """
        从SQL中提取表名

        Args:
            sql: SQL语句

        Returns:
            表名列表
        """
        import re

        tables = []
        # FROM table1, FROM table1 JOIN table2
        pattern = r'FROM\s+([a-z_]+)|JOIN\s+([a-z_]+)'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        for match in matches:
            tables.extend([t for t in match if t])

        return list(set(tables))
```

---

## 步骤2：修改 execute_sql 方法

**文件**：`core/graph/nodes.py` → 第448行 `def execute_sql()`

### 2.1 在方法开始添加导入和时间记录

在 `execute_sql` 方法的开头添加：

```python
    def execute_sql(self, state: AgentState) -> Dict[str, Any]:
        """
        节点4: 执行SQL查询

        ... (原文档注释) ...
        """
        # ✅ 导入必要模块
        import time
        from datetime import datetime

        # ✅ 记录开始时间
        start_time = time.time()

        try:
            current_sql = state.get("current_sql")
            current_step = state.get("current_step", 0)

            # ... (原代码继续) ...
```

### 2.2 修改错误处理部分

找到 `if execution_result["status"] == "error"` 这部分代码（大约在第485行），替换为：

```python
            if execution_result["status"] == "error":
                # ✅ 计算执行耗时
                execution_time_ms = (time.time() - start_time) * 1000

                # ✅ 构建完整错误上下文
                error_context = {
                    "failed_sql": current_sql,
                    "error_message": execution_result["error"],
                    "error_code": self._extract_pg_error_code(execution_result["error"]),
                    "error_position": self._extract_error_position(execution_result["error"]),
                    "failed_at_step": current_step,
                    "query_context": {
                        "original_query": state.get("query"),
                        "enhanced_query": state.get("enhanced_query"),
                        "intent_type": state.get("query_intent"),
                        "requires_spatial": state.get("requires_spatial", False)
                    },
                    "database_context": {
                        "schema_used": state.get("database_schema"),
                        "tables_accessed": self._extract_tables_from_sql(current_sql)
                    },
                    "execution_context": {
                        "execution_time_ms": execution_time_ms,
                        "rows_affected": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                }

                # ✅ 记录结构化日志（如果日志器可用）
                if hasattr(self, 'slog') and self.slog:
                    query_id = state.get("query_id", "unknown")
                    self.slog.log_error(
                        query_id=query_id,
                        error_type="sql_execution_error",
                        error_message=execution_result["error"],
                        failed_sql=current_sql,
                        retry_count=state.get("retry_count", 0),
                        error_code=error_context["error_code"]
                    )

                # 执行失败，返回错误上下文
                return {
                    "error": execution_result["error"],
                    "error_context": error_context,  # ✅ 传递完整上下文
                    "should_continue": False,
                    "thought_chain": [{
                        "step": current_step + 4,
                        "type": "sql_execution",
                        "action": "execute_sql",
                        "input": current_sql,
                        "error": execution_result["error"],
                        "status": "failed"
                    }]
                }
```

### 2.3 添加成功执行的日志记录

在执行成功的返回语句前（大约在第549行），添加日志记录：

```python
            # ✅ 计算执行耗时
            execution_time_ms = (time.time() - start_time) * 1000

            # ✅ 记录SQL成功执行日志
            if hasattr(self, 'slog') and self.slog:
                query_id = state.get("query_id", "unknown")
                self.slog.log_sql_execution(
                    query_id=query_id,
                    sql=current_sql,
                    step=current_step,
                    status="success",
                    duration_ms=execution_time_ms,
                    rows_returned=execution_result.get("count", 0)
                )

            return {
                "current_result": current_result,
                "final_data": final_data,
                # ... (其余返回字段) ...
            }
```

---

## 步骤3：修改 handle_error 方法

**文件**：`core/graph/nodes.py` → 第778行 `def handle_error()`

### 在返回字典中保留 error_context

找到所有的 `return` 语句，确保包含 `error_context`：

```python
    def handle_error(self, state: AgentState) -> Dict[str, Any]:
        """
        节点7: 增强的错误处理和重试

        ... (原文档注释) ...
        """
        try:
            error = state.get("error") or state.get("last_error")
            retry_count = state.get("retry_count", 0)
            current_sql = state.get("current_sql")
            current_step = state.get("current_step", 0)

            # ✅ 获取错误上下文
            error_context = state.get("error_context", {})

            # 获取增强的错误处理器（如果可用）
            error_handler = getattr(self, 'error_handler', None)

            if error_handler:
                # ... (使用增强错误处理器的代码) ...

                # ✅ 在所有返回语句中添加 error_context
                if not retry_strategy["should_retry"]:
                    return {
                        "error": f"错误无法恢复 ({retry_strategy['reason']}): {error}",
                        "error_type": error_analysis["error_type"],
                        "fallback_strategy": "fail",
                        "should_continue": False,
                        "error_context": error_context,  # ✅ 保留错误上下文
                        "error_history": [error_record],
                        "thought_chain": [thought_step]
                    }

                # ... (其他策略的返回语句也要添加 error_context) ...

                if retry_strategy["strategy_type"] == "retry_sql":
                    return {
                        "retry_count": retry_count + 1,
                        "last_error": error,
                        "error_type": error_analysis["error_type"],
                        "fallback_strategy": retry_strategy["strategy_type"],
                        "error_context": error_context,  # ✅ 保留
                        "error_history": [error_record],
                        "current_sql": None,
                        "error": None,
                        "thought_chain": [thought_step]
                    }
```

同样修改 `_handle_error_basic` 方法中的所有返回语句。

---

## 步骤4：修改 generate_sql 方法

**文件**：`core/graph/nodes.py` → `def generate_sql()`

### 在 fallback_strategy == "retry_sql" 分支使用错误上下文

找到 `generate_sql` 方法中处理 `retry_sql` 策略的部分，修改为：

```python
    def generate_sql(self, state: AgentState) -> Dict[str, Any]:
        """
        节点3: 生成SQL查询

        ... (原代码) ...
        """
        try:
            # ... (原代码) ...

            fallback_strategy = state.get("fallback_strategy")
            error_context = state.get("error_context", {})  # ✅ 获取错误上下文

            # ✅ 修改：使用错误上下文修复SQL
            if fallback_strategy == "retry_sql":
                self.logger.info(f"[Node: generate_sql] Retry SQL with error context")

                # ✅ 使用 fix_sql_with_context 方法（需要在 sql_generator.py 中实现）
                sql = self.sql_generator.fix_sql_with_context(
                    failed_sql=error_context.get("failed_sql"),
                    error_message=error_context.get("error_message"),
                    error_code=error_context.get("error_code"),
                    error_position=error_context.get("error_position"),
                    query_context=error_context.get("query_context"),
                    database_schema=state.get("database_schema")
                )

                return {
                    "current_sql": sql,
                    "thought_chain": [{
                        "step": current_step + 3,
                        "type": "sql_generation",
                        "action": "fix_sql_with_context",
                        "input": {
                            "failed_sql": error_context.get("failed_sql"),
                            "error_code": error_context.get("error_code")
                        },
                        "output": sql,
                        "status": "completed"
                    }]
                }
```

---

## 步骤5：在 sql_generator.py 中添加 fix_sql_with_context 方法

**文件**：`core/processors/sql_generator.py`

在 `SQLGenerator` 类中添加此方法（在类的末尾）：

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
            failed_sql: 出错的SQL语句
            error_message: 完整错误信息
            error_code: PostgreSQL错误码（如 "42P01"）
            error_position: 错误位置（字符偏移）
            query_context: 查询上下文
            database_schema: 数据库schema

        Returns:
            修复后的SQL语句
        """
        self.logger.info(f"[SQLGenerator] Fixing SQL with context: error_code={error_code}")

        # 构建详细的修复提示词
        prompt = f"""你是PostgreSQL专家，需要修复以下SQL错误：

**出错SQL**:
```sql
{failed_sql}
```

**错误信息**:
{error_message}

**PostgreSQL错误码**: {error_code or '未知'}
**错误位置**: 字符偏移 {error_position or '未知'}

**查询上下文**:
- 原始查询: {query_context.get('original_query') if query_context else '未知'}
- 查询意图: {query_context.get('intent_type') if query_context else '未知'}
- 是否空间查询: {query_context.get('requires_spatial') if query_context else False}

**数据库Schema**:
{self._format_schema_brief(database_schema) if database_schema else '未提供'}

**修复要求**:
1. 根据错误码 {error_code} 确定错误类型
2. 修复SQL中的具体问题
3. 确保修复后的SQL符合PostgreSQL语法
4. 保持原SQL的查询逻辑不变

请直接返回修复后的完整SQL语句（不要添加任何解释或markdown格式）。
"""

        # 调用LLM修复
        fixed_sql = self.llm.invoke(prompt)

        # 清理SQL（去除可能的markdown标记）
        fixed_sql = self._clean_sql(fixed_sql)

        self.logger.info(f"[SQLGenerator] Fixed SQL: {fixed_sql[:100]}...")

        return fixed_sql

    def _format_schema_brief(self, schema: Dict) -> str:
        """格式化简要schema信息"""
        if not schema:
            return "无"

        brief = []
        for table_name, table_info in schema.items():
            if isinstance(table_info, dict) and 'columns' in table_info:
                columns = [col['name'] for col in table_info['columns'][:5]]  # 只显示前5个字段
                brief.append(f"- {table_name}: {', '.join(columns)}")

        return "\n".join(brief[:3])  # 只显示前3个表

    def _clean_sql(self, sql: str) -> str:
        """清理SQL语句"""
        import re

        # 移除markdown代码块标记
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*$', '', sql)
        sql = sql.strip()

        return sql
```

---

## 步骤6：在 __init__ 方法中初始化 StructuredLogger

**文件**：`core/graph/nodes.py` → `AgentNodes.__init__()`

在初始化方法中添加 `slog` 参数：

```python
    def __init__(
        self,
        sql_generator,
        sql_executor,
        result_parser,
        answer_generator,
        schema_fetcher,
        llm=None,
        error_handler=None,
        cache_manager=None,
        structured_logger=None  # ✅ 新增：结构化日志器
    ):
        """初始化节点函数 ..."""
        self.sql_generator = sql_generator
        self.sql_executor = sql_executor
        self.result_parser = result_parser
        self.answer_generator = answer_generator
        self.schema_fetcher = schema_fetcher
        self.llm = llm
        self.error_handler = error_handler
        self.cache_manager = cache_manager
        self.slog = structured_logger  # ✅ 保存结构化日志器
        self.logger = logger
```

---

## 完整实现checklist

- [ ] 添加辅助方法到 `nodes.py`
- [ ] 修改 `execute_sql` 方法（添加错误上下文构建）
- [ ] 修改 `handle_error` 方法（保留错误上下文）
- [ ] 修改 `generate_sql` 方法（使用错误上下文）
- [ ] 在 `sql_generator.py` 中添加 `fix_sql_with_context` 方法
- [ ] 更新 `AgentNodes.__init__` 添加 `structured_logger` 参数
- [ ] 创建日志查询API（参考 `FALLBACK_ENHANCEMENT_SUMMARY.md`）
- [ ] 更新 `agent.py` 集成 StructuredLogger（参考 `FALLBACK_ENHANCEMENT_SUMMARY.md`）

---

## 测试步骤

### 1. 测试错误上下文构建

```python
# 创建测试脚本 test_error_context.py
from core.agent import SQLQueryAgent

agent = SQLQueryAgent(...)

# 故意触发错误（查询不存在的字段）
result = agent.run("查询所有景区的xxx字段")

# 检查error_context
print("Error Context:", result.get("error_context"))
# 应该包含: failed_sql, error_code: "42703", error_message等
```

### 2. 测试SQL修复

```python
# 触发SQL错误，观察是否能自动修复
result = agent.run("查询浙江省的5A景区")

# 检查思维链中是否有 fix_sql_with_context 步骤
for step in result["thought_chain"]:
    if step["action"] == "fix_sql_with_context":
        print("Found SQL fix step:", step)
```

### 3. 测试结构化日志

```bash
# 运行查询后查看日志文件
cat logs/sight_server.jsonl

# 应该看到JSON格式的日志，包含：
# - query_start
# - sql_execution (error)
# - error_occurred
# - sql_execution (success)
# - query_end
```

---

## 故障排查

### 问题1：AttributeError: 'AgentNodes' object has no attribute 'slog'

**解决**：确保在创建 `AgentNodes` 时传递了 `structured_logger` 参数。

### 问题2：fix_sql_with_context 未定义

**解决**：确保在 `SQLGenerator` 类中添加了该方法。

### 问题3：日志文件为空

**解决**：检查 `logs/` 目录是否存在，并确保 StructuredLogger 被正确初始化。

---

*最后更新：2025-10-04*
