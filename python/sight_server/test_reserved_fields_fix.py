"""
Test LangGraph Reserved Fields Fix

Verify that AgentState does not contain LangGraph reserved fields
"""

import sys
import traceback

def test_imports():
    """Test imports"""
    try:
        print("Test 1: Import modules...")
        from core.schemas import AgentState
        from langgraph.graph import StateGraph
        print("[PASS] Modules imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        traceback.print_exc()
        return False

def test_reserved_fields():
    """Test reserved fields"""
    try:
        print("\nTest 2: Check reserved fields...")
        from core.schemas import AgentState

        # LangGraph reserved fields
        reserved_fields = ['checkpoint_id', 'checkpoint_ns', 'checkpoint']

        # AgentState fields
        state_fields = list(AgentState.__annotations__.keys())

        # Check conflicts
        conflicts = [f for f in state_fields if f in reserved_fields]

        if conflicts:
            print(f"[FAIL] Reserved field conflicts found: {conflicts}")
            return False
        else:
            print("[PASS] No reserved field conflicts")
            print("  Checkpoint fields used: saved_checkpoint_id, saved_checkpoint_step, is_resumed_from_checkpoint")
            return True

    except Exception as e:
        print(f"[FAIL] Check failed: {e}")
        traceback.print_exc()
        return False

def test_graph_building():
    """Test graph building (without DB connection)"""
    try:
        print("\nTest 3: Test graph building...")
        from core.schemas import AgentState
        from langgraph.graph import StateGraph, END

        # Create simple test graph
        workflow = StateGraph(AgentState)

        # Add test node
        def test_node(state):
            return {"answer": "test"}

        workflow.add_node("test", test_node)
        workflow.set_entry_point("test")
        workflow.add_edge("test", END)

        # Compile graph (this will check reserved fields)
        graph = workflow.compile()

        print("[PASS] Graph built successfully, no reserved field conflicts")
        return True

    except ValueError as e:
        if "reserved" in str(e):
            print(f"[FAIL] Reserved field error: {e}")
            return False
        raise
    except Exception as e:
        print(f"[FAIL] Graph build failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("LangGraph Reserved Fields Fix Verification")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Import modules", test_imports()))
    results.append(("Check reserved fields", test_reserved_fields()))
    results.append(("Graph building", test_graph_building()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{name}: {status}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS! All tests passed! Fix is working correctly!")
        print("=" * 60)
        return 0
    else:
        print("FAILURE! Some tests failed, please check error messages")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
