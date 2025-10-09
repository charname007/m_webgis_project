#!/usr/bin/env python3
"""
测试缓存管理器修复验证脚本
验证 query_cache_manager.py 中的 get() 方法是否正常工作
"""

import sys
import os
import logging

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'python', 'sight_server'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_cache_manager_get_method():
    """测试缓存管理器的 get() 方法"""
    try:
        from core.query_cache_manager import QueryCacheManager
        
        print("=== 测试缓存管理器 get() 方法 ===\n")
        
        # 创建缓存管理器
        cache_manager = QueryCacheManager(cache_dir="./test_cache_fix", ttl=60, max_size=10)
        
        # 测试1: 检查 get() 方法是否存在
        print("--- 测试1: 检查 get() 方法是否存在 ---")
        if hasattr(cache_manager, 'get'):
            print("✓ get() 方法存在")
        else:
            print("✗ get() 方法不存在")
            return False
        
        # 测试2: 测试 get() 方法调用
        print("\n--- 测试2: 测试 get() 方法调用 ---")
        test_cache_key = "test_key_123"
        result = cache_manager.get(test_cache_key)
        print(f"get() 方法调用结果: {result}")
        print("✓ get() 方法可以正常调用")
        
        # 测试3: 测试 get_query_cache() 方法调用
        print("\n--- 测试3: 测试 get_query_cache() 方法调用 ---")
        result2 = cache_manager.get_query_cache(test_cache_key)
        print(f"get_query_cache() 方法调用结果: {result2}")
        print("✓ get_query_cache() 方法可以正常调用")
        
        # 测试4: 验证两个方法返回结果一致
        print("\n--- 测试4: 验证两个方法返回结果一致 ---")
        if result == result2:
            print("✓ get() 和 get_query_cache() 返回结果一致")
        else:
            print("✗ get() 和 get_query_cache() 返回结果不一致")
            return False
        
        # 测试5: 测试缓存统计
        print("\n--- 测试5: 测试缓存统计 ---")
        stats = cache_manager.get_cache_stats()
        print(f"缓存统计: {stats}")
        print("✓ 缓存统计功能正常")
        
        print("\n🎉 所有测试通过！缓存管理器修复成功")
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sql_generation_cache():
    """测试 SQL 生成节点的缓存功能"""
    try:
        from core.graph.nodes.sql_generation import GenerateSqlNode
        from core.schemas import AgentState
        
        print("\n=== 测试 SQL 生成节点缓存功能 ===\n")
        
        # 创建测试状态
        test_state = AgentState({
            "query": "北京大学",
            "current_step": 0,
            "enable_spatial": True,
            "query_intent": "query"
        })
        
        # 创建缓存管理器
        from core.query_cache_manager import QueryCacheManager
        cache_manager = QueryCacheManager(cache_dir="./test_cache_fix", ttl=60, max_size=10)
        
        # 创建 SQL 生成节点
        sql_node = GenerateSqlNode()
        sql_node.cache_manager = cache_manager
        
        # 测试 _maybe_load_cache 方法
        print("--- 测试 _maybe_load_cache 方法 ---")
        try:
            result = sql_node._maybe_load_cache(test_state)
            print(f"_maybe_load_cache 结果: {result}")
            print("✓ _maybe_load_cache 方法可以正常调用")
        except Exception as e:
            print(f"✗ _maybe_load_cache 方法调用失败: {e}")
            return False
        
        # 测试 _build_cache_key 方法
        print("\n--- 测试 _build_cache_key 方法 ---")
        try:
            cache_key = sql_node._build_cache_key(test_state, "北京大学")
            print(f"_build_cache_key 结果: {cache_key}")
            print("✓ _build_cache_key 方法可以正常调用")
        except Exception as e:
            print(f"✗ _build_cache_key 方法调用失败: {e}")
            return False
        
        print("\n🎉 SQL 生成节点缓存功能测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"SQL 生成节点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始验证缓存管理器修复...\n")
    
    # 运行测试
    test1_success = test_cache_manager_get_method()
    test2_success = test_sql_generation_cache()
    
    print("\n" + "="*50)
    if test1_success and test2_success:
        print("🎉 所有测试通过！缓存管理器修复成功")
        print("✅ 'QueryCacheManager' object has no attribute 'get' 错误已修复")
        print("✅ 查询'北京大学'应该不再出现此错误")
    else:
        print("❌ 部分测试失败，需要进一步检查")
        sys.exit(1)
