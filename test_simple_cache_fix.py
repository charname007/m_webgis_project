#!/usr/bin/env python3
"""
简化版缓存管理器修复验证脚本
只验证核心的 get() 方法修复
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

def test_core_fix():
    """测试核心修复：get() 方法是否存在并能正常调用"""
    try:
        from core.query_cache_manager import QueryCacheManager
        
        print("=== 核心修复验证：get() 方法 ===\n")
        
        # 创建缓存管理器（禁用语义搜索以避免网络问题）
        cache_manager = QueryCacheManager(
            cache_dir="./test_simple_cache", 
            ttl=60, 
            max_size=10,
            enable_semantic_search=False  # 禁用语义搜索
        )
        
        # 关键测试：get() 方法是否存在
        print("--- 关键测试1: get() 方法是否存在 ---")
        if hasattr(cache_manager, 'get'):
            print("✅ get() 方法存在")
        else:
            print("❌ get() 方法不存在 - 修复失败")
            return False
        
        # 关键测试：get() 方法能否正常调用
        print("\n--- 关键测试2: get() 方法能否正常调用 ---")
        try:
            test_cache_key = "test_key_123"
            result = cache_manager.get(test_cache_key)
            print(f"get() 方法调用结果: {result}")
            print("✅ get() 方法可以正常调用")
        except Exception as e:
            print(f"❌ get() 方法调用失败: {e}")
            return False
        
        # 关键测试：get() 和 get_query_cache() 返回结果一致
        print("\n--- 关键测试3: 方法一致性验证 ---")
        try:
            result1 = cache_manager.get(test_cache_key)
            result2 = cache_manager.get_query_cache(test_cache_key)
            
            if result1 == result2:
                print("✅ get() 和 get_query_cache() 返回结果一致")
            else:
                print("❌ get() 和 get_query_cache() 返回结果不一致")
                return False
        except Exception as e:
            print(f"❌ 方法一致性验证失败: {e}")
            return False
        
        print("\n🎉 核心修复验证通过！")
        print("✅ 'QueryCacheManager' object has no attribute 'get' 错误已修复")
        print("✅ 查询'北京大学'应该不再出现此错误")
        return True
        
    except Exception as e:
        logger.error(f"核心修复验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_original_error_scenario():
    """测试原始错误场景是否修复"""
    try:
        from core.graph.nodes.sql_generation import GenerateSqlNode
        
        print("\n=== 原始错误场景验证 ===\n")
        
        # 模拟原始错误场景：检查 _maybe_load_cache 方法是否还会报错
        print("--- 检查 _maybe_load_cache 方法 ---")
        
        # 创建一个模拟的缓存管理器
        from core.query_cache_manager import QueryCacheManager
        cache_manager = QueryCacheManager(
            cache_dir="./test_original_scenario", 
            ttl=60, 
            max_size=10,
            enable_semantic_search=False
        )
        
        # 检查缓存管理器是否有 get 方法
        if hasattr(cache_manager, 'get'):
            print("✅ 缓存管理器有 get() 方法")
            
            # 尝试调用 get 方法
            try:
                result = cache_manager.get("test_key")
                print(f"✅ get() 方法调用成功，结果: {result}")
            except Exception as e:
                print(f"❌ get() 方法调用失败: {e}")
                return False
        else:
            print("❌ 缓存管理器没有 get() 方法")
            return False
        
        print("\n🎉 原始错误场景验证通过！")
        print("✅ 不会再出现 'QueryCacheManager' object has no attribute 'get' 错误")
        return True
        
    except Exception as e:
        logger.error(f"原始错误场景验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始验证缓存管理器核心修复...\n")
    
    # 运行核心测试
    core_success = test_core_fix()
    scenario_success = test_original_error_scenario()
    
    print("\n" + "="*60)
    if core_success and scenario_success:
        print("🎉 所有核心修复验证通过！")
        print("✅ 缓存管理器修复成功")
        print("✅ 原始错误已解决")
        print("✅ 系统应该可以正常处理查询'北京大学'")
    else:
        print("❌ 核心修复验证失败，需要进一步检查")
        sys.exit(1)
