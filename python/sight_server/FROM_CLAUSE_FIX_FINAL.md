# FROM子句错误根本解决方案

## 问题根源

### 为什么反复出现 "丢失FROM子句项" 错误？

1. **LLM幻觉问题**：LLM有时会生成不完整的SQL，即使提示词中强调了FROM子句
2. **重试提示词不足**：`fix_sql_with_error` 的提示词不够明确，LLM在修复时仍可能犯同样错误
3. **缺少验证机制**：生成的SQL没有经过结构验证就直接执行

### 错误SQL示例
```sql
SELECT json_agg(
    json_build_object(
        'name', COALESCE(a.name, TRIM(SPLIT_PART(t.name, ' ', 1))),
        'level', a.level,
        'province', a."所属省份"
    )
) as result
WHERE a."所属省份" = '浙江省'  -- ❌ 使用了a但没有FROM a_sight a
```

## 三层防护方案

### 第1层：增强提示词

#### 初始SQL生成提示词
**文件**: `core/processors/sql_generator.py` 第37-69行

```python
template="""你是一个PostgreSQL + PostGIS SQL查询专家...

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

🚨 必须检查：如果SQL中出现 a.xxx 或 t.xxx，FROM子句必须定义对应的别名！
"""
```

#### SQL修复提示词
**文件**: `core/processors/sql_generator.py` 第333-369行

```python
fix_prompt = f"""你是一个SQL修复专家...

🚨 SQL必须包含的完整结构（按顺序检查）：
1. SELECT json_agg(...) as result
2. FROM 表名 别名   ← 这一行必须存在！
3. WHERE 条件（可选）

常见错误修复：
❌ 错误："丢失FROM子句项" / "missing FROM-clause entry"
   → 原因：使用了 a.xxx 或 t.xxx 但缺少 FROM 子句
   → 修复：添加 FROM a_sight a FULL OUTER JOIN tourist_spot t ON ...

修复步骤：
1. 检查是否有 FROM 子句
2. 检查所有使用的表别名（a, t）是否在 FROM 中定义
3. 检查字段名是否正确
4. 检查是否有正确的连接条件
"""
```

### 第2层：SQL结构验证

**新增方法**: `_validate_sql_structure(sql: str) -> bool`
**位置**: `core/processors/sql_generator.py` 第391-426行

**验证逻辑**：
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

### 第3层：自动修复机制

**新增方法**: `_add_from_clause_if_missing(sql: str, query: str) -> str`
**位置**: `core/processors/sql_generator.py` 第428-481行

**修复逻辑**：
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
    elif uses_t:
        from_clause = "FROM tourist_spot t"

    # 3. 智能插入FROM子句
    if 有WHERE:
        在WHERE前插入FROM
    else:
        在SQL末尾插入FROM

    return fixed_sql
```

## 完整防护流程

### 初始SQL生成
```
1. LLM生成SQL
2. _extract_sql() 提取清理
3. _validate_sql_structure() 验证   ← 新增
4. 如果验证失败：
   → _add_from_clause_if_missing() 自动修复   ← 新增
   → 再次验证
5. 返回SQL
```

### SQL错误修复
```
1. 接收错误的SQL和错误信息
2. 使用增强的fix_prompt调用LLM   ← 改进
3. _extract_sql() 提取清理
4. _validate_sql_structure() 验证   ← 新增
5. 如果验证失败：
   → _add_from_clause_if_missing() 自动修复   ← 新增
