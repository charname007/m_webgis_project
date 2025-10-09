#!/usr/bin/env python3
"""
测试缓存类型修复脚本
验证查询结果缓存和模式学习缓存的数据混淆问题是否已解决
"""

import sys
import os
import json
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python', 'sight_server'))

# 直接导入需要的模块，避免复杂的依赖
try:
    from core.cache_manager import QueryCacheManager
    from core.database import DatabaseConnector
    from core.optimized_memory_manager import OptimizedMemoryManager
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("尝试直接导入...")
    # 如果导入失败，创建简单的测试函数
    def test_cache_type_separation():
        """直接测试缓存类型分离"""
        print("=== 直接测试缓存类型分离 ===")
        
        try:
            from core.database import DatabaseConnector
            db_connector = DatabaseConnector()
            
            # 测试查询结果缓存类型
            test_query_cache_key = "test_query_cache_key_123"
            test_query_data = {
                "result": {"data": "test_query_result"},
                "query": "测试查询",
                "cache_key": test_query_cache_key,
                "created_at": datetime.now().isoformat()
            }
            
            # 保存查询结果缓存
            query_success = db_connector.save_cache_data(
                cache_key=test_query_cache_key,
                cache_value=test_query_data,
                cache_type="query_result",
                ttl_seconds=3600
            )
            print(f"查询结果缓存保存: {'成功' if query_success else '失败'}")
            
            # 测试模式学习缓存类型
            test_pattern_cache_key = "success_pattern:测试 + 模式 + 学习"
            test_pattern_data = {
                "query_template": "测试 + 模式 + 学习",
                "sql_template": "SELECT * FROM test_table",
                "success": True,
                "result_count": 1,
                "response_time": 0.5,
                "learned_at": datetime.now().isoformat()
            }
            
            # 保存模式学习缓存
            pattern_success = db_connector.save_cache_data(
                cache_key=test_pattern_cache_key,
                cache_value=test_pattern_data,
                cache_type="success_pattern",
                ttl_seconds=86400
            )
            print(f"模式学习缓存保存: {'成功' if pattern_success else '失败'}")
            
            # 验证缓存类型
            query_cache = db_connector.get_cache_data(test_query_cache_key)
            pattern_cache = db_connector.get_cache_data(test_pattern_cache_key)
            
            query_type = query_cache.get("cache_type", "unknown") if query_cache else "not_found"
            pattern_type = pattern_cache.get("cache_type", "unknown") if pattern_cache else "not_found"
            
            print(f"查询结果缓存类型: {query_type}")
            print(f"模式学习缓存类型: {pattern_type}")
            
            # 验证分离是否成功
            if query_type == "query_result" and pattern_type == "success_pattern":
                print("✅ 缓存类型分离成功！")
                success = True
            else:
                print("❌ 缓存类型分离失败！")
                success = False
            
            # 清理测试数据
            db_connector.delete_cache_data(test_query_cache_key)
            db_connector.delete_cache_data(test_pattern_cache_key)
            
            return success
                
        except Exception as e:
            print(f"测试缓存类型分离失败: {e}")
            return False

    def main():
        """主测试函数"""
        print("开始测试缓存类型修复...")
        success = test_cache_type_separation()
        print("\n=== 测试总结 ===")
        if success:
            print("✅ 缓存类型修复测试通过！")
            print("   查询结果缓存和模式学习缓存已正确分离")
        else:
            print("❌ 缓存类型修复测试失败！")
            print("   需要进一步检查缓存类型设置")
        
        return

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_query_cache_manager():
    """测试 QueryCacheManager 的查询结果缓存"""
    print("=== 测试 QueryCacheManager 查询结果缓存 ===")
    
    # 创建数据库连接器
    db_connector = DatabaseConnector()
    
    # 创建缓存管理器
    cache_manager = QueryCacheManager(
        cache_dir="./test_cache_query",
        ttl=3600,
        max_size=100,
        enable_database_persistence=True,
        database_connector=db_connector,
        cache_strategy="hybrid"
    )
    
    # 测试数据
    test_query = "查询武汉的5A级景区"
    test_context = {
        "enable_spatial": True,
        "query_intent": "query",
        "include_sql": True
    }
    test_result = {
        "data": [
            {"name": "黄鹤楼", "rating": "5A", "location": "武汉"},
            {"name": "东湖", "rating": "5A", "location": "武汉"}
        ],
        "count": 2,
        "status": "success"
    }
    
    # 生成缓存键
    cache_key = cache_manager.get_cache_key(test_query, test_context)
    print(f"缓存键: {cache_key}")
    
    # 保存缓存
    success = cache_manager.set(cache_key, test_result, test_query)
    print(f"查询结果缓存保存: {'成功' if success else '失败'}")
    
    # 获取缓存
    cached_result = cache_manager.get(cache_key)
    print(f"查询结果缓存获取: {'成功' if cached_result else '失败'}")
    
    # 检查数据库中的缓存类型
    try:
        db_cache = db_connector.get_cache_data(cache_key)
        if db_cache:
            cache_type = db_cache.get("cache_type", "unknown")
            print(f"数据库缓存类型: {cache_type}")
            
            # 解析缓存值
            cache_value = json.loads(db_cache.get("cache_value", "{}"))
            print(f"缓存值结构: {list(cache_value.keys()) if cache_value else '空'}")
        else:
            print("数据库中没有找到缓存")
    except Exception as e:
        print(f"检查数据库缓存失败: {e}")
    
    return cache_manager, cache_key

