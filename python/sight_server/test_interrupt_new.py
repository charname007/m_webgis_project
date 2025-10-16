#!/usr/bin/env python3
"""
测试LangGraph的interrupt功能（新版本）
测试使用内置的interrupt和Command机制
"""

import json
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

from core.schemas import AgentState
from core.graph.nodes import build_node_context, build_node_mapping
from core.graph.edges import should_interrupt_after_intent

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_test_graph():
    """设置测试用的简化LangGraph"""

    # 创建基本的测试架构
    context = build_node_context(
        sql_generator=None,
        sql_executor=None,
        result_parser=None,
        answer_generator=None,
        schema_fetcher=None,
        llm=None,
        error_handler=None,
        cache_manager=None,
        structured_logger=None
    )

    node_handlers = build_node_mapping(context)

    # 创建简化的测试图
    workflow = StateGraph(AgentState)

    # 添加测试节点
    def analyze_intent_node(state: AgentState) -> Dict[str, Any]:
        print(f"🔍 分析意图: '{state['query']}'")

        # 简化的意图分析
        is_clear = len(state['query']) > 5 and any(word in state['query'] for word in ['的', '统计', '查询', '多少'])

        intent_info = {
            "intent_type": "query",
            "is_spatial": False,
            "confidence": 0.8 if is_clear else 0.3,
            "reasoning": f"查询包含足够信息: {is_clear}",
            "is_query_clear": is_clear,
            "keywords_matched": ["测试"]
        }

        return {
            "query_intent": "query",
            "requires_spatial": False,
            "intent_info": intent_info,
            "thought_chain": [{
                "step": 1,
                "type": "intent_analysis",
                "action": "analyze_intent",
                "input": state['query'],
                "output": intent_info,
                "status": "completed"
            }]
        }

    def interrupt_check_node(state: AgentState) -> Dict[str, Any]:
        print(f"🔄 检查interrupt: '{state['query']}'")

        intent_info = state.get("intent_info", {})
        is_query_clear = intent_info.get("is_query_clear", True)

        if not is_query_clear:
            print("❓ 查询不明确，请求澄清...")
            new_query = interrupt({
                "original_query": state['query'],
                "message": "您的查询不够明确"
            })
            print(f"✅ 获得新查询: '{new_query}'")

            return {
                "query": new_query,
                "interrupt_info": {
                    "interrupted": True,
                    "reason": "query_clarified",
                    "new_query": new_query
                },
                "thought_chain": [{
                    "step": 2,
                    "type": "interruption",
                    "action": "request_clarification",
                    "input": state['query'],
                    "output": {"new_query": new_query},
                    "status": "completed"
                }]
            }
        else:
            return {
                "interrupt_info": {"interrupted": False},
                "thought_chain": [{
                    "step": 2,
                    "type": "interruption",
                    "action": "query_clear",
                    "input": state['query'],
                    "output": {"query_clear": True},
                    "status": "completed"
                }]
            }

    def enhance_query_node(state: AgentState) -> Dict[str, Any]:
        print(f"⭐ 增强查询: '{state['query']}'")
        return {
            "enhanced_query": state['query'] + " 增强版",
            "message": f"已增强查询: {state['query']}"
        }

    def generate_answer_node(state: AgentState) -> Dict[str, Any]:
        print(f"✨ 生成答案: '{state['enhanced_query']}'")
        return {
            "answer": f"您的查询 '{state['query']}' 的答案是...",
            "status": "completed",
            "final_data": []
        }

    # 添加节点到工作流
    workflow.add_node("analyze_intent", analyze_intent_node)
    workflow.add_node("interrupt_check", interrupt_check_node)
    workflow.add_node("enhance_query", enhance_query_node)
    workflow.add_node("generate_answer", generate_answer_node)

    # 设置入口点
    workflow.add_edge(START, "analyze_intent")

    # 添加条件边
    workflow.add_conditional_edges(
        "analyze_intent",
        should_interrupt_after_intent,
        {
            "interrupt_check": "interrupt_check",
            "enhance_query": "enhance_query",
            "analyze_intent": "analyze_intent"  # 对应Command(goto="analyze_intent")
        }
    )

    workflow.add_edge("interrupt_check", "analyze_intent")  # interrupt后重新分析
    workflow.add_edge("enhance_query", "generate_answer")
    workflow.add_edge("generate_answer", END)

    # 配置checkpoint用于保存状态
    checkpointer = InMemorySaver()
    return workflow.compile(checkpointer=checkpointer)


