# Memory 和 Checkpoint 功能增强总结

## 概述

本次更新为 Sight Server 的 SQL查询Agent 添加了两个重要功能：
1. **Memory机制** - 短期和长期记忆管理
2. **Checkpoint机制** - 断点续传和状态持久化
3. **最大迭代次数** - 从3次增加到10次

## 新增功能

### 1. Memory机制 (`core/memory.py`)

#### 功能说明
Memory机制提供智能的查询历史管理和模式学习功能。

#### 核心特性

**短期记忆 (Session Memory)**
- 记录当前会话的所有查询
- 追踪查询历史和上下文
- 支持会话ID关联多轮对话

**长期记忆 (Knowledge Base)**
- 跨会话的知识积累
- 学习成功和失败的查询模式
- 查询优化建议生成
- 相似查询检索

#### 主要方法

```python
class MemoryManager:
    def start_session(conversation_id: str) -> Dict
        # 开始新会话

    def add_query_to_session(query, result, sql, success) -> Dict
        # 添加查询到会话历史

    def learn_from_query(query, sql, result, success) -> Optional[Dict]
        # 从查询中学习模式

    def find_similar_queries(query, top_k=3) -> List[Dict]
        # 查找相似的历史查询

    def get_optimization_suggestions(query, sql) -> List[str]
        # 获取查询优化建议

    def export_memory() -> Dict
        # 导出记忆数据

    def import_memory(memory_data) -> bool
        # 导入记忆数据
```

#### 使用示例

```python
from core import SQLQueryAgent

# 创建启用Memory的Agent
agent = SQLQueryAgent(enable_memory=True)

# 执行查询（自动记录到Memory）
result = agent.run("查询浙江省的5A景区", conversation_id="user-001")

# 导出Memory数据
memory_data = agent.get_memory_export()

# 导入Memory数据（跨会话恢复知识）
agent.import_memory(memory_data)
```

### 2. Checkpoint机制 (`core/checkpoint.py`)

#### 功能说明
Checkpoint机制支持Agent执行状态的保存和恢复，实现断点续传。

#### 核心特性

**状态持久化**
- 保存Agent执行的完整状态
- 支持pickle和JSON双格式
- 自动生成checkpoint元数据

**断点续传**
- 从任意checkpoint恢复执行
- 支持异常恢复
- 保留执行历史

**自动管理**
- 自动保存（按步数间隔）
- 自动清理旧checkpoint
- Checkpoint列表和查询

#### 主要方法

```python
class CheckpointManager:
    def save_checkpoint(checkpoint_id, state, step) -> bool
        # 保存checkpoint

    def load_checkpoint(checkpoint_id) -> Optional[Dict]
        # 加载checkpoint

    def resume_from_checkpoint(checkpoint_id) -> Optional[Dict]
        # 从checkpoint恢复执行

    def list_checkpoints() -> List[Dict]
        # 列出所有checkpoint

    def delete_checkpoint(checkpoint_id) -> bool
        # 删除指定checkpoint

    def cleanup_old_checkpoints(keep_latest=10) -> int
        # 清理旧checkpoint

    def auto_save(state, step, save_interval=3) -> Optional[str]
        # 自动保存checkpoint
```

#### 使用示例

```python
from core import SQLQueryAgent

# 创建启用Checkpoint的Agent
agent = SQLQueryAgent(
    enable_checkpoint=True,
    checkpoint_dir="./checkpoints"
)

# 执行查询（自动保存checkpoint）
result = agent.run("查询浙江省的5A景区")

# 列出所有checkpoint
checkpoints = agent.list_checkpoints()
print(f"Found {len(checkpoints)} checkpoints")

# 从checkpoint恢复执行
result = agent.run(
    "继续之前的查询",
    resume_from_checkpoint="session_abc_final_1234567890"
)

# 清理旧checkpoint（保留最新10个）
deleted = agent.cleanup_old_checkpoints(keep_latest=10)
```

### 3. 最大迭代次数增强

**变更：**
- 最大迭代次数从 3 次增加到 **10 次**
- 支持更复杂的多步查询场景
- 提高数据完整性的概率

**位置：**
- `core/schemas.py` - AgentState.max_iterations 默认值
- `core/agent.py` - run() 和 run_with_thought_chain() 初始化状态

## 架构更新

### 新增文件

```
core/
├── memory.py           # ✨ NEW - Memory管理器
└── checkpoint.py       # ✨ NEW - Checkpoint管理器
```

### 更新文件