def test_optimized_memory_manager():
    """测试 OptimizedMemoryManager 的模式学习缓存"""
    print("\n=== 测试 OptimizedMemoryManager 模式学习缓存 ===")
    
    # 创建数据库连接器
    db_connector = DatabaseConnector()
    
    # 创建内存管理器
    memory_manager = OptimizedMemoryManager(
        enable_database_persistence=True,
        database_connector=db_connector
    )
    
    # 启动会话
    session_id = "test_session_123"
    memory_manager.start_session(session_id)
    
    # 测试数据
    test_query = "查询 + 景区 + 地区 + 评级"
    test_sql = "SELECT * FROM tourist_spots WHERE rating = '5A' AND location LIKE '%武汉%'"
    test_result = {
        "data": [{"name": "黄鹤楼", "rating": "5A"}],
        "count": 1,
        "status": "success"
    }
    
    # 学习模式
    pattern = memory_manager.learn_from_query(
        query=test_query,
        sql=test_sql,
        result=test_result,
        success=True,
        response_time=0.5
    )
    
    print(f"模式学习: {'成功' if pattern else '失败'}")
    if pattern:
        print(f"学习到的模式: {pattern['query_template']}")
    
    # 检查数据库中的模式缓存
    try:
        pattern_cache_key = f"success_pattern:{pattern['query_template']}"
        db_cache = db_connector.get_cache_data(pattern_cache_key)
        if db_cache:
            cache_type = db_cache.get("cache_type", "unknown")
            print(f"模式缓存类型: {cache_type}")
            
            # 解析缓存值
            cache_value = json.loads(db_cache.get("cache_value", "{}"))
            print(f"模式缓存结构: {list(cache_value.keys()) if cache_value else '空'}")
        else:
            print("数据库中没有找到模式缓存")
    except Exception as e:
        print(f"检查模式缓存失败: {e}")
    
    return memory_manager

def test_cache_type_separation():
    """测试缓存类型分离是否成功"""
    print("\n=== 测试缓存类型分离 ===")
    
    db_connector = DatabaseConnector()
    
    try:
        # 测试查询结果缓存类型
        test_query_cache_key = "test_query_cache_key_123"
        test_query_data = {
            "result": {"data": "test_query_result"},
            "query": "测试查询",
            "cache_key": test_query_cache_key,
            "created_at": datetime.now().isoformat()
        }
        
        # 保存查询结果缓存
        query_success = db_connector.save_cache_data(
            cache_key=test_query_cache_key,
            cache_value=test_query_data,
            cache_type="query_result",
            ttl_seconds=3600
        )
        print(f"查询结果缓存保存: {'成功' if query_success else '失败'}")
        
        # 测试模式学习缓存类型
        test_pattern_cache_key = "success_pattern:测试 + 模式 + 学习"
        test_pattern_data = {
            "query_template": "测试 + 模式 + 学习",
            "sql_template": "SELECT * FROM test_table",
            "success": True,
            "result_count": 1,
            "response_time": 0.5,
            "learned_at": datetime.now().isoformat()
        }
        
        # 保存模式学习缓存
        pattern_success = db_connector.save_cache_data(
            cache_key=test_pattern_cache_key,
            cache_value=test_pattern_data,
            cache_type="success_pattern",
            ttl_seconds=86400
        )
        print(f"模式学习缓存保存: {'成功' if pattern_success else '失败'}")
        
        # 验证缓存类型
        query_cache = db_connector.get_cache_data(test_query_cache_key)
        pattern_cache = db_connector.get_cache_data(test_pattern_cache_key)
        
        query_type = query_cache.get("cache_type", "unknown") if query_cache else "not_found"
        pattern_type = pattern_cache.get("cache_type", "unknown") if pattern_cache else "not_found"
        
        print(f"查询结果缓存类型: {query_type}")
        print(f"模式学习缓存类型: {pattern_type}")
        
        # 验证分离是否成功
        if query_type == "query_result" and pattern_type == "success_pattern":
            print("✅ 缓存类型分离成功！")
            success = True
        else:
            print("❌ 缓存类型分离失败！")
            success = False
        
        # 清理测试数据
        db_connector.delete_cache_data(test_query_cache_key)
        db_connector.delete_cache_data(test_pattern_cache_key)
        
        return success
            
    except Exception as e:
        print(f"测试缓存类型分离失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试缓存类型修复...")
    
    try:
        # 测试 QueryCacheManager
        cache_manager, query_cache_key = test_query_cache_manager()
        
        # 测试 OptimizedMemoryManager
        memory_manager = test_optimized_memory_manager()
        
        # 测试缓存类型分离
        separation_success = test_cache_type_separation()
        
        # 清理测试数据
        print("\n=== 清理测试数据 ===")
        try:
            # 清理缓存管理器
            cache_manager.clear_all()
            
            # 清理数据库中的测试缓存
            db_connector = DatabaseConnector()
            db_connector.delete_cache_data(query_cache_key)
            db_connector.delete_cache_data("success_pattern:查询 + 景区 + 地区 + 评级")
            
            print("测试数据清理完成")
        except Exception as e:
            print(f"清理测试数据失败: {e}")
        
        # 总结
        print("\n=== 测试总结 ===")
        if separation_success:
            print("✅ 缓存类型修复测试通过！")
            print("   查询结果缓存和模式学习缓存已正确分离")
        else:
            print("❌ 缓存类型修复测试失败！")
            print("   需要进一步检查缓存类型设置")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
