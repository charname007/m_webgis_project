#!/usr/bin/env python3
"""
测试语义搜索功能移植验证脚本
验证从 cache_manager.py 移植到 query_cache_manager.py 的语义搜索功能
"""

import os
import sys
import logging
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from sight_server.core.query_cache_manager import QueryCacheManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试基本功能 ===")
    
    # 创建缓存管理器
    cache_manager = QueryCacheManager(
        cache_dir="./test_semantic_cache",
        ttl=300,  # 5分钟
        max_size=10,
        enable_semantic_search=True,
        similarity_threshold=0.85
    )
    
    # 测试1: 保存缓存
    print("\n--- 测试1: 保存缓存 ---")
    test_queries = [
        "武汉大学附近有什么景点",
        "武汉大学周边的旅游景点",
        "武汉大学附近的著名景点",
        "武汉大学周围有什么好玩的地方",
        "查询武汉大学附近的景点"
    ]
    
    for i, query in enumerate(test_queries):
        result = {
            "data": [f"景点{i+1}", f"景点{i+2}"],
            "count": 2,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        cache_manager.save_query_cache(query, result)
        print(f"✓ 保存缓存: '{query}'")
    
    # 测试2: 获取精确匹配
    print("\n--- 测试2: 精确匹配测试 ---")
    exact_query = "武汉大学附近有什么景点"
    exact_result = cache_manager.get_query_cache(
        cache_manager.get_cache_key(exact_query, {})
    )
    if exact_result:
        print(f"✓ 精确匹配成功: '{exact_query}'")
    else:
        print(f"✗ 精确匹配失败: '{exact_query}'")
    
    # 测试3: 语义搜索测试
    print("\n--- 测试3: 语义搜索测试 ---")
    semantic_query = "武大附近有什么好玩的地方"
    semantic_result = cache_manager.get_with_semantic_search(semantic_query, {})
    
    if semantic_result:
        print(f"✓ 语义搜索成功: '{semantic_query}'")
        print(f"  返回结果: {semantic_result.get('data', [])}")
    else:
        print(f"✗ 语义搜索失败: '{semantic_query}'")
    
    # 测试4: 获取统计信息
    print("\n--- 测试4: 统计信息测试 ---")
    stats = cache_manager.get_cache_stats()
    print(f"总缓存条目: {stats['total_entries']}")
    print(f"命中率: {stats['hit_rate_percent']}%")
    
    if 'semantic_search' in stats:
        semantic_stats = stats['semantic_search']
        print(f"语义搜索启用: {semantic_stats['enabled']}")
        print(f"语义搜索命中: {semantic_stats['semantic_hits']}")
        print(f"语义搜索命中率: {semantic_stats['semantic_hit_rate_percent']}%")
    
    # 测试5: 语义搜索统计
    print("\n--- 测试5: 语义搜索详细统计 ---")
    semantic_stats = cache_manager.get_semantic_search_stats()
    print(f"语义搜索统计: {json.dumps(semantic_stats, indent=2, ensure_ascii=False)}")
    
    # 测试6: 相似度搜索统计
    print("\n--- 测试6: 相似度搜索统计 ---")
    similar_stats = cache_manager.get_similar_cache_stats("武大附近景点", 0.7)
    print(f"相似查询数量: {similar_stats['total_similar']}")
    print(f"最大相似度: {similar_stats['max_similarity']}")
    
    # 清理测试缓存
    print("\n--- 清理测试缓存 ---")
    cleared_count = cache_manager.clear_all()
    print(f"清理了 {cleared_count} 个测试缓存条目")
    
    return True

def test_fallback_functionality():
    """测试降级功能（禁用语义搜索）"""
    print("\n=== 测试降级功能 ===")
    
    # 创建禁用语义搜索的缓存管理器
    cache_manager = QueryCacheManager(
        cache_dir="./test_fallback_cache",
        ttl=300,
        max_size=5,
        enable_semantic_search=False  # 禁用语义搜索
    )
    
    # 保存一些测试数据
    test_query = "测试查询"
    test_result = {"data": ["测试结果"], "status": "success"}
    cache_manager.save_query_cache(test_query, test_result)
    
    # 测试语义搜索（应该返回 None）
    semantic_result = cache_manager.get_with_semantic_search("相似查询", {})
    if semantic_result is None:
        print("✓ 降级功能正常：语义搜索禁用时返回 None")
    else:
        print("✗ 降级功能异常：语义搜索禁用时不应返回结果")
    
    # 清理
    cache_manager.clear_all()
    
    return True

def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    try:
        # 创建缓存管理器（使用不存在的模型）
        cache_manager = QueryCacheManager(
            cache_dir="./test_error_cache",
            enable_semantic_search=True,
            embedding_model="non-existent-model"  # 不存在的模型
        )
        
        # 应该降级到禁用语义搜索
        if not cache_manager.enable_semantic_search:
            print("✓ 错误处理正常：模型加载失败时自动禁用语义搜索")
        else:
            print("✗ 错误处理异常：模型加载失败时应禁用语义搜索")
        
        # 清理
        cache_manager.clear_all()
        
    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("开始语义搜索功能移植验证测试...\n")
    
    tests = [
        ("基本功能测试", test_basic_functionality),
        ("降级功能测试", test_fallback_functionality),
        ("错误处理测试", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            print(f"执行: {test_name}")
            print(f"{'='*50}")
            
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✓ {test_name} - 通过")
            else:
                print(f"✗ {test_name} - 失败")
                
        except Exception as e:
            print(f"✗ {test_name} - 异常: {e}")
            results.append((test_name, False))
    
    # 输出测试总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{status} - {test_name}")
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！语义搜索功能移植成功！")
        return True
    else:
        print("❌ 部分测试失败，请检查移植的代码")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
