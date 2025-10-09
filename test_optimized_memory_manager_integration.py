"""
测试优化内存管理器与数据库集成功能
"""

import logging
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python', 'sight_server'))

from core.optimized_memory_manager import OptimizedMemoryManager
from core.database import DatabaseConnector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_optimized_memory_manager():
    """测试优化内存管理器与数据库集成"""
    print("=== 测试优化内存管理器与数据库集成 ===\n")
    
    try:
        # 创建数据库连接器
        print("--- 创建数据库连接器 ---")
        db_connector = DatabaseConnector()
        print("✓ 数据库连接器创建成功")
        
        # 创建优化内存管理器
        print("\n--- 创建优化内存管理器 ---")
        memory_manager = OptimizedMemoryManager(
            max_sessions=5,
            session_ttl=300,  # 5分钟，便于测试
            enable_database_persistence=True,
            database_connector=db_connector
        )
        print("✓ 优化内存管理器创建成功")
        
        # 测试1: 创建会话
        print("\n--- 测试1: 创建会话 ---")
        session_id = "test_session_001"
        session_state = memory_manager.start_session(session_id)
        print(f"✓ 会话创建成功: {session_id}")
        print(f"  会话状态: {session_state['conversation_id']}")
        
        # 测试2: 添加查询历史
        print("\n--- 测试2: 添加查询历史 ---")
        query_result = memory_manager.add_query_to_session(
            query="查询浙江省的5A景区",
            result={"count": 10, "data": [{"name": "西湖", "level": "5A"}]},
            sql="SELECT * FROM a_sight WHERE province='浙江省' AND level='5A'",
            success=True,
            response_time=1.5
        )
        print(f"✓ 查询历史添加成功")
        print(f"  查询: {query_result['query'][:30]}...")
        print(f"  响应时间: {query_result['response_time']}s")
        
        # 测试3: 保存中间步骤
        print("\n--- 测试3: 保存中间步骤 ---")
        step_result = memory_manager.save_step(
            step_type="sql_generation",
            step_data={
                "query": "查询浙江省的5A景区",
                "generated_sql": "SELECT * FROM a_sight WHERE province='浙江省' AND level='5A'",
                "intent_info": {"intent_type": "spatial_query"},
                "step_number": 1
            },
            importance=2
        )
        if step_result:
            print(f"✓ 中间步骤保存成功")
            print(f"  步骤类型: {step_result['step_type']}")
            print(f"  重要性: {step_result['importance']}")
        else:
            print("✗ 中间步骤保存失败")
        
        # 测试4: 学习模式
        print("\n--- 测试4: 学习模式 ---")
        pattern = memory_manager.learn_from_query(
            query="查询浙江省的5A景区",
            sql="SELECT * FROM a_sight WHERE province='浙江省' AND level='5A'",
            result={"count": 10},
            success=True,
            response_time=1.5
        )
        if pattern:
            print(f"✓ 学习模式成功")
            print(f"  查询模板: {pattern['query_template']}")
            print(f"  SQL模板: {pattern['sql_template']}")
        else:
            print("✗ 学习模式失败")
        
        # 测试5: 获取会话统计
        print("\n--- 测试5: 获取会话统计 ---")
        stats = memory_manager.get_session_stats(session_id)
        if stats:
            print(f"✓ 会话统计获取成功")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print("✗ 会话统计获取失败")
        
        # 测试6: 从数据库获取会话历史
        print("\n--- 测试6: 从数据库获取会话历史 ---")
        try:
            db_history = db_connector.get_conversation_history(session_id, limit=5)
            print(f"✓ 数据库会话历史获取成功")
            print(f"  历史记录数量: {len(db_history)}")
            for record in db_history:
                print(f"  - 查询: {record['query_text'][:30]}...")
                print(f"    状态: {record['status']}")
                print(f"    时间: {record['created_at']}")
        except Exception as e:
            print(f"✗ 数据库会话历史获取失败: {e}")
        
        # 测试7: 从数据库获取AI上下文
        print("\n--- 测试7: 从数据库获取AI上下文 ---")
        try:
            db_context = db_connector.get_ai_context(session_id)
            print(f"✓ 数据库AI上下文获取成功")
            print(f"  上下文记录数量: {len(db_context)}")
            for record in db_context:
                print(f"  - 类型: {record['context_type']}")
                print(f"    时间: {record['created_at']}")
        except Exception as e:
            print(f"✗ 数据库AI上下文获取失败: {e}")
        
        # 测试8: 从数据库获取会话统计
        print("\n--- 测试8: 从数据库获取会话统计 ---")
        try:
            db_stats = db_connector.get_session_statistics(session_id)
            print(f"✓ 数据库会话统计获取成功")
            if db_stats:
                query_stats = db_stats.get('query_statistics', {})
                context_stats = db_stats.get('context_statistics', {})
                print(f"  查询统计:")
                print(f"    - 总查询数: {query_stats.get('total_queries', 0)}")
                print(f"    - 成功查询数: {query_stats.get('successful_queries', 0)}")
                print(f"    - 平均执行时间: {query_stats.get('avg_execution_time', 0)}")
                print(f"  上下文统计:")
                print(f"    - 上下文数量: {context_stats.get('context_count', 0)}")
                print(f"    - 上下文类型: {context_stats.get('context_types', 0)}")
        except Exception as e:
            print(f"✗ 数据库会话统计获取失败: {e}")
        
        # 测试9: 清理会话
        print("\n--- 测试9: 清理会话 ---")
        cleared_count = memory_manager.clear_all_sessions()
        print(f"✓ 清理会话成功")
        print(f"  清理的会话数量: {cleared_count}")
        
        print("\n=== 所有测试完成 ===")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimized_memory_manager()
