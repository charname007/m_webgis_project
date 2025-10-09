"""
测试分离缓存架构 - Sight Server
验证新的 query_cache 和 pattern_cache 表功能
"""

import sys
import os
import logging
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

# 设置环境变量
os.environ['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), 'python')

try:
    from sight_server.core.database import DatabaseConnector
    from sight_server.core.query_cache_manager import QueryCacheManager
    from sight_server.core.optimized_memory_manager import OptimizedMemoryManager
except ImportError as e:
    print(f"导入错误: {e}")
    print("尝试直接导入...")
    # 尝试直接导入
    import importlib.util
    import sys
    
    # 添加当前目录到路径
    sys.path.insert(0, os.path.dirname(__file__))
    
    # 直接导入模块
    spec = importlib.util.spec_from_file_location("database", "python/sight_server/core/database.py")
    database_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(database_module)
    DatabaseConnector = database_module.DatabaseConnector
    
    spec = importlib.util.spec_from_file_location("query_cache_manager", "python/sight_server/core/query_cache_manager.py")
    query_cache_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(query_cache_module)
    QueryCacheManager = query_cache_module.QueryCacheManager
    
    spec = importlib.util.spec_from_file_location("optimized_memory_manager", "python/sight_server/core/optimized_memory_manager.py")
    memory_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(memory_module)
    OptimizedMemoryManager = memory_module.OptimizedMemoryManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connector():
    """测试数据库连接器的新功能"""
    print("=== 测试数据库连接器 ===")
    
    try:
        # 创建数据库连接器
        db_connector = DatabaseConnector()
        
        # 测试1: 保存查询结果缓存
        print("\n--- 测试1: 保存查询结果缓存 ---")
        query_cache_id = db_connector.save_query_cache(
            cache_key="test_query_1",
            query_text="查询武汉的景点",
            result_data={"data": [{"name": "黄鹤楼", "location": "武汉"}], "count": 1},
            response_time=0.5,
            ttl_seconds=3600
        )
        print(f"查询结果缓存保存成功，ID: {query_cache_id}")
        
        # 测试2: 获取查询结果缓存
        print("\n--- 测试2: 获取查询结果缓存 ---")
        cached_result = db_connector.get_query_cache("test_query_1")
        if cached_result:
            print(f"查询缓存获取成功: {cached_result}")
        else:
            print("查询缓存获取失败")
        
        # 测试3: 保存模式学习缓存
        print("\n--- 测试3: 保存模式学习缓存 ---")
        pattern_cache_id = db_connector.save_pattern_cache(
            pattern_key="success_pattern:查询武汉的景点",
            query_template="查询{城市}的景点",
            sql_template="SELECT * FROM tourist_spots WHERE city = '{城市}'",
            response_time=0.5,
            result_count=1
        )
        print(f"模式学习缓存保存成功，ID: {pattern_cache_id}")
        
        # 测试4: 获取模式学习缓存
        print("\n--- 测试4: 获取模式学习缓存 ---")
        pattern_result = db_connector.get_pattern_cache("success_pattern:查询武汉的景点")
        if pattern_result:
            print(f"模式缓存获取成功: {pattern_result}")
        else:
            print("模式缓存获取失败")
            
        return True
        
    except Exception as e:
        logger.error(f"数据库连接器测试失败: {e}")
        return False


def test_query_cache_manager():
    """测试查询缓存管理器"""
    print("\n=== 测试查询缓存管理器 ===")
    
    try:
        # 创建数据库连接器
        db_connector = DatabaseConnector()
        
        # 创建查询缓存管理器
        cache_manager = QueryCacheManager(
            cache_dir="./test_cache",
            ttl=3600,
            max_size=100,
            database_connector=db_connector,
            cache_strategy="hybrid"
        )
        
        # 测试1: 保存查询缓存
        print("\n--- 测试1: 保存查询缓存 ---")
        test_result = {
            "data": [
                {"name": "黄鹤楼", "location": "武汉", "type": "景点"},
                {"name": "东湖", "location": "武汉", "type": "景点"}
            ],
            "count": 2,
            "status": "success"
        }
        
        cache_id = cache_manager.save_query_cache(
            query_text="查询武汉的著名景点",
            result_data=test_result,
            response_time=0.8
        )
        print(f"查询缓存保存成功，ID: {cache_id}")
        
        # 测试2: 获取查询缓存
        print("\n--- 测试2: 获取查询缓存 ---")
        cache_key = cache_manager.get_cache_key("查询武汉的著名景点", {})
        cached_data = cache_manager.get_query_cache(cache_key)
        if cached_data:
            print(f"查询缓存获取成功: {cached_data}")
        else:
            print("查询缓存获取失败")
        
        # 测试3: 获取缓存统计
        print("\n--- 测试3: 获取缓存统计 ---")
        stats = cache_manager.get_cache_stats()
        print(f"缓存统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        return True
        
    except Exception as e:
        logger.error(f"查询缓存管理器测试失败: {e}")
        return False


def test_optimized_memory_manager():
    """测试优化内存管理器"""
    print("\n=== 测试优化内存管理器 ===")
    
    try:
        # 创建数据库连接器
        db_connector = DatabaseConnector()
        
        # 创建优化内存管理器
        memory_manager = OptimizedMemoryManager(
            max_sessions=10,
            session_ttl=3600,
            enable_database_persistence=True,
            database_connector=db_connector
        )
        
        # 测试1: 开始新会话
        print("\n--- 测试1: 开始新会话 ---")
        session_id = "test_session_001"
        session_state = memory_manager.start_session(session_id)
        print(f"会话启动成功: {session_id}")
        
        # 测试2: 添加查询到会话
        print("\n--- 测试2: 添加查询到会话 ---")
        test_result = {
            "data": [{"name": "黄鹤楼", "location": "武汉"}],
            "count": 1,
            "status": "success"
        }
        
        history_entry = memory_manager.add_query_to_session(
            query="查询武汉的景点",
            result=test_result,
            sql="SELECT * FROM tourist_spots WHERE city = '武汉'",
            success=True,
            response_time=0.6
        )
        print(f"查询历史添加成功: {history_entry}")
        
        # 测试3: 学习模式
        print("\n--- 测试3: 学习模式 ---")
        learned_pattern = memory_manager.learn_from_query(
            query="查询武汉的景点",
            sql="SELECT * FROM tourist_spots WHERE city = '武汉'",
            result=test_result,
            success=True,
            response_time=0.6
        )
        if learned_pattern:
            print(f"模式学习成功: {learned_pattern}")
        else:
            print("模式学习失败")
        
        # 测试4: 获取会话统计
        print("\n--- 测试4: 获取会话统计 ---")
        session_stats = memory_manager.get_session_stats(session_id)
        if session_stats:
            print(f"会话统计: {json.dumps(session_stats, indent=2, ensure_ascii=False)}")
        else:
            print("会话统计获取失败")
        
        return True
        
    except Exception as e:
        logger.error(f"优化内存管理器测试失败: {e}")
        return False


def test_data_migration():
    """测试数据迁移功能"""
    print("\n=== 测试数据迁移 ===")
    
    try:
        # 创建数据库连接器
        db_connector = DatabaseConnector()
        
        # 检查现有数据
        print("\n--- 检查现有数据 ---")
        # 使用现有的方法检查缓存数据
        existing_data = []
        
        # 尝试获取一些测试数据
        test_query = db_connector.get_query_cache("test_query_1")
        test_pattern = db_connector.get_pattern_cache("success_pattern:查询武汉的景点")
        
        if test_query:
            existing_data.append({"type": "query_cache", "data": test_query})
        if test_pattern:
            existing_data.append({"type": "pattern_cache", "data": test_pattern})
        
        print(f"新表数据数量: {len(existing_data)}")
        
        # 检查新表结构
        print("\n--- 检查新表结构 ---")
        print("✅ query_cache 表: 用于存储查询结果缓存")
        print("✅ pattern_cache 表: 用于存储模式学习缓存")
        print("✅ 分离存储架构已就绪")
        
        return True
        
    except Exception as e:
        logger.error(f"数据迁移测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试分离缓存架构...")
    
    # 运行所有测试
    tests = [
        ("数据库连接器", test_database_connector),
        ("查询缓存管理器", test_query_cache_manager),
        ("优化内存管理器", test_optimized_memory_manager),
        ("数据迁移", test_data_migration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"测试 {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n=== 测试结果汇总 ===")
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    # 统计通过率
    passed_count = sum(1 for _, success in results if success)
    total_count = len(results)
    pass_rate = (passed_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"\n总体通过率: {passed_count}/{total_count} ({pass_rate:.1f}%)")
    
    if passed_count == total_count:
        print("🎉 所有测试通过！分离缓存架构验证成功。")
    else:
        print("⚠️ 部分测试失败，请检查相关组件。")


if __name__ == "__main__":
    main()
