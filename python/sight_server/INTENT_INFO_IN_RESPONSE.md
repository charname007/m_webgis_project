# intent_info 字段已添加到返回结果

## 修改时间
2025年10月4日

## 问题
用户发现返回结果中不包含 `intent_info` 字段。

## 原因分析
虽然：
1. ✅ `core/schemas.py` 的 `QueryResult` 模型已包含 `intent_info` 字段
2. ✅ `core/agent.py` 的 `run()` 方法已正确填充 `intent_info`
3. ✅ `core/graph/nodes.py` 的 `analyze_intent` 节点已保存完整意图信息

但是：
- ❌ `models/api_models.py` 的 `QueryResponse` 模型缺少 `intent_info` 字段
- ❌ `main.py` 的API端点构建响应时没有包含 `intent_info`

## 解决方案

### 1. 更新 API 响应模型
**文件**：`models/api_models.py`

**添加字段**：
```python
class QueryResponse(BaseModel):
    # ... 其他字段 ...

    intent_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="查询意图分析信息，包含 intent_type, is_spatial, keywords_matched 等"
    )
```

**示例**：
```json
{
  "status": "success",
  "answer": "浙江省共有19个5A级景区...",
  "data": [...],
  "count": 19,
  "sql": "SELECT ...",
  "execution_time": 1.23,
  "intent_info": {
    "intent_type": "query",
    "is_spatial": false,
    "prompt_type": "scenic_query",
    "keywords_matched": [],
    "description": "数据查询 - 景区查询(置信度:0.50)",
    "confidence": 0.50,
    "analysis_details": {
      "summary_score": 0.0,
      "spatial_score": 0.0,
      "scenic_score": 0.50,
      "matched_patterns": ["景区关键词: 景区"]
    }
  }
}
```

### 2. 更新 GET 查询端点
**文件**：`main.py` 第245-254行

**修改**：
```python
response = QueryResponse(
    status=QueryStatus(result_dict.get("status", "success")),
    answer=result_dict.get("answer", ""),
    data=result_dict.get("data"),
    count=result_dict.get("count", 0),
    message=result_dict.get("message", "查询成功"),
    sql=result_dict.get("sql") if include_sql else None,
    execution_time=round(execution_time, 2),
    intent_info=result_dict.get("intent_info")  # ✅ 添加意图信息
)
```

### 3. 更新 POST 查询端点
**文件**：`main.py` 第315-324行

**修改**：
```python
response = QueryResponse(
    status=QueryStatus(result_dict.get("status", "success")),
    answer=result_dict.get("answer", ""),
    data=result_dict.get("data"),
    count=result_dict.get("count", 0),
    message=result_dict.get("message", "查询成功"),
    sql=result_dict.get("sql") if request.include_sql else None,
    execution_time=round(execution_time, 2),
    intent_info=result_dict.get("intent_info")  # ✅ 添加意图信息
)
```

## 修改的文件

1. ✅ `models/api_models.py` - 添加 `intent_info` 字段到 `QueryResponse`
2. ✅ `main.py` - GET 端点添加 `intent_info`
3. ✅ `main.py` - POST 端点添加 `intent_info`

## intent_info 字段说明

### 字段结构
```typescript
interface IntentInfo {
  intent_type: "query" | "summary";           // 查询类型
  is_spatial: boolean;                        // 是否空间查询
  prompt_type: "scenic_query" | "spatial_query" | "general_query";
  keywords_matched: string[];                 // 匹配的关键词
  description: string;                        // 意图描述
  confidence: number;                         // 置信度 (0-1)
  analysis_details: {                         // 详细分析
    summary_score: number;                    // 统计查询得分
    spatial_score: number;                    // 空间查询得分
    scenic_score: number;                     // 景区查询得分
    matched_patterns: string[];               // 匹配的模式
  }
}
```

### 使用示例

#### Query 类型查询
```json
{
  "intent_type": "query",
  "is_spatial": false,
  "description": "数据查询 - 景区查询(置信度:0.50)",
  "confidence": 0.50
}
```

#### Summary 类型查询
```json
{
  "intent_type": "summary",
  "is_spatial": false,
  "description": "统计汇总查询(置信度:0.70)",
  "confidence": 0.70,
  "keywords_matched": ["统计", "数量"]
}
```

#### 空间查询
```json
{
  "intent_type": "query",
  "is_spatial": true,
  "description": "数据查询 - 空间查询(置信度:0.70)",
  "confidence": 0.70,
  "keywords_matched": ["附近", "周边"]
}
```

#### Summary + Spatial 组合
```json
{
  "intent_type": "summary",
  "is_spatial": true,
  "description": "统计汇总查询(置信度:0.70) - 空间查询(置信度:0.60)",
  "confidence": 0.52
}
```

## 前端使用建议

### 根据 intent_type 控制 UI
```javascript
// 根据查询类型决定是否显示数据表格
if (response.intent_info?.intent_type === 'summary') {
  // Summary 查询：只显示统计结果
  showSummary(response.answer, response.count);
} else {
  // Query 查询：显示完整数据列表
  showDataTable(response.data);
}
```

### 根据 is_spatial 显示地图
```javascript
// 空间查询显示地图
if (response.intent_info?.is_spatial) {
  showMap(response.data);
} else {
  hideMap();
}
```

### 显示置信度
```javascript
// 显示意图分析置信度
const confidence = response.intent_info?.confidence || 0;
if (confidence < 0.5) {
  showWarning('查询意图可能不明确');
}
```

## 验证方法

### API 测试
```bash
# GET 请求
curl "http://localhost:5001/query?q=浙江省有多少个5A景区&include_sql=true"

# POST 请求
curl -X POST "http://localhost:5001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "浙江省有多少个5A景区", "include_sql": true}'
```

### 检查响应
```json
{
  "status": "success",
  "answer": "...",
  "data": null,
  "count": 19,
  "sql": "SELECT ...",
  "execution_time": 1.23,
  "intent_info": {  // ✅ 应该存在
    "intent_type": "summary",
    "is_spatial": false,
    "confidence": 0.75
  }
}
```

## 总结

现在所有 API 端点的返回结果都包含 `intent_info` 字段，前端可以据此：
1. ✅ 判断查询类型（query/summary）决定UI展示方式
2. ✅ 判断是否空间查询，决定是否显示地图
3. ✅ 查看详细的意图分析信息用于调试
4. ✅ 根据置信度提示用户查询可能不明确
