#!/usr/bin/env python3
"""
测试内存装饰器功能
验证为实际使用的节点类添加的内存装饰器是否正常工作
"""

import sys
import os
import logging

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from sight_server.core.graph.nodes.memory_decorators import with_memory_tracking
from sight_server.schemas import AgentState

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
            "saved_at": "2025-01-01T00:00:00"
        }
        self.saved_steps.append(step_record)
        return step_record

class MockNode:
    """模拟节点类"""
    def __init__(self):
        self.memory_manager = MockMemoryManager()
        self.logger = logging.getLogger(__name__)
    
    @with_memory_tracking("sql_generation")
    def generate_sql(self, state: AgentState) -> dict:
        """模拟 SQL 生成节点"""
        return {
            "current_sql": "SELECT * FROM test WHERE id = 1",
            "thought_chain": [{"step": 1, "type": "sql_generation"}]
        }
    
    @with_memory_tracking("sql_execution")
    def execute_sql(self, state: AgentState) -> dict:
        """模拟 SQL 执行节点"""
        return {
            "current_result": {"status": "success", "count": 5},
            "thought_chain": [{"step": 2, "type": "sql_execution"}]
        }
    
    @with_memory_tracking("intent_analysis")
    def analyze_intent(self, state: AgentState) -> dict:
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
    test_state = {
        "query": "测试查询",
        "conversation_id": "test-session-001",
        "current_step": 1,
        "enhanced_query": "增强的测试查询"
    }
    
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

def test_importance_levels():
    """测试重要性级别映射"""
    print("\n=== 测试重要性级别映射 ===\n")
    
    from sight_server.core.graph.nodes.memory_decorators import get_step_importance
    
    test_cases = [
        ("sql_generation", 3),
        ("sql_execution", 4),
        ("error_handling", 2),
        ("intent_analysis", 2),
        ("result_validation", 2),
        ("check_results", 2),
        ("generate_answer", 4),
        ("fetch_schema", 1),
        ("enhance_query", 1),
        ("unknown_type", 1)
    ]
    
    for step_type, expected_importance in test_cases:
        importance = get_step_importance(step_type)
        status = "✅" if importance == expected_importance else "❌"
        print(f"{status} {step_type}: 期望={expected_importance}, 实际={importance}")
    
    print("\n✅ 重要性级别映射测试完成")

if __name__ == "__main__":
    try:
        test_memory_decorators()
        test_importance_levels()
        print("\n🎉 所有测试成功完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
