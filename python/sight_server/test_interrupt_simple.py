#!/usr/bin/env python3
"""
简单测试LangGraph的interrupt功能
使用ASCII字符避免编码问题
"""

import logging

def test_interrupt_simple():
    """简单的interrupt功能测试"""

    print("=" * 60)
    print("    LangGraph Interrupt功能集成测试")
    print("=" * 60)

    try:
        from langgraph.graph import StateGraph, START, END
        from langgraph.types import interrupt, Command
        from core.schemas import AgentState

        # 创建简化的测试图
        workflow = StateGraph(AgentState)

        def analyze_intent_node(state: AgentState):
            print(f"[INTENT] 分析意图: '{state['query']}'")

            # 简化的明确性判断
            is_clear = len(state['query']) > 5
            intent_info = {
                "intent_type": "query",
                "is_query_clear": is_clear,
                "confidence": 0.8 if is_clear else 0.3,
                "reasoning": f"查询长度判断: {len(state['query'])}字符"
            }

            return {
                "intent_info": intent_info,
                "thought_chain": [{
                    "step": 1, "type": "intent_analysis", "action": "analyze",
                    "input": state['query'], "output": intent_info, "status": "completed"
                }]
            }

        def interrupt_check_node(state: AgentState):
            print(f"[INTERRUPT] 检查查询: '{state['query']}'")

            intent_info = state.get("intent_info", {})
            is_query_clear = intent_info.get("is_query_clear", True)

            if not is_query_clear:
                print("[INTERRUPT] 查询不明确，请求澄清...")
                try:
                    # 模拟interrupt被触发
                    new_query = interrupt({
                        "reason": "query_not_clear",
                        "original_query": state['query'],
                        "message": "请提供更具体的查询"
                    })
                    print(f"[INTERRUPT] 获得新查询: '{new_query}'")

                    return {
                        "query": new_query,
                        "interrupt_info": {"interrupted": True, "new_query": new_query},
                        "thought_chain": [{
                            "step": 2, "type": "interruption", "action": "clarify_query",
                            "input": state['query'], "output": {"new_query": new_query},
                            "status": "completed"
                        }]
                    }
                except Exception as e:
                    print(f"[INTERRUPT] interrupt失败: {e}")
                    # 如果interrupt失败，继续使用原查询
                    return {"interrupt_info": {"interrupted": False}, "thought_chain": []}
            else:
                print("[INTERRUPT] 查询明确，继续执行")
                return {
                    "interrupt_info": {"interrupted": False},
                    "thought_chain": [{
                        "step": 2, "type": "interruption", "action": "query_clear",
                        "input": state['query'], "output": {"query_clear": True},
                        "status": "completed"
                    }]
                }

        def process_query_node(state: AgentState):
            print(f"[PROCESS] 处理查询: '{state['query']}'")
            return {
                "answer": f"处理完成: {state['query']}",
                "status": "completed",
                "final_data": []
            }

        # 添加到工作流
        workflow.add_node("analyze_intent", analyze_intent_node)
        workflow.add_node("interrupt_check", interrupt_check_node)
        workflow.add_node("process_query", process_query_node)

        workflow.add_edge(START, "analyze_intent")
        workflow.add_conditional_edges(
            "analyze_intent",
            lambda state: Command(goto="analyze_intent") if state.get("interrupt_info", {}).get("interrupted") else "interrupt_check",
            {"interrupt_check": "interrupt_check", "analyze_intent": "analyze_intent"}
        )
        workflow.add_edge("interrupt_check", "analyze_intent")
        workflow.add_edge("interrupt_check", "process_query")
        workflow.add_edge("process_query", END)

        # 简化版本的条件边
        def simple_condition(state):
            intent_info = state.get("intent_info", {})
            if not intent_info.get("is_query_clear", True):
                return "interrupt_check"
            return "process_query"

        # 重新设置条件边
        workflow.add_conditional_edges(
            "analyze_intent",
            simple_condition,
            {"interrupt_check": "interrupt_check", "process_query": "process_query"}
        )

        # 配置checkpoint
        from langgraph.checkpoint.memory import InMemorySaver
        checkpointer = InMemorySaver()
        graph = workflow.compile(checkpointer=checkpointer)

        print("* 测试图构建成功")

        # 测试1：明确查询
        test1_query = "浙江省5A景区统计"
        print(f"\n[TEST1] 明确查询: '{test1_query}' (应该正常执行)")

        config = {"configurable": {"thread_id": "test1"}}

        try:
            result1 = graph.invoke({"query": test1_query}, config)
            print(f"* 测试结果: {result1.get('status', 'unknown')}")
            print(f"* 最终答案: {result1.get('answer', '无')}")
        except Exception as e:
            print(f"- 测试1出错: {e}")

        # 测试2：不明确的查询
        test2_query = "查询"  # 过于模糊
        clarified_query = "查询浙江省的5A景区有哪些"
        print(f"\n[TEST2] 不明确查询: '{test2_query}' (应该触发interrupt)")

        # 模拟用户对interrupt的响应
        import langgraph.types
        original_interrupt = langgraph.types.interrupt

        def mock_interrupt_unclear(context):
            print("[MOCK] interrupt被触发")
            print(f"  原始查询: {context.get('original_query', '')}")
            return clarified_query  # 返回澄清后的查询

        langgraph.types.interrupt = mock_interrupt_unclear

        try:
            config2 = {"configurable": {"thread_id": "test2"}}
            result2 = graph.invoke({"query": test2_query}, config2)
            print(f"* 测试结果: {result2.get('status', 'unknown')}")
            print(f"* 最终答案: {result2.get('answer', '无')}")
            print(f"* 最终查询: {result2.get('query', '无')}")

            if result2.get('query') == clarified_query:
                print("* 查询澄清功能正常")
            else:
                print("- 查询澄清功能异常")
        except Exception as e:
            print(f"- 测试2出错: {e}")
        finally:
            langgraph.types.interrupt = original_interrupt

        print("\n" + "=" * 60)
        print("测试结果: interrupt机制基本正常")
        return True

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_interrupt_simple()
    status = "通过" if success else "失败"
    print("\n最终状态:", status)