```
core/
├── schemas.py          # 更新 AgentState（添加Memory和Checkpoint字段）
├── agent.py            # 集成Memory和Checkpoint功能
└── __init__.py         # 导出新模块
```

### AgentState 新增字段

```python
class AgentState(TypedDict):
    # ... 原有字段 ...

    # ==================== Memory 机制 ====================
    session_history: Annotated[List[Dict[str, Any]], add]
    conversation_id: Optional[str]
    knowledge_base: Optional[Dict[str, Any]]
    learned_patterns: Annotated[List[Dict[str, Any]], add]

    # ==================== Checkpoint 机制 ====================
    checkpoint_id: Optional[str]
    checkpoint_step: Optional[int]
    is_resumed: bool
    last_checkpoint_time: Optional[str]
```

## API 更新

### SQLQueryAgent 新增参数

```python
class SQLQueryAgent:
    def __init__(
        self,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        enable_spatial: bool = True,
        prompt_type: PromptType = PromptType.SCENIC_QUERY,
        enable_memory: bool = True,           # ✨ NEW
        enable_checkpoint: bool = True,        # ✨ NEW
        checkpoint_dir: str = "./checkpoints", # ✨ NEW
        checkpoint_interval: int = 3           # ✨ NEW
    )
```

### run() 方法新增参数

```python
def run(
    self,
    query: str,
    conversation_id: Optional[str] = None,        # ✨ NEW
    resume_from_checkpoint: Optional[str] = None  # ✨ NEW
) -> str
```

### run_with_thought_chain() 返回值扩展

```python
{
    "status": "success",
    "final_answer": "...",
    "thought_chain": [...],
    "step_count": 6,
    "sql_queries_with_results": [...],
    "result_data": {...},
    "memory_info": {              # ✨ NEW
        "conversation_id": "...",
        "learned_patterns_count": 5,
        "session_queries_count": 3
    },
    "checkpoint_info": {          # ✨ NEW
        "checkpoint_id": "...",
        "checkpoint_step": 5,
        "is_resumed": false
    }
}
```

### 新增管理方法

```python
# Memory管理
agent.get_memory_export() -> Dict
agent.import_memory(memory_data: Dict) -> bool

# Checkpoint管理
agent.list_checkpoints() -> List[Dict]
agent.delete_checkpoint(checkpoint_id: str) -> bool
agent.cleanup_old_checkpoints(keep_latest: int = 10) -> int
```

## 完整使用示例

### 示例1: 基础使用（启用所有功能）

```python
from core import SQLQueryAgent

# 创建Agent（启用Memory和Checkpoint）
agent = SQLQueryAgent(
    enable_memory=True,
    enable_checkpoint=True,
    checkpoint_dir="./my_checkpoints"
)

# 执行查询
result = agent.run(
    "查询浙江省的5A景区",
    conversation_id="user-12345"
)

print(result)
```

### 示例2: 多轮对话（利用Memory）

```python
from core import SQLQueryAgent

agent = SQLQueryAgent(enable_memory=True)

# 第一轮对话
result1 = agent.run(
    "查询浙江省的5A景区",
    conversation_id="conversation-001"
)

# 第二轮对话（同一会话）
result2 = agent.run(
    "再查询杭州市的景区",
    conversation_id="conversation-001"
)

# Agent可以利用第一轮的查询经验优化第二轮查询
```

### 示例3: 断点续传（利用Checkpoint）

```python
from core import SQLQueryAgent

agent = SQLQueryAgent(enable_checkpoint=True)

# 查看可用的checkpoint
checkpoints = agent.list_checkpoints()
print(f"Available checkpoints: {len(checkpoints)}")

for cp in checkpoints:
    print(f"  - {cp['checkpoint_id']} at step {cp.get('state_summary', {}).get('current_step')}")

# 从checkpoint恢复
if checkpoints:
    latest_checkpoint = checkpoints[0]['checkpoint_id']
    result = agent.run(
        "继续执行",
        resume_from_checkpoint=latest_checkpoint
    )
```

### 示例4: 完整的思维链（包含Memory和Checkpoint信息）