6. 返回修复后的SQL
```

## 代码修改总结

### 修改的方法

1. **generate_initial_sql()** - 添加验证和自动修复
   ```python
   # ✅ 验证SQL结构
   if not self._validate_sql_structure(sql):
       self.logger.warning("Generated SQL missing proper FROM clause, attempting to fix")
       sql = self._add_from_clause_if_missing(sql, query)
   ```

2. **fix_sql_with_error()** - 增强提示词和添加验证
   ```python
   # 增强的修复提示词
   fix_prompt = f"""..."""

   # ✅ 验证修复后的SQL
   if not self._validate_sql_structure(fixed_sql):
       fixed_sql = self._add_from_clause_if_missing(fixed_sql, query)
   ```

### 新增的方法

3. **_validate_sql_structure()** - 验证SQL结构完整性
   - 检查FROM关键字
   - 检查表别名定义
   - 返回验证结果

4. **_add_from_clause_if_missing()** - 自动添加缺失的FROM子句
   - 智能检测使用的表别名
   - 构建正确的FROM子句
   - 在合适位置插入

## 预期效果

### Before（修复前）
```
查询: "浙江省的5A景区"

第1次生成 → 缺少FROM → 执行失败 ❌
第1次重试 → 仍然缺少FROM → 执行失败 ❌
第2次重试 → 仍然缺少FROM → 执行失败 ❌
...
第5次重试 → 达到最大重试次数 → 返回错误 ❌
```

### After（修复后）
```
查询: "浙江省的5A景区"

第1次生成 → LLM生成SQL
         → 验证检测到缺少FROM ✅
         → 自动添加FROM子句 ✅
         → 再次验证通过 ✅
         → 执行成功 ✅

如果仍然失败：
第1次重试 → LLM修复SQL（增强提示词）
         → 验证检测到问题（如果有）
         → 自动修复
         → 执行成功 ✅
```

## 测试建议

### 测试用例

```python
# 测试1：简单查询
query = "浙江省的5A景区"
# 预期：即使LLM生成缺少FROM的SQL，也能自动修复

# 测试2：统计查询
query = "浙江省有多少个5A景区"
# 预期：生成正确的COUNT查询

# 测试3：复杂查询
query = "查找浙江省和江苏省的5A景区，按评分排序"
# 预期：正确处理多条件和排序

# 测试4：空间查询
query = "杭州附近10公里的景区"
# 预期：生成包含ST_DWithin的空间查询
```

### 验证点

1. ✅ 检查生成的SQL是否包含FROM子句
2. ✅ 检查日志中是否有"Auto-added FROM clause"
3. ✅ 检查SQL执行是否成功
4. ✅ 检查结果是否正确

## 日志示例

### 成功自动修复的日志
```
WARNING - Generated SQL missing proper FROM clause, attempting to fix
INFO - Auto-added FROM clause to SQL
INFO - Generated initial SQL: SELECT json_agg(...) FROM a_sight a...
INFO - Executing SQL: SELECT json_agg(...) FROM a_sight a WHERE...
INFO - SQL executed successfully, 15 records returned
```

### 重试修复的日志
```
ERROR - SQL execution failed: 错误: 对于表"a",丢失FROM子句项
INFO - Error classified as: sql_syntax_error
INFO - Fallback strategy: retry_sql
INFO - Attempting to fix SQL with error: 丢失FROM子句项
WARNING - Fixed SQL still missing FROM clause, adding it manually
INFO - Auto-added FROM clause to SQL
INFO - SQL executed successfully
```

## 监控建议

### 关键指标

1. **FROM子句错误率**
   - 监控：`错误信息包含 "丢失FROM" 的次数 / 总查询次数`
   - 目标：< 1%

2. **自动修复成功率**
   - 监控：`Auto-added FROM clause 日志次数 / FROM错误次数`
   - 目标：> 95%

3. **重试成功率**
   - 监控：`retry_sql后成功次数 / retry_sql次数`
   - 目标：> 90%

## 总结

通过三层防护机制：

1. **第1层（提示词）**：减少LLM生成错误SQL的概率
2. **第2层（验证）**：及时发现SQL结构问题
3. **第3层（自动修复）**：自动修复常见的FROM子句缺失问题

**预期效果**：
- ✅ 大幅降低FROM子句错误的发生频率
- ✅ 即使发生错误，也能自动修复
- ✅ 提升整体查询成功率到 >95%
- ✅ 减少用户看到错误的概率
