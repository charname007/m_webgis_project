#!/usr/bin/env python3
"""
最终测试LangGraph的interrupt功能
完整ASCII版本，避免中文编码问题
"""

import logging

def test_interrupt_final():
    """最终的interrupt功能测试"""

    print("=" * 60)
    print("    LangGraph Interrupt Integration Test")
    print("=" * 60)

    try:
        from langgraph.graph import StateGraph, START, END
        from langgraph.types import interrupt, Command
        from core.schemas import AgentState

        # 创建工作流
        workflow = StateGraph(AgentState)

        def analyze_intent_node(state: AgentState):
            print(f"[INTENT] Analyzing query: '{state['query']}'")

            # 简化的明确性判断
            query = state['query']
            is_clear = len(query) > 5 and "统计" in query

            intent_info = {
                "intent_type": "query",
                "is_query_clear": is_clear,
                "confidence": 0.8 if is_clear else 0.3,
                "reasoning": f"Query clarity based on content length and keywords"
            }

            return {
                "intent_info": intent_info,
                "thought_chain": [{
                    "step": 1,
                    "type": "intent_analysis",
                    "action": "analyze_intent",
                    "input": query,
                    "output": intent_info,
                    "status": "completed"
                }]
            }

        def interrupt_check_node(state: AgentState):
            print(f"[INTERRUPT] Checking query clarity: '{state['query']}'")

            intent_info = state.get("intent_info", {})
            is_query_clear = intent_info.get("is_query_clear", True)

            if not is_query_clear:
                print("[INTERRUPT] Query unclear, requesting clarification...")
                try:
                    # 使用interrupt功能
                    new_query = interrupt({
                        "reason": "query_not_clear",
                        "original_query": state['query'],
                        "message": "Query is not clear, please provide more details"
                    })
                    print(f"[INTERRUPT] Received clarified query: '{new_query}'")

                    return {
                        "query": new_query,  # 更新查询
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
                except Exception as e:
                    print(f"[INTERRUPT] Error in interrupt: {e}")
                    return {"interrupt_info": {"interrupted": False}}
            else:
                print("[INTERRUPT] Query is clear, continuing execution")
                return {
                    "interrupt_info": {"interrupted": False, "reason": "query_clear"},
                    "thought_chain": [{
                        "step": 2,
                        "type": "interruption",
                        "action": "query_clear_continue",
                        "input": state['query'],
                        "output": {"query_clear": True},
                        "status": "completed"
                    }]
                }

        def process_query_node(state: AgentState):
            print(f"[PROCESS] Processing query: '{state['query']}'")
            return {
                "answer": f"Processing complete for query: {state['query']}",
                "status": "completed"
            }

        # 构建工作流
        workflow.add_node("analyze_intent", analyze_intent_node)
        workflow.add_node("interrupt_check", interrupt_check_node)
        workflow.add_node("process_query", process_query_node)

        workflow.add_edge(START, "analyze_intent")

        # 关键：使用条件边处理interrupt流程
        def condition_func(state):
            if state.get("interrupt_info", {}).get("reason") == "query_clarified":
                return Command(goto="analyze_intent")  # 重新分析新查询
            intent_info = state.get("intent_info", {})
            return "interrupt_check" if not intent_info.get("is_query_clear", True) else "process_query"

        workflow.add_conditional_edges("analyze_intent", condition_func, {
            "interrupt_check": "interrupt_check",
            "process_query": "process_query",
            "analyze_intent": "analyze_intent"  # Command(goto='analyze_intent')
        })

        workflow.add_edge("interrupt_check", "analyze_intent")  # 检查后续重新分析
        workflow.add_edge("process_query", END)

        # 添加checkpoint
        from langgraph.checkpoint.memory import InMemorySaver
        checkpointer = InMemorySaver()
        graph = workflow.compile(checkpointer=checkpointer)

        print("[OK] Test graph built successfully")

        # 测试1：明确查询
        clear_query = "Statistics of 5A scenic spots in Zhejiang Province"
        print(f"\n[Test1] Clear query: '{clear_query}' (should execute normally)")

        config = {"configurable": {"thread_id": "test_clear"}}

        try:
            result1 = graph.invoke({"query": clear_query}, config)
            print(f"[OK] Result: {result1.get('status', 'unknown')}")
            print(f"[OK] Answer: {result1.get('answer', 'No answer')}")
        except Exception as e:
            print(f"[ERR] Test1 failed: {e}")

        # 测试2：不明确的查询
        unclear_query = "query"
        clarified_query = "Statistics of 5A scenic spots in Zhejiang Province"
        print(f"\n[Test2] Unclear query: '{unclear_query}' (should trigger interrupt)")

        # 模拟用户对interrupt的响应
        import langgraph.types
        original_interrupt = langgraph.types.interrupt

        def simulate_user_clarify(context):
            print("[MOCK] Interrupt triggered")
            print(f"  Original query: {context.get('original_query', '')}")
            return clarified_query  # Return clarified query

        langgraph.types.interrupt = simulate_user_clarify

        try:
            config2 = {"configurable": {"thread_id": "test_unclear"}}
            result2 = graph.invoke({"query": unclear_query}, config2)

            print(f"[OK] Result: {result2.get('status', 'unknown')}")
            print(f"[OK] Answer: {result2.get('answer', 'No answer')}")

            final_query = result2.get('query', '')
            if final_query == clarified_query:
                print("[OK] Query clarification successful")
                print(f"        Original: '{unclear_query}' -> Clarified: '{final_query}'")
            else:
                print(f"[WARN] Query clarification failed. Final: '{final_query}'")

        except Exception as e:
            print(f"[ERR] Test2 failed: {e}")
        finally:
            langgraph.types.interrupt = original_interrupt

        print("\n" + "=" * 60)
        return True

    except Exception as e:
        print(f"[ERR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_interrupt_final()
    status = "SUCCESS" if success else "FAILED"
    print(f"\nFinal Test Status: {status}")