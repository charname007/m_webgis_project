"""
测试统一缓存管理器功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from sight_server.core.query_cache_manager import QueryCacheManager

def test_unified_cache():
    """测试统一缓存管理器功能"""
    print("=== 测试统一缓存管理器 ===")
    
    try:
        # 1. 创建缓存管理器
        cache_manager = QueryCacheManager(cache_dir='./test_cache', ttl=60, max_size=10)
        print("✓ 缓存管理器创建成功")
        
        # 2. 测试缓存功能
        test_key = cache_manager.get_cache_key('测试查询', {'enable_spatial': True})
        test_data = {'test': 'data', 'count': 1}
        
        # 设置缓存
        cache_manager.set(test_key, test_data, '测试查询')
        print("✓ 缓存设置成功")
        
        # 获取缓存
        cached = cache_manager.get(test_key)
        print(f"✓ 缓存获取成功: {cached}")
        
        # 3. 测试缓存统计
        stats = cache_manager.get_cache_stats()
        print(f"✓ 缓存统计: {stats}")
        
        print("✓ 统一缓存管理器测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_unified_cache()
