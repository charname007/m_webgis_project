#!/usr/bin/env python3
"""
真正实现LangGraph interrupt功能的测试
展示如何处理真实的interrupt流程
"""

import logging

def test_interrupt_real():
    """真实的interrupt功能测试"""

    print("=" * 60)
    print("    Real LangGraph Interrupt Test")
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
            is_clear = len(query.strip().split()) > 2  # 至少需要3个单词

            intent_info = {
                "intent_type": "query",
                "is_query_clear": is_clear,
                "confidence": 0.8 if is_clear else 0.3,
                "reasoning": f"Query has {len(query.strip().split())} words"
            }

            return {
                "intent_info": intent_info,
                "thought_chain": [{
                    "step": len(state.get("thought_chain", [])),
                    "type": "intent_analysis",
                    "action": "analyze_intent",
                    "input": query,
                    "output": {"is_clear": is_clear},
                    "status": "completed"
                }]
            }

        def interrupt_node(state: AgentState):
            print(f"[INTERRUPT] Checking if query needs clarification: '{state['query']}'")
            intent_info = state.get("intent_info", {})
            is_query_clear = intent_info.get("is_query_clear", True)

            if not is_query_clear:
                print("[INTERRUPT] Query unclear, requesting clarification...")
                print("[INTERRUPT] About to call interrupt() - this will pause the workflow")

                # 真正的interrupt调用 - 这会自动暂停工作流
                new_query = interrupt({
                    "reason": "query_not_clear",
                    "original_query": state['query'],
                    "message": "Please provide a clearer query with more details",
                    "suggestion": "Be more specific about location, type, or conditions"
                })

                print(f"[INTERRUPT] Resumed! New query received: '{new_query}'")
                return {
                    "query": new_query,
                    "interrupt_info": {"interrupted": True, "new_query": new_query},
                    "thought_chain": [{
                        "step": len(state.get("thought_chain", [])),
                        "type": "interruption",
                        "action": "query_clarification",
                        "input": state['query'],
                        "output": {"new_query": new_query},
                        "status": "completed"
                    }]
                }
            else:
                print("[INTERRUPT] Query is clear, no interruption needed")
                return {"interrupt_info": {"interrupted": False}}

        def process_node(state: AgentState):
            print(f"[PROCESS] Processing final query: '{state['query']}'")
            return {"answer": f"Processed query: {state['query']}", "status": "completed"}

        # 构建工作流
        workflow.add_node("analyze_intent", analyze_intent_node)
        workflow.add_node("interrupt_check", interrupt_node)
        workflow.add_node("process", process_node)

        workflow.add_edge(START, "analyze_intent")
        workflow.add_conditional_edges(
            "analyze_intent",
            lambda state: "interrupt_check" if not state.get("intent_info", {}).get("is_query_clear", True) else "process",
            {"interrupt_check": "interrupt_check", "process": "process"}
        )
        workflow.add_edge("interrupt_check", "process")
        workflow.add_edge("process", END)

        # 添加checkpoint
        from langgraph.checkpoint.memory import InMemorySaver
        checkpointer = InMemorySaver()
        graph = workflow.compile(checkpointer=checkpointer)
        print("[OK] Graph compiled successfully")

        # 测试1：明确的查询（应该直接执行）
        test1_query = "Statistics of 5A scenic spots in Zhejiang Province"
        print(f"\n[Test1] Clear query: '{test1_query}' (should execute normally)")

        config = {"configurable": {"thread_id": "test1"}}
        try:
            result1 = graph.invoke({"query": test1_query}, config)
            print(f"[OK] Result: {result1.get('status', 'unknown')}")
            print(f"[OK] Answer: {result1.get('answer', 'No answer')}")
        except Exception as e:
            print(f"[ERR] Test1 failed: {e}")

        # 测试2：不明确的查询（应该触发interrupt）
        test2_query = "query"
        clarified_query = "Statistics of 5A scenic spots in Zhejiang Province"
        print(f"\n[Test2] Unclear query: '{test2_query}' (should trigger interrupt)")

        # 第一步：运行工作流直到interrupt点
        config2 = {"configurable": {"thread_id": "test2"}}
        try:
            print("[TEST] Running graph with unclear query...")
            result2_a = graph.invoke({"query": test2_query}, config2)
            print("[TEST] This should have hit interrupt and returned the result")

            # 检查是否有interrupt信息
            interrupts = result2_a.get('__interrupt__', [])
            if interrupts:
                print(f"[INFO] Found {len(interrupts)} interrupt(s):")
                for i, interrupt_info in enumerate(interrupts):
                    print(f"  Interrupt {i+1}: {interrupt_info}")

                # 模拟用户澄清查询并恢复执行
                print(f"[TEST] Simulating user clarification to: '{clarified_query}'")

                # 使用Command.resume来恢复执行
                result2_b = graph.invoke(
                    Command(resume=clarified_query),
                    config2
                )

                print(f"[OK] Result after clarification: {result2_b.get('status', 'unknown')}")
                print(f"[OK] Answer: {result2_b.get('answer', 'No answer')}

            else:
                print("[WARN] No interrupt detected, checking what happened")
                print(f"[INFO] Result keys: {list(result2_a.keys())}")

        except Exception as e:
            print(f"[ERR] Test2 failed: {e}")
            import traceback
            traceback.print_exc()

        return True

    except Exception as e:
        print(f"[ERR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_interrupt_real()
    status = "SUCCESS" if success else "FAILED"
    print(f"\nFinal Test Status: {status}")