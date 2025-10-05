"""
测试SQL历史记录功能
"""
import sys
sys.path.insert(0, 'E:/study/class/m_webgis_project/python/sight_server')

from core.graph.nodes import AgentNodes
from core.processors.sql_generator import SQLGenerator
from core.processors.sql_executor import SQLExecutor
from core.processors.result_parser import ResultParser
from core.processors.answer_generator import AnswerGenerator

# 创建Mock数据库连接器
class MockDBConnector:
    def execute_raw_query(self, sql):
        """模拟返回字典列表（修复后的行为）"""
        print(f"[MockDB] Executing: {sql[:50]}...")
        # 模拟返回RealDictRow格式
        return [
            {'json_agg': [
                {'name': '西湖', 'level': '5A'},
                {'name': '千岛湖', 'level': '5A'}
            ]}
        ]

# 创建Mock LLM
class MockLLM:
    class InnerLLM:
        def invoke(self, prompt):
            return "SELECT json_agg(json_build_object('name', a.name)) FROM a_sight a"

    def __init__(self):
        self.llm = self.InnerLLM()

# 测试
def test_sql_history():
    print("="*60)
    print("测试SQL历史记录功能")
    print("="*60)

    # 创建组件
    db_connector = MockDBConnector()
    llm = MockLLM()

    sql_generator = SQLGenerator(llm, "test prompt")
    sql_executor = SQLExecutor(db_connector)
    result_parser = ResultParser()
    answer_generator = AnswerGenerator(None)

    nodes = AgentNodes(sql_generator, sql_executor, result_parser, answer_generator)

    # 测试1: generate_sql
    print("\n--- 测试1: generate_sql 节点 ---")
    state1 = {
        'query': '查询杭州的5A景区',
        'enhanced_query': '查询杭州的5A景区',
        'current_step': 0
    }

    result1 = nodes.generate_sql(state1)
    print(f"返回的keys: {list(result1.keys())}")
    print(f"current_sql: {result1.get('current_sql', 'None')[:50] if result1.get('current_sql') else 'None'}...")
    print(f"sql_history在返回值中: {'sql_history' in result1}")

    if 'sql_history' in result1:
        print(f"FAIL: generate_sql should not return sql_history")
        return False
    else:
        print(f"PASS: generate_sql correctly does not return sql_history")

    # 测试2: execute_sql
    print("\n--- 测试2: execute_sql 节点 ---")
    state2 = {
        'current_sql': result1['current_sql'],
        'current_step': 0
    }

    result2 = nodes.execute_sql(state2)
    print(f"返回的keys: {list(result2.keys())}")
    print(f"sql_history在返回值中: {'sql_history' in result2}")

    if 'sql_history' in result2:
        sql_history = result2['sql_history']
        print(f"sql_history: {sql_history}")
        print(f"sql_history长度: {len(sql_history)}")

        if len(sql_history) > 0:
            print(f"PASS: execute_sql correctly returned sql_history")
            print(f"  SQL: {sql_history[0][:60]}...")
        else:
            print(f"FAIL: sql_history is empty")
            return False
    else:
        print(f"FAIL: execute_sql did not return sql_history")
        return False

    # 测试3: 检查final_data
    print("\n--- 测试3: 检查数据解析 ---")
    final_data = result2.get('final_data')
    print(f"final_data类型: {type(final_data)}")
    print(f"final_data: {final_data}")

    if final_data is not None and len(final_data) > 0:
        print(f"PASS: Data parsed successfully, {len(final_data)} records")
    else:
        print(f"FAIL: Data parsing failed")
        return False

    print("\n" + "="*60)
    print("SUCCESS: All tests passed! SQL history works correctly")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_sql_history()
    sys.exit(0 if success else 1)
