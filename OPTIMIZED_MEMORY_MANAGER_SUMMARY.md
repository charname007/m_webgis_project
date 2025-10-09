# 优化内存管理器 (OptimizedMemoryManager) 总结

## 概述

`OptimizedMemoryManager` 是 Sight Server 中的核心内存管理组件，继承自 `MemoryManager` 基类，提供增强的内存管理功能，包括会话自动清理、性能优化和数据库持久化。

## 主要功能

### 1. 会话管理
- **多会话支持**: 同时管理多个会话，每个会话独立存储查询历史、上下文和性能数据
- **自动清理**: 基于TTL（生存时间）和最大会话数量自动清理过期会话
- **会话统计**: 跟踪每个会话的查询数量、成功率、响应时间等性能指标

### 2. 内存优化
- **步骤保存**: 支持不同级别的中间步骤保存（basic/debug/detailed/learning）
- **步骤压缩**: 可选的步骤数据压缩功能
- **内存监控**: 跟踪内存使用情况和清理统计

### 3. 数据库集成
- **持久化存储**: 将会话历史、查询记录、AI上下文保存到数据库
- **数据恢复**: 支持从数据库恢复会话状态和上下文
- **统计分析**: 从数据库获取完整的会话统计信息

### 4. 学习功能
- **模式学习**: 从成功/失败的查询中学习查询模式和SQL模板
- **性能统计**: 跟踪整体系统的查询性能指标
- **知识积累**: 构建跨会话的知识库

## 在 LangGraph 中的使用

### 集成方式

`OptimizedMemoryManager` 在 LangGraph 工作流中的使用方式：

```python
# 在 LangGraph 节点中使用
def sql_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # 获取内存管理器实例
    memory_manager = state.get("memory_manager")
    
    # 保存中间步骤
    memory_manager.save_step(
        step_type="sql_generation",
        step_data={
            "query": state["query"],
            "generated_sql": generated_sql,
            "intent_info": state.get("intent_info")
        },
        importance=2
    )
    
    # 添加查询历史
    memory_manager.add_query_to_session(
        query=state["query"],
        result=result,
        sql=generated_sql,
        success=True,
        response_time=response_time
    )
    
    return state
```

### 主要使用场景

1. **会话状态管理**
   - 在 `start_session` 中初始化会话
   - 在查询过程中维护会话上下文
   - 在会话结束时清理资源

2. **中间步骤追踪**
   - SQL生成步骤
   - SQL执行步骤  
   - 错误恢复步骤
   - 策略决策步骤

3. **性能监控**
   - 响应时间统计
   - 成功率跟踪
   - 查询模式分析

4. **知识积累**
   - 成功查询模式学习
   - 失败模式记录
   - 优化规则构建

## 配置选项

### 基本配置
```python
memory_manager = OptimizedMemoryManager(
    max_sessions=100,           # 最大会话数
    session_ttl=86400,          # 会话TTL（24小时）
    enable_auto_cleanup=True,   # 启用自动清理
)
```

### 高级配置
```python
memory_manager = OptimizedMemoryManager(
    enable_step_saving=True,           # 启用步骤保存
    step_saving_level="debug",         # 保存级别
    max_steps_per_session=1000,        # 最大步骤数
    enable_step_compression=True,      # 启用步骤压缩
    enable_database_persistence=True,  # 启用数据库持久化
    database_connector=db_connector    # 数据库连接器
)
```

## 数据流

```
用户查询 → LangGraph工作流 → 优化内存管理器
                                    ↓
会话管理 → 步骤保存 → 性能统计 → 数据库持久化
                                    ↓
模式学习 → 知识积累 → 查询优化 → 性能提升
```

## 优势

1. **性能优化**: 自动清理过期数据，减少内存占用
2. **可扩展性**: 支持多会话和大量查询历史
3. **可观测性**: 详细的步骤追踪和性能监控
4. **持久化**: 数据库集成确保数据不丢失
5. **智能学习**: 从历史查询中学习优化模式

## 测试验证

通过集成测试验证了以下功能：
- ✅ 会话创建和管理
- ✅ 查询历史记录
- ✅ 中间步骤保存
- ✅ 模式学习功能
- ✅ 数据库持久化
- ✅ 会话统计获取
- ✅ 自动清理功能

## 结论

`OptimizedMemoryManager` 是 Sight Server 中 LangGraph 工作流的关键组件，提供了强大的内存管理、性能监控和学习能力，显著提升了系统的稳定性和智能水平。
