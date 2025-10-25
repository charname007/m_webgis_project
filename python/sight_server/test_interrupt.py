#!/usr/bin/env python3
"""
测试LangGraph的interrupt功能
用于验证在用户查询不明确时，系统是否能正确中断并重新执行
"""

import json
import logging
from core.agent import SQLQueryAgent

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_interrupt_functionality():
    """测试interrupt功能的集成"""

    print("🧪 开始测试LangGraph Interrupt功能...")

    try:
        # 初始化Agent（不依赖外部服务）
        agent = SQLQueryAgent(
            enable_spatial=True,
            enable_memory=False,  # 简化测试
            enable_checkpoint=False,
            enable_cache=False
        )

        print("✅ SQLQueryAgent初始化成功")

        # 测试1: 明确的查询 - 应该直接执行
        clear_query = "查询浙江省的5A景区"
        print(f"\n📋 测试1 - 明确查询: '{clear_query}'")

        # 直接调用intent分析来验证
        from core.processors.intent_analyzer import IntentAnalyzer
        from core.llm import BaseLLM

        llm = BaseLLM(temperature=0.0)
        analyzer = IntentAnalyzer(llm)

        result = analyzer.analyze_intent(clear_query)
        print(f"Intent分析结果:")
        print(f"  - Query类型: {result['intent_type']}")
        print(f"  - 是否空间查询: {result['is_spatial']}")
        print(f"  - Confidence: {result['confidence']:.2f}")
        print(f"  - 查询是否明确: {result['is_query_clear']}")
        print(f"  - 推理: {result['reasoning'][:100]}...")

        # 测试2: 模糊的查询 - 应该触发interrupt
        unclear_query = "查询"  # 过于模糊
        print(f"\n📋 测试2 - 不明确查询: '{unclear_query}'")

        result2 = analyzer.analyze_intent(unclear_query)
        print(f"Intent分析结果:")
        print(f"  - Query类型: {result2['intent_type']}")
        print(f"  - 是否空间查询: {result2['is_spatial']}")
        print(f"  - Confidence: {result2['confidence']:.2f}")
        print(f"  - 查询是否明确: {result2['is_query_clear']}")
        print(f"  - 推理: {result2['reasoning'][:100]}...")

        # 验证interrupt检查函数
        from core.graph.edges import should_interrupt_after_intent
        from core.schemas import AgentState

        # 模拟AgentState
        mock_state_clear: AgentState = {
            "query": clear_query,
            "enhanced_query": "",
            "query_intent": result['intent_type'],
            "requires_spatial": result['is_spatial'],
            "intent_info": result,
            "database_schema": None,
            "schema_fetched": False,
            "sql_history": [],
            "execution_results": [],
            "thought_chain": [],
            "current_step": 0,
            "current_sql": None,
            "current_result": None,
            "should_continue": True,
            "max_iterations": 10,
            "error": None,
            "retry_count": 0,
            "max_retries": 3,
            "last_error": None,
            "error_history": [],
            "fallback_strategy": None,
            "error_type": None,
            "error_context": None,
            "query_id": "test-001",
            "query_start_time": "2025-10-04T00:00:00",
            "node_execution_logs": [],
            "session_history": [],
            "conversation_id": "test-session",
            "knowledge_base": None,
            "learned_patterns": [],
            "saved_checkpoint_id": None,
            "saved_checkpoint_step": None,
            "is_resumed_from_checkpoint": False,
            "last_checkpoint_time": None,
            "validation_history": [],
            "validation_retry_count": 0,
            "max_validation_retries": 3,
            "validation_feedback": None,
            "is_validation_enabled": True,
            "should_return_data": True,
            "analysis": None,
            "insights": None,
            "suggestions": None,
            "analysis_type": None,
            "final_data": None,
            "answer": "",
            "status": "pending",
            "message": ""
        }

        mock_state_unclear = mock_state_clear.copy()
        mock_state_unclear["query"] = unclear_query
        mock_state_unclear["intent_info"] = result2

        # 测试条件边函数
        edge_result_clear = should_interrupt_after_intent(mock_state_clear)
        edge_result_unclear = should_interrupt_after_intent(mock_state_unclear)

        print(f"\n🔍 条件边测试:")
        print(f"  - 明确查询结果: {edge_result_clear}")
        print(f"  - 不明确查询结果: {edge_result_unclear}")

        # 验证结果
        test_passed = (
            edge_result_clear == "enhance_query" and
            edge_result_unclear == "interrupt_check"
        )

        if test_passed:
            print("\n✅ Interrupt功能测试通过！")
            print("  - 明确查询会正常执行")
            print("  - 不明确查询会触发interrupt检查")
        else:
            print("\n❌ Interrupt功能测试失败！")

        print(f"\n📝 测试结果总结:")
        print(f"  查询明确性判断: {'✅ 正常' if result['is_query_clear'] else '❌ 异常'}")
        print(f"  条件边路由: {'✅ 正确' if test_passed else '❌ 错误'}")

        return test_passed

    except Exception as e:
        logger.error(f"测试过程中出错: {e}", exc_info=True)
        return False
    finally:
        if 'agent' in locals():
            agent.close()


if __name__ == "__main__":
    print("=" * 50)
    print("🏁 LangGraph Interrupt功能集成测试")
    print("=" * 50)

    success = test_interrupt_functionality()

    print("\n" + "=" * 50)
    if success:
        print("🎉 所有测试通过！Interrupt功能已正确集成到LangGraph工作流中")
    else:
        print("⚠️  部分测试失败，请检查日志")
    print("=" * 50)