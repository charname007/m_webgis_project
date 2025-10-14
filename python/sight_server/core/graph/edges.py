"""
LangGraph边条件模块 - Sight Server
定义工作流的条件边函数
"""

import logging
from typing import Literal

from ..schemas import AgentState

logger = logging.getLogger(__name__)


def should_retry_or_fail(
    state: AgentState
) -> Literal["handle_error", "check_results"]:
    """
    条件边: 判断SQL执行后是否应该重试还是继续

    决策逻辑:
    1. 如果没有错误 → 继续到规则检查节点
    2. 如果有错误且可以重试 → 进入错误处理节点
    3. 如果错误不可恢复 → 继续（在check_results中会停止）
    4. 如果SQL执行重试耗尽 → 继续到规则检查节点（避免无限循环）

    Args:
        state: Agent状态

    Returns:
        下一个节点名称: "handle_error" 或 "check_results"
    """
    error = state.get("error")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 5)
    
    # 检查SQL执行重试是否已耗尽
    sql_execution_retries = state.get("sql_execution_retries", 0)
    max_sql_execution_retries = state.get("max_sql_execution_retries", 3)

    # 没有错误，正常继续到规则检查节点
    if not error:
        logger.info("[Edge: should_retry_or_fail] No error, proceeding to check_results")
        return "check_results"

    # 有错误但SQL执行重试已耗尽
    if sql_execution_retries >= max_sql_execution_retries:
        logger.warning(
            f"[Edge: should_retry_or_fail] SQL execution retries exhausted "
            f"({sql_execution_retries}/{max_sql_execution_retries}), proceeding to check_results"
        )
        return "check_results"

    # 有错误但已达重试上限
    if retry_count >= max_retries:
        logger.warning(
            f"[Edge: should_retry_or_fail] Max retries reached "
            f"({retry_count}/{max_retries}), proceeding to check_results with error"
        )
        return "check_results"

    # 有错误且可以重试
    logger.info(
        f"[Edge: should_retry_or_fail] Error detected (retry {retry_count}/{max_retries}, "
        f"sql_retry {sql_execution_retries}/{max_sql_execution_retries}), going to handle_error"
    )
    return "handle_error"


def should_continue_querying(
    state: AgentState
) -> Literal["generate_sql", "generate_answer"]:
    """
    条件边: 判断是否继续查询

    决策逻辑:
    1. 如果有错误 → 生成答案（结束）
    2. 如果达到最大迭代次数 → 生成答案（结束）
    3. 如果 should_continue=False → 生成答案（结束）
    4. 否则 → 继续生成SQL（循环）

    Args:
        state: Agent状态

    Returns:
        下一个节点名称: "generate_sql" 或 "generate_answer"
    """
    # 检查错误
    if state.get("error"):
        logger.info("[Edge: should_continue_querying] Error detected, going to generate_answer")
        return "generate_answer"

    # 检查迭代次数
    current_step = state.get("current_step", 0)
    max_iterations = state.get("max_iterations", 10)

    if current_step >= max_iterations:
        logger.info(
            f"[Edge: should_continue_querying] Max iterations reached "
            f"({current_step}/{max_iterations}), going to generate_answer"
        )
        return "generate_answer"

    # 检查 should_continue 标志
    should_continue = state.get("should_continue", False)

    if not should_continue:
        logger.info("[Edge: should_continue_querying] should_continue=False, going to generate_answer")
        return "generate_answer"

    # 继续查询
    logger.info(
        f"[Edge: should_continue_querying] Continuing query "
        f"(step {current_step}/{max_iterations})"
    )
    return "generate_sql"


