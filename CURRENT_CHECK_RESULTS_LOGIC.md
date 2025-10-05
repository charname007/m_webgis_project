# 当前 check_results 节点执行逻辑详解

## 核心执行流程

### 1. 初始检查
```python
# 检查是否有数据
if not final_data:
    reason = "查询无结果"
    return {
        "should_continue": False,
        "reason": reason
    }
```

### 2. 数据完整性评估
```python
# 评估数据完整性
completeness = self.result_parser.evaluate_completeness(final_data)
```

**完整性评估标准**：
- `complete`: 布尔值，表示是否完整
- `completeness_score`: 完整度评分 (0.0-1.0)
- `missing_fields`: 缺失字段列表
- `records_with_missing`: 有缺失字段的记录数

### 3. 迭代控制决策逻辑

#### 停止迭代的条件（优先级从高到低）：
1. **达到最大迭代次数**
   ```python
   if current_step >= max_iterations - 1:
       reason = f"达到最大迭代次数 ({current_step + 1}/{max_iterations})"
       should_continue = False
   ```

2. **数据完整度达标**
   ```python
   elif completeness["complete"] or completeness["completeness_score"] >= 0.9:
       reason = f"数据完整度达标 ({completeness['completeness_score']:.1%})"
       should_continue = False
   ```

3. **首次查询完整度过低**
   ```python
   elif current_step == 0 and completeness["completeness_score"] < 0.15:
       reason = f"首次查询完整度过低 ({completeness['completeness_score']:.1%})，可能是数据源问题"
       should_continue = False
   ```

4. **所有记录字段完整**
   ```python
   elif completeness["records_with_missing"] == 0:
       reason = "所有记录字段完整"
       should_continue = False
   ```

### 4. LLM智能分析（如果可用）

#### 启发式判断规则：
```python
# 规则1：检查数据不足关键词
if any(keyword in analysis_lower for keyword in ['不足', '不够', '缺少', '缺失', '需要补充', '建议补充', '应该补充']):
    should_continue = True
    reason = "LLM分析认为数据不足，需要补充"

# 规则2：检查数据完整关键词  
elif any(keyword in analysis_lower for keyword in ['完整', '足够', '充分', '满足', '不需要补充', '无需补充']):
    should_continue = False
    reason = "LLM分析认为数据已足够完整"

# 规则3：检查改进建议关键词
elif any(keyword in analysis_lower for keyword in ['建议', '改进', '优化', '提升', '增强']):
    should_continue = True
    reason = "LLM分析提供了改进建议，需要补充数据"

# 规则4：数据量启发式
elif count < 5 and len(analysis_text) > 100:
    should_continue = True
    reason = f"数据量较少({count}条)且分析详细，建议补充更多数据"

# 默认情况
else:
    should_continue = False
    reason = "LLM分析未明确建议补充数据"
```

### 5. 补充建议提取

#### 建议提取流程：
1. **识别建议性内容**
   ```python
   if any(keyword in line.lower() for keyword in ['建议', '可以', '应该', '需要', '推荐', '考虑']):
   ```

2. **提取具体建议内容**
   ```python
   # 从标记后提取内容
   parts = line.split(marker, 1)
   if len(parts) > 1:
       content = parts[1].strip()
   ```

3. **分类建议类型**
   ```python
   # 基于关键词自动分类
   if any(keyword in content_lower for keyword in ['字段', '信息', '数据', '属性']):
       return "field_completion"
   elif any(keyword in content_lower for keyword in ['更多', '扩展', '增加', '补充']):
       return "data_expansion"
   # ... 其他类型
   ```

### 6. 返回结果结构

```python
return {
    "current_step": current_step + 1,
    "should_continue": should_continue,
    "thought_chain": [thought_step],
    # 如果有LLM分析结果
    "llm_analysis": llm_analysis,
    "supplement_suggestions": supplement_suggestions,
    "enhancement_guidance": guidance_for_next_step,
    "supplement_needed": should_continue
}
```

## 多轮查询支持机制

### 迭代控制参数：
- `max_iterations`: 最大迭代次数（默认3次）
- `current_step`: 当前迭代步数
- `should_continue`: 是否继续下一轮查询

### 状态传递：
- `final_data`: 累积的查询结果
- `sql_history`: SQL查询历史
- `supplement_suggestions`: 补充建议指导下一轮查询

## 与工作流的集成

### LangGraph工作流顺序：
1. `fetch_schema` → 2. `analyze_intent` → 3. `enhance_query` → 
4. `generate_sql` → 5. `execute_sql` → 6. `check_results` → 
7. `generate_answer`

### 循环机制：
- 如果 `check_results` 返回 `should_continue=True`
- 工作流会回到 `generate_sql` 节点
- 基于 `supplement_suggestions` 生成补充查询
- 继续执行直到 `should_continue=False` 或达到最大迭代次数

## 关键改进点

### 1. 移除了summary查询的特殊处理
- 原逻辑：summary查询不进行迭代
- 新逻辑：所有查询类型都进行LLM分析，summary也可能需要补充

### 2. 始终使用LLM分析
- 无论查询意图如何，都会调用LLM分析结果质量
- 提供更智能的补充建议

### 3. 启发式解析
- 不再依赖固定的预设类别
- 基于自然语言理解提取建议
- 更强的适应性

### 4. 智能迭代控制
- 基于多个因素综合决策
- 避免无意义的重复查询
- 在数据源问题明显时及时停止

## 实际执行示例

### 场景1：需要补充数据
```
用户查询: "查询浙江省的5A景区"
当前结果: 2条记录，缺少评分和门票信息
LLM分析: "数据不够完整，建议补充评分和门票价格"
决策: should_continue=True
补充建议: [{"type": "field_completion", "description": "补充评分和门票信息"}]
```

### 场景2：数据完整
```
用户查询: "查询浙江省的5A景区"  
当前结果: 10条记录，所有字段完整
LLM分析: "数据非常完整，不需要补充"
决策: should_continue=False
```

### 场景3：数据源问题
```
用户查询: "查询浙江省的5A景区"
当前结果: 0条记录
决策: should_continue=False
原因: "查询无结果"
```

这个逻辑确保了Agent能够智能地进行多轮SQL查询，在需要时补充数据，在数据足够时及时停止，避免不必要的查询开销。
