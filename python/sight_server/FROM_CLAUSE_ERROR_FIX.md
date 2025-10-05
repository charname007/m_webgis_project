# FROM子句错误修复

## 问题
用户报告错误：
```
错误: 对于表"a",丢失FROM子句项
LINE 3: 'name', COALESCE(a.name, TRIM(SPLIT_PART(t.name, ' '...
```

## 原因分析

### 1. LLM生成了不完整的SQL
生成的SQL缺少FROM子句：
```sql
SELECT json_agg(
    json_build_object(
        'name', COALESCE(a.name, TRIM(SPLIT_PART(t.name, ' ', 1))),
        'level', a.level,
        ...
    )
)
WHERE ...  -- 使用了a.xxx但没有FROM a_sight a
```

### 2. 错误分类器未识别
错误 "丢失FROM子句项" 被分类为 `unknown_error`，而不是 `sql_syntax_error`，导致：
- 无法触发正确的重试策略
- 错误处理不够精准

## 解决方案

### 1. 修复错误分类器
**文件**: `core/graph/nodes.py`

**添加FROM子句错误识别**：
```python
def _classify_error(self, error: Optional[str]) -> str:
    # ...
    # ✅ 新增：FROM子句错误
    elif any(keyword in error_lower for keyword in ["from子句", "丢失from", "missing from", "from-clause"]):
        return "sql_syntax_error"
```

### 2. 增强SQL生成提示词
**文件**: `core/processors/sql_generator.py`

**改进前**：
```python
template="""你是一个SQL查询专家...
要求：
1. 必须使用 json_agg(json_build_object(...))
2. 根据查询意图选择最佳连接策略...
3. 🚨 绝对必须包含完整的 FROM 子句
...
"""
```

**改进后**：
```python
template="""你是一个PostgreSQL + PostGIS SQL查询专家...

🚨 绝对必需的SQL结构（按顺序）：
1. SELECT json_agg(...) as result
2. FROM 表名 别名   ← 必须有这一行！
3. WHERE 条件

❌ 错误示例（缺少FROM子句）：
SELECT json_agg(json_build_object('name', a.name))
WHERE a.level = '5A'   ← 错误：使用了a但没有FROM a_sight a

✅ 正确示例（完整的FROM子句）：
SELECT json_agg(json_build_object('name', a.name)) as result
FROM a_sight a   ← 正确：FROM子句定义了别名a
WHERE a.level = '5A'

🚨 必须检查：如果SQL中出现 a.xxx 或 t.xxx，FROM子句必须定义对应的别名！
"""
```

**改进点**：
1. ✅ 明确SQL结构的顺序要求
2. ✅ 提供错误示例和正确示例对比
3. ✅ 使用视觉标记（❌ ✅ ←）突出关键点
4. ✅ 简化语言，更直接明了

## 修改的文件

1. ✅ `core/graph/nodes.py` - 第808-848行
   - 添加FROM子句错误识别关键词

2. ✅ `core/processors/sql_generator.py` - 第36-69行
   - 增强SQL生成提示词
   - 添加错误/正确示例对比

## 错误处理流程

### Before（修复前）
```
1. LLM生成缺少FROM子句的SQL
2. SQL执行失败："丢失FROM子句项"
3. 错误分类器 → unknown_error
4. 使用通用重试策略
5. 可能再次生成相同错误的SQL
```

### After（修复后）
```
1. LLM生成SQL（提示词更明确）
2. 如果仍然失败："丢失FROM子句项"
3. 错误分类器 → sql_syntax_error ✅
4. 策略 → retry_sql（重新生成SQL）✅
5. 使用增强的提示词重新生成
6. 成功概率显著提高
```

## 测试建议

### 测试用例
```bash
# 测试1：简单查询
"浙江省的5A景区"

# 测试2：统计查询
"浙江省有多少个5A景区"

# 测试3：空间查询
"杭州附近的景区"

# 测试4：复杂组合查询
"统计杭州周围10公里的5A景区数量"
```

### 验证点
1. ✅ 生成的SQL包含完整的FROM子句
2. ✅ 所有使用的表别名都在FROM子句中定义
3. ✅ 如果出现FROM错误，能正确识别并重试
4. ✅ 重试后生成正确的SQL

## 相关错误类型

### 已识别的SQL语法错误
```python
sql_syntax_errors = [
    "syntax error",           # 语法错误
    "near",                   # 语法附近错误
    "unexpected",             # 意外的标记
    "aggregate",              # 聚合函数错误
    "聚合",
    "嵌套",
    "from子句",               # ✅ 新增
    "丢失from",               # ✅ 新增
    "missing from",           # ✅ 新增
    "from-clause"             # ✅ 新增
]
```

## 预防措施

### 提示词最佳实践
1. ✅ 提供错误示例和正确示例对比
2. ✅ 使用视觉标记突出关键点
3. ✅ 明确SQL结构的顺序要求
4. ✅ 强调检查点（"必须检查：..."）
5. ✅ 简化语言，避免冗长描述

### 错误分类器最佳实践
1. ✅ 识别多种语言的错误信息（中文+英文）
2. ✅ 包含常见的错误变体
3. ✅ 按优先级分类（语法 > 字段 > 权限）
4. ✅ 为每种错误类型定义明确的重试策略

## 总结

本次修复：
1. ✅ 增强了错误识别能力（FROM子句错误）
2. ✅ 改进了SQL生成提示词（更清晰的示例）
3. ✅ 提高了错误恢复成功率

预期效果：
- 减少FROM子句错误的发生频率
- 即使发生错误，也能快速识别并正确重试
- 提升整体查询成功率
