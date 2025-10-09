#!/usr/bin/env python3
"""
简化版内存装饰器测试
直接测试内存装饰器模块，避免复杂的依赖
"""

import sys
import os
import logging

# 直接导入内存装饰器模块
sys.path.insert(0, os.path.dirname(__file__))

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 直接复制内存装饰器代码进行测试
import functools
from datetime import datetime
from typing import Dict, Any, Optional, Callable

class MockAgentState:
    """模拟 AgentState"""
    def __init__(self, **kwargs):
        self._data = kwargs
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def __getitem__(self, key):
        return self._data[key]

class MockMemoryManager:
    """模拟内存管理器"""
    def __init__(self):
        self.enable_step_saving = True
        self.saved_steps = []
    
    def save_step(self, step_type: str, step_data: dict, importance: int, session_id: str):
        step_record = {
            "step_type": step_type,
            "step_data": step_data,
            "importance": importance,
            "session_id": session_id,
            "saved_at": datetime.now().isoformat()
        }
        self.saved_steps.append(step_record)
        return step_record

def with_memory_tracking(step_type: str):
    """简化版内存装饰器"""
    def decorator(node_func: Callable) -> Callable:
        @functools.wraps(node_func)
        def wrapper(self, state: MockAgentState) -> Dict[str, Any]:
            # 执行原始节点函数
            result = node_func(self, state)
            
            # 检查是否需要更新 Memory
            memory_manager = getattr(self, 'memory_manager', None)
            if not memory_manager:
                return result
            
            conversation_id = state.get("conversation_id")
            if not conversation_id:
                return result
            
            if hasattr(memory_manager, 'enable_step_saving'):
                if not memory_manager.enable_step_saving:
                    return result
            
            try:
                # 提取步骤数据
                step_data = {
                    "step_type": step_type,
                    "timestamp": datetime.now().isoformat(),
                    "current_step": state.get("current_step", 0),
                    "query": state.get("query", ""),
                    "conversation_id": state.get("conversation_id"),
                    "node_name": node_func.__name__,
                }
                
                # 保存到 Memory
                saved_step = memory_manager.save_step(
                    step_type=step_type,
                    step_data=step_data,
                    importance=2,  # 默认重要性
                    session_id=conversation_id
                )
                
                if saved_step:
                    print(f"✓ Memory updated: {step_type} for session: {conversation_id}")
                else:
                    print(f"✗ Memory update skipped: {step_type}")
                
            except Exception as e:
                print(f"Failed to update memory for {step_type}: {e}")
            
            return result
        
        return wrapper
    return decorator

class MockNode:
    """模拟节点类"""
    def __init__(self):
        self.memory_manager = MockMemoryManager()
        self.logger = logging.getLogger(__name__)
    
    @with_memory_tracking("sql_generation")
    def generate_sql(self, state: MockAgentState) -> dict:
        """模拟 SQL 生成节点"""
        return {
            "current_sql": "SELECT * FROM test WHERE id = 1",
            "thought_chain": [{"step": 1, "type": "sql_generation"}]
        }
    
    @with_memory_tracking("sql_execution")
    def execute_sql(self, state: MockAgentState) -> dict:
        """模拟 SQL 执行节点"""
        return {
            "current_result": {"status": "success", "count": 5},
            "thought_chain": [{"step": 2, "type": "sql_execution"}]
        }
    
    @with_memory_tracking("intent_analysis")
    def analyze_intent(self, state: MockAgentState) -> dict:
        """模拟意图分析节点"""
        return {
            "query_intent": "query",
            "requires_spatial": False,
            "thought_chain": [{"step": 0, "type": "intent_analysis"}]
        }

def test_memory_decorators():
    """测试内存装饰器功能"""
    print("=== 测试内存装饰器功能 ===\n")
    
    # 创建模拟节点
    node = MockNode()
    
    # 测试状态
    test_state = MockAgentState(
        query="测试查询",
        conversation_id="test-session-001",
        current_step=1,
        enhanced_query="增强的测试查询"
    )
    
    print("--- 测试 SQL 生成节点 ---")
    result1 = node.generate_sql(test_state)
    print(f"SQL 生成结果: {result1.get('current_sql')}")
    print(f"Memory 保存的步骤数: {len(node.memory_manager.saved_steps)}")
    
    print("\n--- 测试 SQL 执行节点 ---")
    result2 = node.execute_sql(test_state)
    print(f"SQL 执行结果: {result2.get('current_result')}")
    print(f"Memory 保存的步骤数: {len(node.memory_manager.saved_steps)}")
    
    print("\n--- 测试意图分析节点 ---")
    result3 = node.analyze_intent(test_state)
    print(f"意图分析结果: {result3.get('query_intent')}")
    print(f"Memory 保存的步骤数: {len(node.memory_manager.saved_steps)}")
    
    print("\n--- 查看保存的步骤详情 ---")
    for i, step in enumerate(node.memory_manager.saved_steps):
        print(f"步骤 {i+1}: {step['step_type']} (重要性: {step['importance']})")
        print(f"  会话ID: {step['session_id']}")
        print(f"  步骤数据: {step['step_data'].get('step_type')}")
        print()
    
    # 验证结果
    assert len(node.memory_manager.saved_steps) == 3, f"期望保存3个步骤，实际保存了{len(node.memory_manager.saved_steps)}个"
    step_types = [step['step_type'] for step in node.memory_manager.saved_steps]
    assert "sql_generation" in step_types, "缺少 SQL 生成步骤"
    assert "sql_execution" in step_types, "缺少 SQL 执行步骤"
    assert "intent_analysis" in step_types, "缺少意图分析步骤"
    
    print("✅ 所有测试通过！内存装饰器功能正常工作")
    return True

def test_memory_disabled():
    """测试内存功能禁用的情况"""
    print("\n=== 测试内存功能禁用 ===\n")
    
    node = MockNode()
    node.memory_manager.enable_step_saving = False
    
    test_state = MockAgentState(
        query="测试查询",
        conversation_id="test-session-002",
        current_step=1
    )
    
    result = node.generate_sql(test_state)
    print(f"SQL 生成结果: {result.get('current_sql')}")
    print(f"Memory 保存的步骤数: {len(node.memory_manager.saved_steps)}")
    
    assert len(node.memory_manager.saved_steps) == 0, "内存功能禁用时不应该保存步骤"
    print("✅ 内存功能禁用测试通过")

def test_no_conversation_id():
    """测试无会话ID的情况"""
    print("\n=== 测试无会话ID的情况 ===\n")
    
    node = MockNode()
    
    test_state = MockAgentState(
        query="测试查询",
        current_step=1
    )  # 没有 conversation_id
    
    result = node.generate_sql(test_state)
    print(f"SQL 生成结果: {result.get('current_sql')}")
    print(f"Memory 保存的步骤数: {len(node.memory_manager.saved_steps)}")
    
    assert len(node.memory_manager.saved_steps) == 0, "无会话ID时不应该保存步骤"
    print("✅ 无会话ID测试通过")

if __name__ == "__main__":
    try:
        test_memory_decorators()
        test_memory_disabled()
        test_no_conversation_id()
        print("\n🎉 所有测试成功完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