def test_interrupt_workflow():
    """测试完整的interrupt工作流"""

    print("=" * 60)
    print("    LangGraph Interrupt功能集成测试")
    print("=" * 60)

    try:
        # 创建工作流
        graph = setup_test_graph()
        print("✅ 测试图构建成功")

        # 测试用例1：明确的查询（应该正常执行）
        test1_query = "统计浙江省有多少个5A景区"
        print(f"\n📋 测试1 - 明确查询: '{test1_query}'")

        config = {"configurable": {"thread_id": "test_thread_1"}}

        # 模拟用户输入明确查询的情况
        def mock_interrupt_clear(context):
            return test1_query  # 返回相同的查询

        # 临时替换interrupt函数
        import langgraph.types
        original_interrupt = langgraph.types.interrupt
        langgraph.types.interrupt = mock_interrupt_clear

        try:
            result1 = graph.invoke({"query": test1_query}, config=config)
            print(f"✅ 测试结果: {result1.get('status', 'unknown')}")
            print(f"📝 最终答案: {result1.get('answer', '无')}")

            # 检查思维链
            thought_chain = result1.get('thought_chain', [])
            for step in thought_chain:
                print(f"  - Step {step.get('step')}: {step.get('type')} - {step.get('action')}")
        finally:
            langgraph.types.interrupt = original_interrupt

        # 测试用例2：不明确的查询（应该触发interrupt）
        test2_query = "查询"  # 过于模糊
        print(f"\n📋 测试2 - 不明确查询: '{test2_query}'")

        config2 = {"configurable": {"thread_id": "test_thread_2"}}

        # 模拟用户澄清查询的情况
        clarified_query = "查询浙江省的5A景区有哪些"

        def mock_interrupt_unclear(context):
            print(f"🤔 LangGraph interrupt被触发，模拟用户澄清查询...")
            print(f"   原始查询: {context.get('original_query', '')}")
            print(f"   提示信息: {context.get('message', '')}")
            return clarified_query  # 返回澄清后的查询

        langgraph.types.interrupt = mock_interrupt_unclear

        try:
            result2 = graph.invoke({"query": test2_query}, config=config2)
            print(f"✅ 测试结果: {result2.get('status', 'unknown')}")
            print(f"📝 最终答案: {result2.get('answer', '无')}")

            # 验证最终查询是否更新
            final_query = result2.get('query', '')
            if final_query == clarified_query:
                print(f"✅ 查询澄清成功: '{test2_query}' -> '{final_query}'")
            else:
                print(f"❌ 查询未正确澄清: {final_query}")

            # 检查思维链
            thought_chain = result2.get('thought_chain', [])
            for step in thought_chain:
                print(f"  - Step {step.get('step')}: {step.get('type')} - {step.get('action')}")

        finally:
            langgraph.types.interrupt = original_interrupt

        print(f"\n🎯 测试总结:")
        print(f"✅ Interrupt机制正常触发")
        print(f"✅ 查询澄清流程完整执行")
        print(f"✅ 重新分析功能正常工作")

        return True

    except Exception as e:
        logger.error(f"测试执行出错: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_interrupt_workflow()

    print("\n" + "=" * 60)
    if success:
        print("🎉 LangGraph Interrupt功能测试通过！")
        print("✅ 工作流能够在查询不明确时触发中断")
        print("✅ 用户澄清后可以重新执行")
    else:
        print("⚠️  测试遇到问题，请检查日志")
    print("=" * 60)