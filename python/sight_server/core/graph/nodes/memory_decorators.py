"""
Memory 装饰器模块 - Sight Server
为 LangGraph 节点提供实时上下文更新功能
"""

import logging
import functools
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from ...schemas import AgentState

logger = logging.getLogger(__name__)


def with_memory_update(step_type: str, importance: int = 1):
    """
    装饰器：在 LangGraph 节点执行后自动更新 Memory 上下文
    
    Args:
        step_type: 步骤类型（如：sql_generation, sql_execution, error_handling）
        importance: 重要性级别（1-4，数字越大越重要）
    
    Returns:
        装饰后的节点函数
    """
    def decorator(node_func: Callable) -> Callable:
        @functools.wraps(node_func)
        def wrapper(self, state: AgentState) -> Dict[str, Any]:
            # 执行原始节点函数
            result = node_func(self, state)
            
            # 检查是否需要更新 Memory
            if not _should_update_memory(self, state):
                return result
            
            try:
                # 提取步骤数据
                step_data = _extract_step_data(
                    step_type=step_type,
                    state=state,
                    result=result,
                    node_func=node_func
                )
                
                # 保存到 Memory
                memory_manager = getattr(self, 'memory_manager', None)
                if memory_manager:
                    saved_step = memory_manager.save_step(
                        step_type=step_type,
                        step_data=step_data,
                        importance=importance,
                        session_id=state.get("conversation_id")
                    )
                    
                    if saved_step:
                        logger.debug(
                            f"✓ Memory updated: {step_type} (importance: {importance}) "
                            f"for session: {state.get('conversation_id')}"
                        )
                    else:
                        logger.debug(
                            f"✗ Memory update skipped: {step_type} "
                            f"(step saving disabled or filtered out)"
                        )
                
            except Exception as e:
                logger.warning(
                    f"Failed to update memory for {step_type}: {e}. "
                    f"Continuing with node execution."
                )
            
            return result
        
        return wrapper
    return decorator


def _should_update_memory(self, state: AgentState) -> bool:
    """
    判断是否应该更新 Memory
    
    Args:
        self: 节点实例
        state: Agent 状态
    
    Returns:
        是否应该更新 Memory
    """
    # 检查是否有 MemoryManager
    memory_manager = getattr(self, 'memory_manager', None)
    if not memory_manager:
        return False
    
    # 检查是否有会话ID
    conversation_id = state.get("conversation_id")
    if not conversation_id:
        return False
    
    # 检查 Memory 功能是否启用
    if hasattr(memory_manager, 'enable_step_saving'):
        if not memory_manager.enable_step_saving:
            return False
    
    return True


def _extract_step_data(
    step_type: str,
    state: AgentState,
    result: Dict[str, Any],
    node_func: Callable
) -> Dict[str, Any]:
    """
    从状态和结果中提取步骤数据
    
    Args:
        step_type: 步骤类型
        state: Agent 状态
        result: 节点执行结果
        node_func: 节点函数
    
    Returns:
        步骤数据字典
    """
    step_data = {
        "step_type": step_type,
        "timestamp": datetime.now().isoformat(),
        "current_step": state.get("current_step", 0),
        "query": state.get("query", ""),
        "conversation_id": state.get("conversation_id"),
        "node_name": node_func.__name__,
    }
    
    # 根据步骤类型提取特定数据
    if step_type == "sql_generation":
        step_data.update(_extract_sql_generation_data(state, result))
    elif step_type == "sql_execution":
        step_data.update(_extract_sql_execution_data(state, result))
    elif step_type == "error_handling":
        step_data.update(_extract_error_handling_data(state, result))
    elif step_type == "intent_analysis":
        step_data.update(_extract_intent_analysis_data(state, result))
    elif step_type == "result_validation":
        step_data.update(_extract_result_validation_data(state, result))
    else:
        # 通用提取
        step_data.update(_extract_generic_data(state, result))
    
    return step_data


def _extract_sql_generation_data(state: AgentState, result: Dict[str, Any]) -> Dict[str, Any]:
    """提取 SQL 生成相关的数据"""
    return {
        "generated_sql": result.get("current_sql"),
        "enhanced_query": state.get("enhanced_query", state.get("query")),
        "intent_info": state.get("intent_info"),
        "fallback_strategy": state.get("fallback_strategy"),
        "validation_feedback": state.get("validation_feedback"),
        "sql_generation_success": result.get("current_sql") is not None,
    }


def _extract_sql_execution_data(state: AgentState, result: Dict[str, Any]) -> Dict[str, Any]:
    """提取 SQL 执行相关的数据"""
    execution_result = result.get("current_result", {})
    return {
        "executed_sql": state.get("current_sql"),
        "execution_status": execution_result.get("status"),
        "result_count": execution_result.get("count", 0),
        "execution_time_ms": result.get("execution_time_ms"),
        "error_occurred": bool(result.get("error")),
        "error_message": result.get("error"),
    }


