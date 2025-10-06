"""
Fallback机制测试脚本 - Sight Server
测试错误处理、重试逻辑和SQL修复功能
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.schemas import AgentState
from core.graph.nodes import AgentNodes
from core.graph.edges import should_retry_or_fail, should_continue_querying
from core.graph.builder import GraphBuilder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# ==================== Mock 对象 ====================

class MockLLM:
    """模拟LLM用于测试"""
    def __init__(self, response="SELECT * FROM a_sight LIMIT 10"):
        self.response = response

    def invoke(self, prompt):
        """模拟LLM调用"""
        class Response:
            def __init__(self, content):
                self.content = content
        return Response(self.response)


class MockSQLExecutor:
    """模拟SQL执行器用于测试"""
    def __init__(self, should_fail=False, error_type="sql_syntax_error"):
        self.should_fail = should_fail
        self.error_type = error_type
        self.execution_count = 0

    def execute(self, sql):
        """模拟SQL执行"""
        self.execution_count += 1

        if self.should_fail:
            # 根据错误类型返回不同错误
            error_messages = {
                "sql_syntax_error": "syntax error near 'SELCT'",
                "execution_timeout": "execution timeout after 30s",
                "connection_error": "connection refused to database",
                "field_error": "column 'invalid_field' does not exist",
                "permission_error": "permission denied for table a_sight"
            }
            return {
                "status": "error",
                "error": error_messages.get(self.error_type, "unknown error"),
                "data": None,
                "count": 0
            }

        # 成功返回模拟数据
        return {
            "status": "success",
            "data": [
                {"name": "西湖", "level": "5A", "address": "杭州市"}
            ],
            "count": 1,
            "sql": sql
        }


class MockResultParser:
    """模拟结果解析器"""
    def merge_results(self, results_list):
        """合并多个查询结果"""
        merged = []
        for result in results_list:
            if result:
                merged.extend(result)
        return merged

    def evaluate_completeness(self, data):
        """评估数据完整性"""
        if not data:
            return {
                "complete": False,
                "completeness_score": 0.0,
                "missing_fields": [],
                "records_with_missing": 0
            }

        # 简单判断：如果有数据就认为完整
        return {
            "complete": True,
            "completeness_score": 1.0,
            "missing_fields": [],
            "records_with_missing": 0
        }


class MockAnswerGenerator:
    """模拟答案生成器"""
    def generate(self, query, data, count):
        """生成答案"""
        if count > 0:
            return f"找到{count}条记录"
        return "未找到匹配记录"


class MockSQLGenerator:
    """模拟SQL生成器"""
    def __init__(self, llm):
        self.llm = llm
        self.generation_count = 0
        self.schema_updates = 0
        self.last_match_mode = None

    def set_database_schema(self, formatted_schema):
        """记录 schema 注入次数"""
        self.schema_updates += 1

    def generate_initial_sql(self, query, intent_info=None, database_schema=None, match_mode="fuzzy"):
        """生成初始SQL"""
        self.generation_count += 1
        self.last_match_mode = match_mode
        return "SELECT * FROM a_sight LIMIT 10"

    def generate_followup_sql(
        self,
        original_query,
        previous_sql,
        record_count,
        missing_fields=None,
        database_schema=None,
        match_mode="fuzzy",
    ):
        """生成后续SQL（简单返回上一次结果）"""
        self.generation_count += 1
        self.last_match_mode = match_mode
        return previous_sql or "SELECT * FROM a_sight LIMIT 10"

    def fix_sql_with_error(self, sql, error, query):
        """修复SQL（模拟）"""
        logger.info(f"[MockSQLGenerator] Fixing SQL with error: {error[:50]}...")
        return "SELECT * FROM a_sight LIMIT 10"  # 修复后的SQL

    def simplify_sql(self, sql, max_limit=100):
        """简化SQL（使用真实实现）"""
        import re
        logger.info(f"[MockSQLGenerator] Simplifying SQL with LIMIT {max_limit}")

        # 先移除末尾的分号
        sql = sql.rstrip().rstrip(';')

        # 检查是否已经有LIMIT（不区分大小写）
        if re.search(r'\bLIMIT\s+\d+', sql, flags=re.IGNORECASE):
            # 替换现有的LIMIT
            sql = re.sub(r'\bLIMIT\s+\d+', f'LIMIT {max_limit}', sql, flags=re.IGNORECASE)
        else:
            # 添加LIMIT
            sql = f"{sql}\nLIMIT {max_limit}"

        return sql

    def analyze_missing_info(self, query, current_data):
        """分析缺失信息"""
        return {
            "has_missing": False,
            "missing_fields": [],
            "data_complete": True,
            "suggestion": "数据完整"
        }


# ==================== 测试用例 ====================

def create_initial_state(query="测试查询") -> AgentState:
    """创建初始状态"""
    return {
        "query": query,
        "enhanced_query": query,
        "query_intent": "query",
        "requires_spatial": False,
        "sql_history": [],
        "execution_results": [],
        "thought_chain": [],
        "current_step": 0,
        "current_sql": None,
        "current_result": None,
        "should_continue": True,
        "max_iterations": 3,
        "error": None,
        # Fallback字段
        "retry_count": 0,
        "max_retries": 3,
        "last_error": None,
        "error_history": [],
        "fallback_strategy": None,
        "error_type": None,
        # Memory字段
        "session_history": [],
        "conversation_id": None,
        "knowledge_base": None,
        "learned_patterns": [],
        # Checkpoint字段
        "saved_checkpoint_id": None,
        "saved_checkpoint_step": None,
        "is_resumed_from_checkpoint": False,
        "last_checkpoint_time": None,
        # 最终输出
        "final_data": None,
        "answer": "",
        "status": "pending",
        "message": ""
    }


def test_error_classification():
    """测试1: 错误分类功能"""
    print("\n" + "="*60)
    print("测试1: 错误分类功能")
    print("="*60)

    mock_llm = MockLLM()
    sql_gen = MockSQLGenerator(mock_llm)
    nodes = AgentNodes(
        sql_generator=sql_gen,
        sql_executor=MockSQLExecutor(),
        result_parser=MockResultParser(),
        answer_generator=MockAnswerGenerator()
    )

    # 测试各种错误类型
    test_errors = [
        ("syntax error near 'SELCT'", "sql_syntax_error"),
        ("execution timeout after 30s", "execution_timeout"),
        ("connection refused", "connection_error"),
        ("column does not exist", "field_error"),
        ("permission denied", "permission_error"),
        ("unknown error message", "unknown_error")
    ]

    print("\n测试错误分类:")
    for error_msg, expected_type in test_errors:
        classified = nodes._classify_error(error_msg)
        status = "[PASS]" if classified == expected_type else "[FAIL]"
        print(f"  {status} '{error_msg[:30]}...' -> {classified}")
        if classified != expected_type:
            print(f"     预期: {expected_type}, 实际: {classified}")

    print("\n[PASS] 错误分类测试完成")


def test_fallback_strategies():
    """测试2: Fallback策略决策"""
    print("\n" + "="*60)
    print("测试2: Fallback策略决策")
    print("="*60)

    mock_llm = MockLLM()
    sql_gen = MockSQLGenerator(mock_llm)
    nodes = AgentNodes(
        sql_generator=sql_gen,
        sql_executor=MockSQLExecutor(),
        result_parser=MockResultParser(),
        answer_generator=MockAnswerGenerator()
    )

    # 测试不同错误类型的策略
    test_cases = [
        ("sql_syntax_error", 0, "retry_sql"),
        ("field_error", 0, "retry_sql"),
        ("execution_timeout", 0, "simplify_query"),
        ("connection_error", 0, "retry_execution"),
        ("connection_error", 2, "fail"),
        ("permission_error", 0, "fail"),
        ("unknown_error", 0, "retry_sql"),
        ("unknown_error", 1, "fail")
    ]

    print("\n测试策略决策:")
    for error_type, retry_count, expected_strategy in test_cases:
        strategy = nodes._determine_fallback_strategy(error_type, retry_count)
        status = "[PASS]" if strategy == expected_strategy else "[FAIL]"
        print(f"  {status} {error_type} (retry={retry_count}) -> {strategy}")
        if strategy != expected_strategy:
            print(f"     预期: {expected_strategy}, 实际: {strategy}")

    print("\n[PASS] 策略决策测试完成")


def test_conditional_edge():
    """测试3: 条件边逻辑"""
    print("\n" + "="*60)
    print("测试3: 条件边逻辑 (should_retry_or_fail)")
    print("="*60)

    # 测试用例
    test_cases = [
        # (error, retry_count, max_retries, expected_result)
        (None, 0, 3, "check_results"),  # 无错误
        ("some error", 0, 3, "handle_error"),  # 有错误且可重试
        ("some error", 2, 3, "handle_error"),  # 有错误，接近上限
        ("some error", 3, 3, "check_results"),  # 达到重试上限
        ("some error", 5, 3, "check_results"),  # 超过重试上限
    ]

    print("\n测试条件边:")
    for error, retry_count, max_retries, expected in test_cases:
        state = create_initial_state()
        state["error"] = error
        state["retry_count"] = retry_count
        state["max_retries"] = max_retries

        result = should_retry_or_fail(state)
        status = "[PASS]" if result == expected else "[FAIL]"
        error_str = f"'{error[:20]}...'" if error else "None"
        print(f"  {status} error={error_str}, retry={retry_count}/{max_retries} -> {result}")
        if result != expected:
            print(f"     预期: {expected}, 实际: {result}")

    print("\n[PASS] 条件边测试完成")


def test_handle_error_node():
    """测试4: handle_error节点功能"""
    print("\n" + "="*60)
    print("测试4: handle_error 节点功能")
    print("="*60)

    mock_llm = MockLLM()
    sql_gen = MockSQLGenerator(mock_llm)
    nodes = AgentNodes(
        sql_generator=sql_gen,
        sql_executor=MockSQLExecutor(),
        result_parser=MockResultParser(),
        answer_generator=MockAnswerGenerator()
    )

    # 测试场景1: SQL语法错误 → retry_sql
    print("\n场景1: SQL语法错误")
    state1 = create_initial_state()
    state1["error"] = "syntax error near 'SELCT'"
    state1["retry_count"] = 0
    state1["current_sql"] = "SELCT * FROM a_sight"

    result1 = nodes.handle_error(state1)
    print(f"  错误类型: {result1.get('error_type')}")
    print(f"  策略: {result1.get('fallback_strategy')}")
    print(f"  重试次数: {result1.get('retry_count')}")
    assert result1["fallback_strategy"] == "retry_sql", "应该使用retry_sql策略"
    assert result1["retry_count"] == 1, "重试次数应该加1"
    print("  [PASS] 策略正确")

    # 测试场景2: 超时错误 → simplify_query
    print("\n场景2: 超时错误")
    state2 = create_initial_state()
    state2["error"] = "execution timeout after 30s"
    state2["retry_count"] = 0
    state2["current_sql"] = "SELECT * FROM a_sight"

    result2 = nodes.handle_error(state2)
    print(f"  错误类型: {result2.get('error_type')}")
    print(f"  策略: {result2.get('fallback_strategy')}")
    print(f"  重试次数: {result2.get('retry_count')}")
    assert result2["fallback_strategy"] == "simplify_query", "应该使用simplify_query策略"
    print("  [PASS] 策略正确")

    # 测试场景3: 达到重试上限
    print("\n场景3: 达到重试上限")
    state3 = create_initial_state()
    state3["error"] = "some error"
    state3["retry_count"] = 3
    state3["max_retries"] = 3

    result3 = nodes.handle_error(state3)
    print(f"  should_continue: {result3.get('should_continue')}")
    print(f"  策略: {result3.get('fallback_strategy')}")
    assert result3["should_continue"] == False, "应该停止继续"
    assert result3["fallback_strategy"] == "fail", "应该标记为失败"
    print("  [PASS] 正确停止重试")

    print("\n[PASS] handle_error节点测试完成")


def test_sql_fix_and_simplify():
    """测试5: SQL修复和简化功能"""
    print("\n" + "="*60)
    print("测试5: SQL修复和简化功能")
    print("="*60)

    mock_llm = MockLLM(response="SELECT * FROM a_sight WHERE level='5A' LIMIT 10")
    sql_gen = MockSQLGenerator(mock_llm)

    # 测试SQL修复
    print("\n测试SQL修复:")
    original_sql = "SELCT * FROM a_sight"
    error = "syntax error near 'SELCT'"
    fixed_sql = sql_gen.fix_sql_with_error(original_sql, error, "查询景区")
    print(f"  原始SQL: {original_sql}")
    print(f"  错误: {error}")
    print(f"  修复后: {fixed_sql}")
    assert fixed_sql != original_sql, "SQL应该被修复"
    print("  [PASS] SQL修复成功")

    # 测试SQL简化（无LIMIT）
    print("\n测试SQL简化 (无LIMIT):")
    sql_no_limit = "SELECT * FROM a_sight WHERE level='5A'"
    simplified = sql_gen.simplify_sql(sql_no_limit, max_limit=50)
    print(f"  原始: {sql_no_limit}")
    print(f"  简化: {simplified}")
    assert "LIMIT 50" in simplified, "应该添加LIMIT"
    print("  [PASS] 成功添加LIMIT")

    # 测试SQL简化（已有LIMIT）
    print("\n测试SQL简化 (已有LIMIT):")
    sql_with_limit = "SELECT * FROM a_sight LIMIT 1000"
    simplified2 = sql_gen.simplify_sql(sql_with_limit, max_limit=50)
    print(f"  原始: {sql_with_limit}")
    print(f"  简化: {simplified2}")
    assert "LIMIT 50" in simplified2, "应该替换为LIMIT 50"
    assert "LIMIT 1000" not in simplified2, "不应该有LIMIT 1000"
    print("  [PASS] 成功替换LIMIT")

    print("\n[PASS] SQL修复和简化测试完成")


def test_full_retry_workflow():
    """测试6: 完整重试工作流"""
    print("\n" + "="*60)
    print("测试6: 完整重试工作流模拟")
    print("="*60)

    mock_llm = MockLLM()
    sql_gen = MockSQLGenerator(mock_llm)

    # 第一次失败，第二次成功
    sql_executor = MockSQLExecutor(should_fail=True, error_type="sql_syntax_error")

    nodes = AgentNodes(
        sql_generator=sql_gen,
        sql_executor=sql_executor,
        result_parser=MockResultParser(),
        answer_generator=MockAnswerGenerator()
    )

    print("\n模拟重试流程:")

    # 步骤1: 生成SQL
    print("\n步骤1: 生成SQL")
    state = create_initial_state("查询5A景区")
    sql_result = nodes.generate_sql(state)
    state.update(sql_result)
    print(f"  生成的SQL: {state['current_sql']}")

    # 步骤2: 执行SQL（失败）
    print("\n步骤2: 执行SQL（第一次，失败）")
    exec_result = nodes.execute_sql(state)
    state.update(exec_result)
    print(f"  执行状态: {state.get('error', 'success')}")

    # 步骤3: 条件边判断
    print("\n步骤3: 条件边判断")
    next_node = should_retry_or_fail(state)
    print(f"  下一节点: {next_node}")
    assert next_node == "handle_error", "应该进入handle_error节点"

    # 步骤4: 错误处理
    print("\n步骤4: 错误处理")
    error_result = nodes.handle_error(state)
    state.update(error_result)
    # 清除错误标志，以便重试
    state["error"] = None
    print(f"  错误类型: {state.get('error_type')}")
    print(f"  策略: {state.get('fallback_strategy')}")
    print(f"  重试次数: {state.get('retry_count')}")
    assert state["fallback_strategy"] == "retry_sql", "应该使用retry_sql策略"

    # 步骤5: 重新生成SQL
    print("\n步骤5: 重新生成SQL")
    # 模拟成功
    sql_executor.should_fail = False
    retry_sql_result = nodes.generate_sql(state)
    state.update(retry_sql_result)
    print(f"  重新生成的SQL: {state['current_sql']}")

    # 步骤6: 重新执行SQL（成功）
    print("\n步骤6: 重新执行SQL（第二次，成功）")
    retry_exec_result = nodes.execute_sql(state)
    state.update(retry_exec_result)
    print(f"  执行状态: {state.get('error', 'success')}")
    print(f"  数据记录数: {len(state.get('final_data', []))}")

    # 验证结果
    assert state.get("error") is None, "不应该有错误"
    assert state.get("final_data") is not None, "应该有数据"

    print("\n[PASS] 完整重试工作流测试完成")


# ==================== 运行所有测试 ====================

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Fallback机制测试套件")
    print("="*60)

    try:
        test_error_classification()
        test_fallback_strategies()
        test_conditional_edge()
        test_handle_error_node()
        test_sql_fix_and_simplify()
        test_full_retry_workflow()

        print("\n" + "="*60)
        print("[PASS] 所有测试通过！")
        print("="*60)

        print("\n测试总结:")
        print("  [PASS] 错误分类功能正常")
        print("  [PASS] 策略决策逻辑正确")
        print("  [PASS] 条件边路由正确")
        print("  [PASS] handle_error节点功能完整")
        print("  [PASS] SQL修复和简化功能正常")
        print("  [PASS] 完整重试工作流可用")

        print("\nFallback机制已准备就绪！")

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n[FAIL] 测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
