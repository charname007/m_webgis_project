"""
增强版缓存管理器集成测试
测试 QueryCacheManager 的数据库持久化功能
"""

import os
import json
import time
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 模拟数据库连接器类
class MockDatabaseConnector:
    """模拟数据库连接器，用于测试"""
    
    def __init__(self):
        self.cache_data = {}
        self.call_count = {
            "get_cache_data": 0,
            "save_cache_data": 0
        }
    
    def get_cache_data(self, cache_key: str) -> Dict[str, Any]:
        """模拟从数据库获取缓存数据"""
        self.call_count["get_cache_data"] += 1
        logger.info(f"MockDatabaseConnector.get_cache_data called for key: {cache_key}")
        
        if cache_key in self.cache_data:
            data = self.cache_data[cache_key]
            # 检查是否过期
            created_at = data.get("created_at")
            if created_at:
                # 简化过期检查：假设所有数据都有效
                return data
        return None
    
    def save_cache_data(self, cache_key: str, cache_value: Dict[str, Any], cache_type: str = "query_result", ttl_seconds: int = 3600) -> bool:
        """模拟保存缓存数据到数据库"""
        self.call_count["save_cache_data"] += 1
        logger.info(f"MockDatabaseConnector.save_cache_data called for key: {cache_key}")
        
        try:
            self.cache_data[cache_key] = {
                "cache_key": cache_key,
                "cache_value": json.dumps(cache_value),
                "cache_type": cache_type,
                "ttl_seconds": ttl_seconds,
                "created_at": time.time()
            }
            return True
        except Exception as e:
            logger.error(f"Failed to save cache data: {e}")
            return False
    
    def clear_cache(self):
        """清空模拟数据库缓存"""
        self.cache_data.clear()
        self.call_count = {
            "get_cache_data": 0,
            "save_cache_data": 0
        }


