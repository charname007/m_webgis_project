# Prompts.py 更新总结

## 更新时间
2025年10月4日

## 主要更新内容

### 1. JOIN 策略全面更新

#### 更新前的问题
- 混用 LEFT JOIN 和 FULL OUTER JOIN，没有明确区分使用场景
- tourist_spot 表中独有的数据会被 LEFT JOIN 丢失

#### 更新后的策略
```
✓ 通用查询 → 使用 FULL OUTER JOIN
  - 包含两表所有数据
  - 使用 COALESCE 处理 NULL 字段
  - 添加 _dataSource 标识数据来源

✓ 空间查询 → 使用 LEFT JOIN
  - 必须有坐标的查询（如"附近"、"距离"）
  - 以 a_sight 为主表（保证有坐标）

✓ UNION ALL 策略 → 推荐用于完整数据获取
  - 查询1：只在 a_sight 中的数据
  - 查询2：只在 tourist_spot 中的数据
  - 查询3：两表都有的数据
```

### 2. 查询意图分析完善

#### analyze_query_intent 方法
- ✓ 完整实现多维度意图分析
- ✓ 支持 query/summary 类型判断
- ✓ 支持空间查询检测
- ✓ 返回置信度和详细分析信息
- ✓ 修复正则表达式错误（[1-5]a 而非 [5-1]a）

#### 意图分析维度
```python
{
    "intent_type": "query" | "summary",
    "is_spatial": bool,
    "prompt_type": PromptType,
    "keywords_matched": List[str],
    "description": str,
    "confidence": float,
    "analysis_details": {
        "summary_score": 0.0-1.0,
        "spatial_score": 0.0-1.0,
        "scenic_score": 0.0-1.0,
        "matched_patterns": []
    }
}
```

### 3. Summary 查询优化

#### 禁止 json_agg 嵌套聚合
```sql
-- ✅ 正确：统计查询不使用 json_agg
SELECT
    '浙江省' as province,
    '5A' as level,
    COUNT(*) as count
FROM a_sight
WHERE "所属省份" = '浙江省' AND level = '5A'

-- ❌ 错误：统计查询不要用 json_agg 包裹 COUNT
SELECT json_agg(
    json_build_object(
        'count', COUNT(*)  -- 错误！嵌套聚合函数
    )
)
FROM a_sight
```

### 4. 数据完整性保障

#### _dataSource 元数据
```python
'_dataSource': CASE
    WHEN t.id IS NULL THEN 'a_sight_only'      # 仅基础信息
    WHEN a.gid IS NULL THEN 'tourist_spot_only'  # 仅详细信息
    ELSE 'joined'                               # 完整数据
END
```

#### COALESCE 空值处理
```python
'name': COALESCE(a.name, TRIM(SPLIT_PART(t.name, ' ', 1)))
'city': COALESCE(a."所属城市", t."城市", '')
'address': COALESCE(t."地址", a.address, '')
```

### 5. WHERE 条件适配

#### FULL OUTER JOIN 后的 WHERE
```sql
-- ✅ 正确：考虑两个表
WHERE a."所属省份" = '浙江省' OR t."城市" LIKE '%浙江%'

-- ❌ 错误：只考虑一个表（会过滤掉另一个表的数据）
WHERE a."所属省份" = '浙江省'
```

## 统计数据

### JOIN 使用频率
- FULL OUTER JOIN: 17 次
- LEFT JOIN: 16 次（主要用于空间查询和 UNION ALL 子查询）
- RIGHT JOIN: 3 次

### 关键特性覆盖
- ✓ 通用查询使用FULL OUTER JOIN
- ✓ 空间查询使用LEFT JOIN
- ✓ 禁止Summary使用json_agg
- ✓ COALESCE处理NULL
- ✓ _dataSource字段
- ✓ UNION ALL策略

## 测试验证

### analyze_query_intent 测试结果
```
✓ '查询浙江省的5A景区'
  - intent: query ✓
  - spatial: False ✓

✓ '统计浙江省有多少个5A景区'
  - intent: summary ✓
  - spatial: False ✓

✓ '查找距离杭州10公里内的景区'
  - intent: query ✓
  - spatial: True ✓

✓ '统计西湖周围5公里的景点数量'
  - intent: summary ✓
  - spatial: True ✓
```

## 决策树更新

```
收到查询请求时，按以下逻辑判断：

1. 是否是空间查询？（如"附近"、"距离XX公里"、"范围内"）
   ✅ YES → 使用 FROM a_sight LEFT JOIN tourist_spot（必须有坐标）
   ❌ NO → 继续判断

2. 是否仅需要景区列表？（如"列出所有5A景区"）
   ✅ YES → 使用 UNION ALL 策略 或 FULL OUTER JOIN
   ❌ NO → 继续判断

3. 是否需要景点详细信息？（如"景区介绍"、"门票价格"）
   ✅ YES → 使用 UNION ALL 策略 或 FULL OUTER JOIN
   ❌ NO → 继续判断

4. 是否需要统计/聚合？（如"统计数量"、"计数"）
   ✅ YES → 使用 UNION ALL + GROUP BY 或 FULL OUTER JOIN + GROUP BY
   ❌ NO → 继续判断

5. 默认情况（查询景区相关信息）
   → 使用 UNION ALL 策略 或 FULL OUTER JOIN
```

## 修复的Bug

### 1. 正则表达式字符范围错误
```python
# ❌ 错误
level_patterns = [
    (r'[5-1]a景区', 0.3)  # bad character range 5-1
]

# ✅ 修复
level_patterns = [
    (r'[1-5]a景区', 0.3)  # 正确范围
]
```

### 2. analyze_query_intent 方法不完整
- 修复前：方法未完整实现，直接跳到测试代码
- 修复后：完整实现意图分析逻辑，包括景区意图分析和综合判断

## 兼容性

### 向后兼容
- 保留所有原有方法签名
- get_scenic_query_prompt() 正常工作
- detect_query_type() 正常工作
- build_enhanced_query() 正常工作

### 新增功能
- analyze_query_intent() 完整实现
- 返回值包含 confidence 和 analysis_details

## 下一步建议

1. **测试真实查询**
   - 运行端到端测试验证 SQL 生成正确性
   - 确保 Agent 正确使用 FULL OUTER JOIN

2. **监控数据完整性**
   - 观察 _dataSource 分布
   - 确认是否有数据丢失

3. **性能优化**
   - FULL OUTER JOIN 可能比 LEFT JOIN 慢
   - 考虑添加索引优化

4. **文档更新**
   - 更新 API 文档
   - 添加查询示例
