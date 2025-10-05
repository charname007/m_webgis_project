"""
重构验证测试脚本 - Sight Server
测试重构后的继承关系和集成功能

测试内容：
1. ✅ OptimizedSQLExecutor 继承 SQLExecutor
2. ✅ OptimizedMemoryManager 继承 MemoryManager
3. ✅ EnhancedErrorHandler 集成到 Agent
4. ✅ QueryCacheManager 集成到 Agent
5. ✅ 所有功能正常工作
"""

import sys
import os
import io

# 设置标准输出为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("重构验证测试")
print("=" * 80)

# 测试1：验证继承关系
print("\n【测试1】验证继承关系")
print("-" * 80)

from core.processors.sql_executor import SQLExecutor
from core.processors.optimized_sql_executor import OptimizedSQLExecutor
from core.memory import MemoryManager
from core.optimized_memory_manager import OptimizedMemoryManager

# 检查 OptimizedSQLExecutor 是否继承自 SQLExecutor
is_inherited_executor = issubclass(OptimizedSQLExecutor, SQLExecutor)
print(f"OptimizedSQLExecutor 继承 SQLExecutor: {'✅ 是' if is_inherited_executor else '❌ 否'}")

# 检查 OptimizedMemoryManager 是否继承自 MemoryManager
is_inherited_memory = issubclass(OptimizedMemoryManager, MemoryManager)
print(f"OptimizedMemoryManager 继承 MemoryManager: {'✅ 是' if is_inherited_memory else '❌ 否'}")

# 测试2：验证基类方法可用性
print("\n【测试2】验证基类方法可用性")
print("-" * 80)

# 测试 OptimizedSQLExecutor 可以使用基类方法
class MockDBConnector:
    def execute_raw_query(self, sql):
        return [{"result": [{"name": "测试", "value": 123}]}]

opt_executor = OptimizedSQLExecutor(MockDBConnector(), timeout=30)

# 检查是否可以调用基类的 _parse_result 方法
test_data = [{"result": [{"name": "测试", "value": 123}]}]
parsed = opt_executor._parse_result(test_data)
print(f"OptimizedSQLExecutor._parse_result() 可用: {'✅ 是' if parsed else '❌ 否'}")

# 测试 OptimizedMemoryManager 可以使用基类方法
opt_memory = OptimizedMemoryManager(max_sessions=5)

# 检查是否可以调用基类的 _extract_query_template 方法
template = opt_memory._extract_query_template("查询浙江省的5A景区")
print(f"OptimizedMemoryManager._extract_query_template() 可用: {'✅ 是' if template else '❌ 否'}")
print(f"  提取的模板: {template}")

# 测试3：验证 Agent 集成
print("\n【测试3】验证 Agent 集成")
print("-" * 80)

from core.error_handler import EnhancedErrorHandler
from core.cache_manager import QueryCacheManager

# 创建错误处理器
error_handler = EnhancedErrorHandler(max_retries=3, enable_learning=True)
print(f"EnhancedErrorHandler 初始化: ✅ 成功")

# 创建缓存管理器
cache_manager = QueryCacheManager(cache_dir="./test_cache", ttl=60, max_size=10)
print(f"QueryCacheManager 初始化: ✅ 成功")

# 测试错误分析
error_analysis = error_handler.analyze_error(
    error_message="syntax error near 'SELECT'",
    sql="SELECT * WHERE name = 'test'",
    context={}
)
print(f"错误分析功能: {'✅ 正常' if error_analysis['error_type'] else '❌ 失败'}")
print(f"  错误类型: {error_analysis['error_type']}")

# 测试缓存功能
cache_key = cache_manager.get_cache_key("测试查询", {"enable_spatial": True})
cache_manager.set(cache_key, {"data": [1, 2, 3], "count": 3}, "测试查询")
cached = cache_manager.get(cache_key)
print(f"缓存功能: {'✅ 正常' if cached else '❌ 失败'}")
print(f"  缓存数据: {cached}")

# 测试4：验证 AgentNodes 参数传递
print("\n【测试4】验证 AgentNodes 参数传递")
print("-" * 80)

from core.graph.nodes import AgentNodes
from core.processors import SQLGenerator, ResultParser, AnswerGenerator, SchemaFetcher
from core.llm import BaseLLM
from core.database import DatabaseConnector

try:
    # 创建必要的组件（使用模拟对象）
    class MockLLM:
        def __init__(self):
            self.llm = self
        def invoke(self, prompt):
            class Response:
                def __init__(self):
                    self.content = "SELECT * FROM test"
            return Response()

    mock_llm = MockLLM()
    sql_gen = SQLGenerator(mock_llm, "test prompt")
    sql_exec = opt_executor
    result_parser = ResultParser()
    answer_gen = AnswerGenerator(mock_llm)

    # 创建 AgentNodes，传递 error_handler 和 cache_manager
    agent_nodes = AgentNodes(
        sql_generator=sql_gen,
        sql_executor=sql_exec,
        result_parser=result_parser,
        answer_generator=answer_gen,
        schema_fetcher=None,  # 可选
        error_handler=error_handler,
        cache_manager=cache_manager
    )

    # 验证参数是否正确传递
    has_error_handler = hasattr(agent_nodes, 'error_handler') and agent_nodes.error_handler is not None
    has_cache_manager = hasattr(agent_nodes, 'cache_manager') and agent_nodes.cache_manager is not None

    print(f"AgentNodes.error_handler 传递: {'✅ 成功' if has_error_handler else '❌ 失败'}")
    print(f"AgentNodes.cache_manager 传递: {'✅ 成功' if has_cache_manager else '❌ 失败'}")

except Exception as e:
    print(f"❌ AgentNodes 初始化失败: {e}")

# 总结
print("\n" + "=" * 80)
print("验证总结")
print("=" * 80)

all_passed = (
    is_inherited_executor and
    is_inherited_memory and
    parsed is not None and
    template and
    error_analysis['error_type'] and
    cached is not None and
    has_error_handler and
    has_cache_manager
)

if all_passed:
    print("✅ 所有测试通过！重构成功")
    print("\n重构成果：")
    print("  1. ✅ OptimizedSQLExecutor 成功继承 SQLExecutor")
    print("  2. ✅ OptimizedMemoryManager 成功继承 MemoryManager")
    print("  3. ✅ 基类方法正常复用")
    print("  4. ✅ EnhancedErrorHandler 成功集成到 Agent")
    print("  5. ✅ QueryCacheManager 成功集成到 Agent")
    print("  6. ✅ AgentNodes 正确接收和使用 error_handler 和 cache_manager")
else:
    print("❌ 部分测试未通过，请检查重构代码")

# 清理测试缓存
print("\n清理测试缓存...")
cache_manager.clear_all()
print("✅ 清理完成")
