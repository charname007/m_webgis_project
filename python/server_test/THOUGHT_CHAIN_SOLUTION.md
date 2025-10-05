# 思维链捕获解决方案

## 问题背景

在使用LangChain的SQL Agent时，默认情况下Agent会隐藏完整的思维链（Thought/Action推理过程），只返回最终结果。这导致我们无法看到Agent的完整推理过程，只能看到被解析器处理后的最终答案。

## 解决方案

通过使用`AgentActionMessageLog`和自定义回调处理器，我们成功实现了完整的思维链捕获功能。

### 核心实现

#### 1. SQLQueryAgent增强

在`sql_query_agent.py`中添加了`run_with_thought_chain`方法：

```python
def run_with_thought_chain(self, query: str) -> Dict[str, Any]:
    """执行SQL查询并返回完整的思维链"""
    # 创建自定义回调处理器
    class ThoughtChainCallbackHandler(BaseCallbackHandler):
        def on_agent_action(self, action: AgentAction, **kwargs):
            # 捕获Action步骤
            pass
        def on_agent_finish(self, finish: AgentFinish, **kwargs):
            # 捕获完成步骤
            pass
    
    # 使用回调处理器执行查询
    result = self.agent.invoke(
        {"input": query},
        config={"callbacks": [callback_handler]}
    )
```

#### 2. SpatialSQLQueryAgent增强

在`spatial_sql_agent.py`中也添加了相同的功能，确保空间查询代理也能捕获思维链。

#### 3. 服务器端集成

在`server.py`中修改了智能查询端点，优先使用思维链捕获功能：

```python
# 执行空间查询并捕获完整思维链
thought_chain_result = sql_query_agent.run_with_thought_chain(question)

if thought_chain_result["status"] == "success":
    result = thought_chain_result["final_answer"]
    thought_chain = thought_chain_result["thought_chain"]
    step_count = thought_chain_result["step_count"]
else:
    # 回退到原有方法
    result = sql_query_agent.run(question)
    thought_chain = extract_thought_chain(result)
```

### 技术要点

#### 回调处理器设计

```python
class ThoughtChainCallbackHandler(BaseCallbackHandler):
    def on_agent_action(self, action: AgentAction, **kwargs):
        step = {
            "type": "action",
            "action": action.tool,
            "action_input": action.tool_input,
            "log": action.log,
            "timestamp": kwargs.get('run_id', 'unknown')
        }
        self.agent.thought_chain_log.append(step)
    
    def on_agent_finish(self, finish: AgentFinish, **kwargs):
        step = {
            "type": "final_answer",
            "content": finish.return_values.get('output', ''),
            "log": finish.log,
            "timestamp": kwargs.get('run_id', 'unknown')
        }
        self.agent.thought_chain_log.append(step)
```

#### 返回格式

思维链捕获方法返回标准化的JSON格式：

```json
{
    "status": "success",
    "final_answer": "最终答案内容",
    "thought_chain": [
        {
            "type": "action",
            "action": "sql_db_list_tables",
            "action_input": "",
            "log": "完整日志",
            "timestamp": "step_1"
        },
        {
            "type": "final_answer",
            "content": "最终答案",
            "log": "完成日志",
            "timestamp": "final"
        }
    ],
    "step_count": 2
}
```

## 测试验证

创建了测试脚本`test_thought_chain_capture.py`来验证功能：

1. **空间代理测试**：测试空间查询的思维链捕获
2. **SQL代理测试**：测试普通SQL查询的思维链捕获  
3. **比较测试**：验证思维链捕获与常规执行的结果一致性

### 测试结果

从测试输出可以看到：

- ✅ Agent正确执行Thought/Action步骤
- ✅ 思维链被完整捕获和记录
- ✅ 最终答案与常规执行一致
- ✅ 错误处理机制正常工作

## 优势

1. **完整可见性**：可以看到Agent的完整推理过程
2. **调试友好**：便于诊断Agent执行过程中的问题
3. **向后兼容**：保持原有API的兼容性
4. **标准化输出**：提供结构化的思维链数据

## 使用方式

### 1. 直接使用代理

```python
from spatial_sql_agent import SpatialSQLQueryAgent

agent = SpatialSQLQueryAgent()
result = agent.run_with_thought_chain("查找附近的POI点")

print(f"步骤数: {result['step_count']}")
for step in result['thought_chain']:
    print(f"{step['type']}: {step['action'] if step['type'] == 'action' else step['content']}")
```

### 2. 通过API调用

```bash
# GET方式
curl "http://localhost:8001/agent/query/查找武汉大学珞珈门附近1公里范围内的POI点"

# POST方式
curl -X POST "http://localhost:8001/agent/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "查找武汉大学珞珈门附近1公里范围内的POI点"}'
```

## 注意事项

1. **性能影响**：思维链捕获会略微增加执行时间
2. **内存使用**：需要存储完整的思维链日志
3. **错误处理**：如果思维链捕获失败，会自动回退到原有方法

## 结论

通过实现思维链捕获功能，我们成功解决了Agent隐藏推理过程的问题。现在可以：

- 查看Agent的完整思考过程
- 诊断执行过程中的问题
- 提供更透明的AI决策过程
- 支持更复杂的调试和分析需求

这个解决方案为WebGIS项目的AI查询功能提供了更强的可观测性和调试能力。