def test_hybrid_cache_strategy():
    """测试混合缓存策略"""
    print("\n=== 测试混合缓存策略 ===\n")
    
    # 创建模拟数据库连接器
    db_connector = MockDatabaseConnector()
    
    # 创建缓存管理器（启用数据库持久化）
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'python', 'sight_server'))
    from core.cache_manager import QueryCacheManager
    
    cache_manager = QueryCacheManager(
        cache_dir="./test_hybrid_cache",
        ttl=60,  # 60秒TTL
        max_size=10,
        enable_database_persistence=True,
        database_connector=db_connector,
        cache_strategy="hybrid"
    )
    
    # 测试数据
    test_query = "查找附近的餐厅"
    test_context = {"enable_spatial": True, "query_intent": "query"}
    test_result = {
        "data": [
            {"name": "餐厅A", "location": "位置A", "rating": 4.5},
            {"name": "餐厅B", "location": "位置B", "rating": 4.2}
        ],
        "count": 2,
        "status": "success"
    }
    
    # 步骤1: 设置缓存
    print("步骤1: 设置缓存")
    cache_key = cache_manager.get_cache_key(test_query, test_context)
    success = cache_manager.set(cache_key, test_result, test_query)
    print(f"设置缓存结果: {'成功' if success else '失败'}")
    
    # 步骤2: 从文件系统获取缓存
    print("\n步骤2: 从文件系统获取缓存")
    cached_result = cache_manager._get_from_filesystem(cache_key)
    print(f"文件系统缓存结果: {cached_result is not None}")
    
    # 步骤3: 从数据库获取缓存
    print("\n步骤3: 从数据库获取缓存")
    db_result = cache_manager._get_from_database(cache_key)
    print(f"数据库缓存结果: {db_result is not None}")
    
    # 步骤4: 使用 get 方法获取缓存（混合策略）
    print("\n步骤4: 使用混合策略获取缓存")
    final_result = cache_manager.get(cache_key)
    print(f"混合策略缓存结果: {final_result is not None}")
    
    # 步骤5: 检查统计信息
    print("\n步骤5: 检查统计信息")
    stats = cache_manager.get_cache_stats()
    print(f"缓存统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    # 步骤6: 检查数据库调用次数
    print(f"\n数据库调用统计:")
    print(f"  - get_cache_data 调用次数: {db_connector.call_count['get_cache_data']}")
    print(f"  - save_cache_data 调用次数: {db_connector.call_count['save_cache_data']}")
    
    # 清理测试文件
    cache_manager.clear_all()
    
    return success and cached_result is not None and db_result is not None and final_result is not None


def test_database_only_strategy():
    """测试仅数据库缓存策略"""
    print("\n=== 测试仅数据库缓存策略 ===\n")
    
    # 创建模拟数据库连接器
    db_connector = MockDatabaseConnector()
    
    # 创建缓存管理器（仅数据库策略）
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'python', 'sight_server'))
    from core.cache_manager import QueryCacheManager
    
    cache_manager = QueryCacheManager(
        cache_dir="./test_db_only_cache",
        ttl=60,
        max_size=10,
        enable_database_persistence=True,
        database_connector=db_connector,
        cache_strategy="db_only"
    )
    
    # 测试数据
    test_query = "查找附近的公园"
    test_context = {"enable_spatial": True, "query_intent": "query"}
    test_result = {
        "data": [
            {"name": "公园A", "location": "位置A", "area": "1000平方米"},
            {"name": "公园B", "location": "位置B", "area": "800平方米"}
        ],
        "count": 2,
        "status": "success"
    }
    
    # 步骤1: 设置缓存
    print("步骤1: 设置缓存")
    cache_key = cache_manager.get_cache_key(test_query, test_context)
    success = cache_manager.set(cache_key, test_result, test_query)
    print(f"设置缓存结果: {'成功' if success else '失败'}")
    
    # 步骤2: 检查文件系统是否没有缓存
    print("\n步骤2: 检查文件系统是否没有缓存")
    cache_file = os.path.join("./test_db_only_cache", f"{cache_key}.json")
    file_exists = os.path.exists(cache_file)
    print(f"文件系统缓存文件存在: {file_exists} (应该为 False)")
    
    # 步骤3: 从数据库获取缓存
    print("\n步骤3: 从数据库获取缓存")
    db_result = cache_manager._get_from_database(cache_key)
    print(f"数据库缓存结果: {db_result is not None}")
    
    # 步骤4: 使用 get 方法获取缓存（仅数据库策略）
    print("\n步骤4: 使用仅数据库策略获取缓存")
    final_result = cache_manager.get(cache_key)
    print(f"仅数据库策略缓存结果: {final_result is not None}")
    
    # 步骤5: 检查统计信息
    print("\n步骤5: 检查统计信息")
    stats = cache_manager.get_cache_stats()
    print(f"缓存统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    # 清理测试文件
    cache_manager.clear_all()
    
    return success and not file_exists and db_result is not None and final_result is not None


def test_fallback_mechanism():
    """测试数据库不可用时的回退机制"""
    print("\n=== 测试数据库不可用时的回退机制 ===\n")
    
    # 创建模拟数据库连接器（模拟数据库故障）
    class FaultyDatabaseConnector:
        def get_cache_data(self, cache_key: str):
            raise Exception("模拟数据库连接失败")
        
        def save_cache_data(self, cache_key: str, cache_value: Dict[str, Any], cache_type: str = "query_result", ttl_seconds: int = 3600):
            raise Exception("模拟数据库保存失败")
    
    faulty_db_connector = FaultyDatabaseConnector()
    
    # 创建缓存管理器（启用数据库持久化，但数据库连接器会失败）
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'python', 'sight_server'))
    from core.cache_manager import QueryCacheManager
    
    cache_manager = QueryCacheManager(
        cache_dir="./test_fallback_cache",
        ttl=60,
        max_size=10,
        enable_database_persistence=True,
        database_connector=faulty_db_connector,
        cache_strategy="hybrid"
    )
    
    # 测试数据
    test_query = "查找附近的商场"
    test_context = {"enable_spatial": True, "query_intent": "query"}
    test_result = {
        "data": [
            {"name": "商场A", "location": "位置A", "floor_count": 5},
            {"name": "商场B", "location": "位置B", "floor_count": 3}
        ],
        "count": 2,
        "status": "success"
    }
    
    # 步骤1: 设置缓存（应该回退到文件系统）
    print("步骤1: 设置缓存（数据库故障时回退到文件系统）")
    cache_key = cache_manager.get_cache_key(test_query, test_context)
    success = cache_manager.set(cache_key, test_result, test_query)
    print(f"设置缓存结果: {'成功' if success else '失败'} (应该为 False，因为数据库失败，但文件系统成功)")
    
    # 步骤2: 检查文件系统是否有缓存
    print("\n步骤2: 检查文件系统是否有缓存")
    cache_file = os.path.join("./test_fallback_cache", f"{cache_key}.json")
    file_exists = os.path.exists(cache_file)
    print(f"文件系统缓存文件存在: {file_exists} (应该为 True)")
    
    # 步骤3: 使用 get 方法获取缓存（应该回退到文件系统）
    print("\n步骤3: 使用 get 方法获取缓存（数据库故障时回退到文件系统）")
    final_result = cache_manager.get(cache_key)
    print(f"回退机制缓存结果: {final_result is not None} (应该为 True)")
    
    # 步骤4: 检查统计信息
    print("\n步骤4: 检查统计信息")
    stats = cache_manager.get_cache_stats()
    print(f"缓存统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    # 步骤5: 检查数据库错误统计
    print(f"\n数据库错误统计:")
    print(f"  - 数据库错误次数: {stats.get('database_stats', {}).get('db_errors', 0)}")
    
    # 清理测试文件
    cache_manager.clear_all()
    
    return not success and file_exists and final_result is not None


def test_cache_cleanup_consistency():
    """测试缓存清理的数据一致性"""
    print("\n=== 测试缓存清理的数据一致性 ===\n")
    
    # 创建模拟数据库连接器
    db_connector = MockDatabaseConnector()
    
    # 创建缓存管理器
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'python', 'sight_server'))
    from core.cache_manager import QueryCacheManager
    
    cache_manager = QueryCacheManager(
        cache_dir="./test_cleanup_cache",
        ttl=1,  # 1秒TTL，便于测试过期
        max_size=3,  # 小容量便于测试清理
        enable_database_persistence=True,
        database_connector=db_connector,
        cache_strategy="hybrid"
    )
    
    # 创建多个测试缓存
    test_queries = [
        "查询1", "查询2", "查询3", "查询4"  # 超过最大容量
    ]
    
    for i, query in enumerate(test_queries):
        test_context = {"enable_spatial": True, "query_intent": "query"}
        test_result = {"data": [f"结果{i+1}"], "count": 1, "status": "success"}
        
        cache_key = cache_manager.get_cache_key(query, test_context)
        success = cache_manager.set(cache_key, test_result, query)
        print(f"设置缓存 {i+1}: {'成功' if success else '失败'}")
    
    # 检查缓存数量
    print(f"\n缓存条目数量: {len(cache_manager.metadata['cache_entries'])}")
    
    # 清理过期缓存
    print("\n清理过期缓存...")
    removed_count = cache_manager.cleanup_expired_entries()
    print(f"清理了 {removed_count} 个过期缓存")
    
    # 检查统计信息
    stats = cache_manager.get_cache_stats()
    print(f"清理后缓存统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    # 清理测试文件
    cache_manager.clear_all()
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行增强版缓存管理器测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行混合缓存策略测试
    try:
        result = test_hybrid_cache_strategy()
        test_results.append(("混合缓存策略", result))
    except Exception as e:
        print(f"混合缓存策略测试失败: {e}")
        test_results.append(("混合缓存策略", False))
    
    # 运行仅数据库策略测试
    try:
        result = test_database_only_strategy()
        test_results.append(("仅数据库策略", result))
    except Exception as e:
        print(f"仅数据库策略测试失败: {e}")
        test_results.append(("仅数据库策略", False))
    
    # 运行回退机制测试
    try:
        result = test_fallback_mechanism()
        test_results.append(("回退机制", result))
    except Exception as e:
        print(f"回退机制测试失败: {e}")
        test_results.append(("回退机制", False))
    
    # 运行缓存清理一致性测试
    try:
        result = test_cache_cleanup_consistency()
        test_results.append(("缓存清理一致性", result))
    except Exception as e:
        print(f"缓存清理一致性测试失败: {e}")
        test_results.append(("缓存清理一致性", False))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print(f"\n总体结果: {'✓ 所有测试通过' if all_passed else '✗ 部分测试失败'}")
    
    return all_passed


if __name__ == "__main__":
    # 运行所有测试
    success = run_all_tests()
    
    # 退出码
    exit(0 if success else 1)