def should_requery(
    state: AgentState
) -> Literal["generate_sql", "validate_results"]:
    """
    条件边: 根据规则检查结果决定是否重新查询

    决策逻辑:
    1. 检查 should_continue 标志
    2. 如果 should_continue=True → 返回 generate_sql 重新查询
    3. 如果 should_continue=False → 继续到 validate_results 进行质量验证

    Args:
        state: Agent状态

    Returns:
        下一个节点名称: "generate_sql" 或 "validate_results"
    """
    # 检查是否需要继续查询
    should_continue = state.get("should_continue", False)

    if should_continue:
        logger.info("[Edge: should_requery] Rule-based check suggests requerying, going to generate_sql")
        return "generate_sql"

    # 不需要继续查询，进行结果质量验证
    logger.info("[Edge: should_requery] Rule-based check passed, proceeding to validate_results")
    return "validate_results"


def should_summarize_conversation(state: AgentState) -> Literal["summarize_conversation", "continue"]:
    """
    条件边: 判断是否需要总结对话
    
    触发条件：
    - session_history 超过阈值（例如5条）
    - 距离上次总结有一定步数间隔
    - 在查询开始时触发，为当前查询提供上下文
    
    Args:
        state: Agent状态
        
    Returns:
        下一个节点名称: "summarize_conversation" 或 "continue"
    """
    session_history = state.get("session_history", [])
    history_length = len(session_history)
    last_summary_step = state.get("last_summary_step", 0)
    current_step = state.get("current_step", 0)
    
    # 计算距离上次总结的步数
    steps_since_summary = current_step - last_summary_step
    
    # 触发条件 - 降低阈值，在查询开始时触发
    summary_threshold = state.get("summary_trigger_count", 5)  # 从30降低到5
    summary_interval = state.get("summary_interval", 3)       # 从10降低到3
    
    # 检查是否需要总结
    if history_length > summary_threshold and steps_since_summary > summary_interval:
        logger.info(
            f"[Edge: should_summarize_conversation] Triggering summary at query start: "
            f"history={history_length}, steps_since_summary={steps_since_summary}"
        )
        return "summarize_conversation"
    
    logger.debug(
        f"[Edge: should_summarize_conversation] No summary needed at query start: "
        f"history={history_length}, steps_since_summary={steps_since_summary}"
    )
    return "continue"


# 其他可能的条件边函数（未来扩展）

def should_use_spatial_query(state: AgentState) -> Literal["spatial_node", "regular_node"]:
    """
    条件边: 判断是否使用空间查询节点

    （示例，暂未使用）

    Args:
        state: Agent状态

    Returns:
        下一个节点名称
    """
    if state.get("requires_spatial", False):
        return "spatial_node"
    else:
        return "regular_node"


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== 条件边测试 ===\n")

    # 测试1: 正常继续
    print("--- 测试1: 正常继续 ---")
    state1: AgentState = {
        "query": "测试",
        "enhanced_query": "测试",
        "query_intent": "query",
        "requires_spatial": False,
        "sql_history": [],
        "execution_results": [],
        "thought_chain": [],
        "current_step": 1,
        "current_sql": None,
        "current_result": None,
        "should_continue": True,
        "max_iterations": 3,
        "error": None,
        "session_history": [],
        "conversation_id": None,
        "knowledge_base": None,
        "learned_patterns": [],
        "saved_checkpoint_id": None,
        "saved_checkpoint_step": None,
        "is_resumed_from_checkpoint": False,
        "last_checkpoint_time": None,
        "final_data": None,
        "answer": "",
        "status": "pending",
        "message": ""
    }
    result1 = should_continue_querying(state1)
    print(f"Result: {result1}\n")

    # 测试2: 达到最大迭代次数
    print("--- 测试2: 达到最大迭代次数 ---")
    state2 = state1.copy()
    state2["current_step"] = 3
    result2 = should_continue_querying(state2)
    print(f"Result: {result2}\n")

    # 测试3: 有错误
    print("--- 测试3: 有错误 ---")
    state3 = state1.copy()
    state3["error"] = "测试错误"
    result3 = should_continue_querying(state3)
    print(f"Result: {result3}\n")

    # 测试4: should_continue=False
    print("--- 测试4: should_continue=False ---")
    state4 = state1.copy()
    state4["should_continue"] = False
    result4 = should_continue_querying(state4)
    print(f"Result: {result4}\n")