def _extract_error_handling_data(state: AgentState, result: Dict[str, Any]) -> Dict[str, Any]:
    """提取错误处理相关的数据"""
    return {
        "error_type": result.get("error_type"),
        "error_message": result.get("error") or result.get("last_error"),
        "retry_count": result.get("retry_count", 0),
        "fallback_strategy": result.get("fallback_strategy"),
        "error_context": result.get("error_context"),
        "error_history": result.get("error_history", []),
        "recovery_suggestions": result.get("recovery_suggestions", []),
    }


def _extract_intent_analysis_data(state: AgentState, result: Dict[str, Any]) -> Dict[str, Any]:
    """提取意图分析相关的数据"""
    intent_info = state.get("intent_info", {})
    return {
        "detected_intent": intent_info.get("intent_type"),
        "is_spatial": intent_info.get("is_spatial"),
        "confidence": intent_info.get("confidence"),
        "keywords_matched": intent_info.get("keywords_matched", []),
        "requires_spatial": state.get("requires_spatial", False),
    }


def _extract_result_validation_data(state: AgentState, result: Dict[str, Any]) -> Dict[str, Any]:
    """提取结果验证相关的数据"""
    validation_history = result.get("validation_history", [])
    if validation_history:
        last_validation = validation_history[-1]
        return {
            "validation_passed": last_validation.get("is_valid"),
            "validation_message": last_validation.get("message"),
            "validation_confidence": last_validation.get("confidence"),
            "validation_issues": last_validation.get("issues", []),
            "validation_suggestions": last_validation.get("suggestions", []),
        }
    return {
        "validation_passed": result.get("validation_passed"),
        "validation_message": result.get("validation_reason"),
        "validation_guidance": result.get("validation_guidance"),
    }


def _extract_generic_data(state: AgentState, result: Dict[str, Any]) -> Dict[str, Any]:
    """提取通用数据"""
    return {
        "result_keys": list(result.keys()) if result else [],
        "state_keys": list(state.keys()),
        "has_error": bool(result.get("error")),
        "should_continue": result.get("should_continue", True),
        "thought_chain_length": len(result.get("thought_chain", [])),
    }


# 预定义的重要性级别映射
STEP_IMPORTANCE_LEVELS = {
    "sql_generation": 3,      # 高重要性 - 核心逻辑
    "sql_execution": 4,       # 最高重要性 - 数据获取
    "error_handling": 2,      # 中等重要性 - 错误恢复
    "intent_analysis": 2,     # 中等重要性 - 查询理解
    "result_validation": 2,   # 中等重要性 - 质量保证
    "check_results": 2,       # 中等重要性 - 迭代控制
    "generate_answer": 4,     # 最高重要性 - 最终结果
    "fetch_schema": 1,        # 低重要性 - 初始化
    "enhance_query": 1,       # 低重要性 - 预处理
}


def get_step_importance(step_type: str) -> int:
    """
    获取步骤类型的默认重要性级别
    
    Args:
        step_type: 步骤类型
    
    Returns:
        重要性级别 (1-4)
    """
    return STEP_IMPORTANCE_LEVELS.get(step_type, 1)


# 便捷装饰器，使用预定义的重要性级别
def with_memory_tracking(step_type: str):
    """
    便捷装饰器：使用预定义的重要性级别
    
    Args:
        step_type: 步骤类型
    
    Returns:
        装饰后的节点函数
    """
    importance = get_step_importance(step_type)
    return with_memory_update(step_type, importance)


# 测试代码
if __name__ == "__main__":
    import logging
    from datetime import datetime
    
    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== Memory Decorators 测试 ===\n")
    
    # 模拟测试类
    class MockMemoryManager:
        def __init__(self):
            self.enable_step_saving = True
            self.saved_steps = []
        
        def save_step(self, step_type: str, step_data: Dict[str, Any], 
                     importance: int, session_id: str) -> Optional[Dict[str, Any]]:
            step_record = {
                "step_type": step_type,
                "step_data": step_data,
                "importance": importance,
                "session_id": session_id,
                "saved_at": datetime.now().isoformat()
            }
            self.saved_steps.append(step_record)
            return step_record
    
    class MockNode:
        def __init__(self):
            self.memory_manager = MockMemoryManager()
        
        @with_memory_tracking("sql_generation")
        def generate_sql(self, state: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "current_sql": "SELECT * FROM test WHERE id = 1",
                "thought_chain": [{"step": 1, "type": "sql_generation"}]
            }
        
        @with_memory_tracking("sql_execution")
        def execute_sql(self, state: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "current_result": {"status": "success", "count": 5},
                "thought_chain": [{"step": 2, "type": "sql_execution"}]
            }
    
    # 测试装饰器
    node = MockNode()
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
    
    print("\n--- 查看保存的步骤 ---")
    for i, step in enumerate(node.memory_manager.saved_steps):
        print(f"步骤 {i+1}: {step['step_type']} (重要性: {step['importance']})")
        print(f"  会话ID: {step['session_id']}")
        print(f"  时间戳: {step['saved_at']}")
        print()
