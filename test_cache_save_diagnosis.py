#!/usr/bin/env python3
"""
缓存保存问题诊断脚本
检查 QueryCacheManager 的数据库保存功能
"""

import sys
import os
import logging

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'python', 'sight_server'))

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_database_connector():
    """测试数据库连接器是否正常工作"""
    try:
        from core.database import DatabaseConnector
        
        print("=== 测试数据库连接器 ===")
        
        # 创建数据库连接器
        db_connector = DatabaseConnector()
        
        # 测试数据库信息
        db_info = db_connector.get_database_info()
        print(f"✓ 数据库连接成功: {db_info}")
        
        # 测试表是否存在
        tables = db_connector.get_usable_table_names()
        print(f"✓ 可用表: {tables}")
        
        # 检查 query_cache 表是否存在
        if 'query_cache' in tables:
            print("✓ query_cache 表存在")
        else:
            print("✗ query_cache 表不存在")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"数据库连接器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_manager_initialization():
    """测试缓存管理器初始化"""
    try:
        from core.query_cache_manager import QueryCacheManager
        from core.database import DatabaseConnector
        
        print("\n=== 测试缓存管理器初始化 ===")
        
        # 创建数据库连接器
        db_connector = DatabaseConnector()
        
        # 创建缓存管理器
        cache_manager = QueryCacheManager(
            cache_dir="./test_cache_diagnosis",
            ttl=60,
            max_size=10,
            cache_strategy="hybrid",
            database_connector=db_connector
        )
        
        print(f"✓ 缓存管理器初始化成功")
        print(f"  缓存策略: {cache_manager.cache_strategy}")
        print(f"  数据库连接器: {cache_manager.database_connector is not None}")
        
        return cache_manager
        
    except Exception as e:
        logger.error(f"缓存管理器初始化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_cache_save_function(cache_manager):
    """测试缓存保存功能"""
    try:
        print("\n=== 测试缓存保存功能 ===")
        
        # 测试数据
        test_query = "测试查询：浙江省的5A景区"
        test_data = {
            "status": "success",
            "answer": "浙江省有多个5A景区，包括西湖、千岛湖等",
            "data": [{"name": "西湖", "level": "5A"}, {"name": "千岛湖", "level": "5A"}],
            "count": 2,
            "message": "查询成功",
            "sql": "SELECT * FROM scenic_spots WHERE province = '浙江省' AND level = '5A'",
            "intent_info": {"intent_type": "query"},
            "conversation_id": "test-session-123"
        }
        
        # 生成缓存键
        cache_context = {
            "enable_spatial": True,
            "query_intent": "query",
            "include_sql": True
        }
        cache_key = cache_manager.get_cache_key(test_query, cache_context)
        print(f"缓存键: {cache_key}")
        
        # 保存缓存
        print("正在保存缓存到数据库...")
        record_id = cache_manager.save_query_cache(
            query_text=test_query,
            result_data=test_data,
            response_time=0.5,
            ttl_seconds=60,
            context=cache_context
        )
        
        print(f"✓ 缓存保存成功，记录ID: {record_id}")
        
        # 验证缓存是否真的保存到数据库
        print("验证数据库中的缓存...")
        db_result = cache_manager._get_from_database(cache_key)
        if db_result:
            print(f"✓ 数据库缓存验证成功: {db_result}")
        else:
            print("✗ 数据库缓存验证失败：缓存未保存到数据库")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"缓存保存测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_retrieval(cache_manager):
    """测试缓存读取功能"""
    try:
        print("\n=== 测试缓存读取功能 ===")
        
        test_query = "测试查询：浙江省的5A景区"
        cache_context = {
            "enable_spatial": True,
            "query_intent": "query",
            "include_sql": True
        }
        cache_key = cache_manager.get_cache_key(test_query, cache_context)
        
        # 从数据库读取
        print("从数据库读取缓存...")
        result = cache_manager.get_query_cache(cache_key)
        
        if result:
            print(f"✓ 缓存读取成功: {result}")
            return True
        else:
            print("✗ 缓存读取失败")
            return False
            
    except Exception as e:
        logger.error(f"缓存读取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_cache_strategy_details(cache_manager):
    """检查缓存策略的详细信息"""
    print("\n=== 检查缓存策略详细信息 ===")
    
    print(f"缓存策略: {cache_manager.cache_strategy}")
    print(f"数据库连接器: {cache_manager.database_connector is not None}")
    print(f"缓存目录: {cache_manager.cache_dir}")
    print(f"TTL: {cache_manager.ttl}秒")
    
    # 检查缓存统计
    stats = cache_manager.get_cache_stats()
    print(f"缓存统计: {stats}")

def main():
    """主测试函数"""
    print("开始缓存保存问题诊断...\n")
    
    # 1. 测试数据库连接器
    if not test_database_connector():
        print("❌ 数据库连接器测试失败")
        return False
    
    # 2. 测试缓存管理器初始化
    cache_manager = test_cache_manager_initialization()
    if not cache_manager:
        print("❌ 缓存管理器初始化测试失败")
        return False
    
    # 3. 检查缓存策略详细信息
    check_cache_strategy_details(cache_manager)
    
    # 4. 测试缓存保存
    if not test_cache_save_function(cache_manager):
        print("❌ 缓存保存测试失败")
        return False
    
    # 5. 测试缓存读取
    if not test_cache_retrieval(cache_manager):
        print("❌ 缓存读取测试失败")
        return False
    
    print("\n🎉 所有测试通过！缓存保存功能正常")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