```python
from core import SQLQueryAgent

agent = SQLQueryAgent(
    enable_memory=True,
    enable_checkpoint=True
)

result = agent.run_with_thought_chain(
    "统计浙江省有多少个5A景区",
    conversation_id="analysis-session-001"
)

print(f"Status: {result['status']}")
print(f"Answer: {result['final_answer']}")
print(f"Steps: {result['step_count']}")
print(f"SQL queries executed: {len(result['sql_queries_with_results'])}")

# Memory信息
if 'memory_info' in result:
    print(f"\nMemory Info:")
    print(f"  Conversation ID: {result['memory_info']['conversation_id']}")
    print(f"  Learned patterns: {result['memory_info']['learned_patterns_count']}")
    print(f"  Session queries: {result['memory_info']['session_queries_count']}")

# Checkpoint信息
if 'checkpoint_info' in result:
    print(f"\nCheckpoint Info:")
    print(f"  ID: {result['checkpoint_info']['checkpoint_id']}")
    print(f"  Step: {result['checkpoint_info']['checkpoint_step']}")
    print(f"  Resumed: {result['checkpoint_info']['is_resumed']}")
```

### 示例5: Memory导出和导入（跨会话知识迁移）

```python
from core import SQLQueryAgent
import json

# Session 1: 学习阶段
agent1 = SQLQueryAgent(enable_memory=True)

# 执行多个查询，积累知识
agent1.run("查询浙江省的5A景区", conversation_id="training-001")
agent1.run("查询杭州市的景区", conversation_id="training-001")
agent1.run("统计景区数量", conversation_id="training-001")

# 导出Memory
memory_data = agent1.get_memory_export()

# 保存到文件
with open("knowledge_base.json", "w", encoding="utf-8") as f:
    json.dump(memory_data, f, ensure_ascii=False, indent=2)

# Session 2: 应用阶段
agent2 = SQLQueryAgent(enable_memory=True)

# 导入Memory（复用之前学习的知识）
with open("knowledge_base.json", "r", encoding="utf-8") as f:
    memory_data = json.load(f)

agent2.import_memory(memory_data)

# 新查询可以利用之前学习的模式
result = agent2.run("查询江苏省的5A景区", conversation_id="production-001")
```

## 配置说明

### Memory配置

Memory默认启用，可通过参数控制：

```python
agent = SQLQueryAgent(
    enable_memory=True  # 启用/禁用Memory
)
```

### Checkpoint配置

Checkpoint支持多个配置项：

```python
agent = SQLQueryAgent(
    enable_checkpoint=True,           # 启用/禁用Checkpoint
    checkpoint_dir="./checkpoints",   # Checkpoint保存目录
    checkpoint_interval=3             # 每N步保存一次
)
```

## 性能优化

### Memory优化
- 使用轻量级的模式匹配算法
- 限制历史记录数量（自动清理旧记录）
- 支持选择性导出（只导出有价值的知识）

### Checkpoint优化
- 使用pickle快速序列化
- 同时保存JSON元数据（便于查看）
- 自动清理机制（避免磁盘占用）

## 向后兼容性

所有新功能都是**可选的**，默认启用但不影响原有API：

```python
# 原有API继续工作（自动启用Memory和Checkpoint）
agent = SQLQueryAgent()
result = agent.run("查询浙江省的5A景区")

# 如需禁用新功能
agent = SQLQueryAgent(
    enable_memory=False,
    enable_checkpoint=False
)
```

## 总结

### 新增功能清单

| 功能 | 描述 | 状态 |
|-----|------|-----|
| Memory机制 | 短期和长期记忆管理 | ✅ 已实现 |
| Checkpoint机制 | 断点续传和状态持久化 | ✅ 已实现 |
| 最大迭代次数 | 从3次增加到10次 | ✅ 已实现 |
| 会话ID支持 | 多轮对话关联 | ✅ 已实现 |
| 查询模式学习 | 自动学习成功模式 | ✅ 已实现 |
| 相似查询检索 | 查找历史相似查询 | ✅ 已实现 |
| 优化建议生成 | SQL查询优化建议 | ✅ 已实现 |
| Memory导出/导入 | 跨会话知识迁移 | ✅ 已实现 |
| Checkpoint自动保存 | 按步数间隔保存 | ✅ 已实现 |
| Checkpoint管理 | 列表、删除、清理 | ✅ 已实现 |

### 文件变更统计

- **新增文件**: 2个
  - `core/memory.py` (390行)
  - `core/checkpoint.py` (340行)

- **更新文件**: 3个
  - `core/schemas.py` - 添加Memory和Checkpoint字段
  - `core/agent.py` - 集成新功能（从350行增至646行）
  - `core/__init__.py` - 导出新模块

### 关键改进

1. **智能性提升** - Memory机制支持模式学习和优化建议
2. **可靠性提升** - Checkpoint机制支持断点续传和异常恢复
3. **性能提升** - 最大迭代次数增加到10次，提高数据完整性
4. **可维护性** - 模块化设计，清晰的职责划分

所有功能已实现并可立即使用！🎉
