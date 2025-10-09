#!/usr/bin/env python3
"""
缓存诊断脚本 - 检查"武汉大学"缓存匹配问题
"""

import sys
import os
sys.path.append('.')

from core.query_cache_manager import QueryCacheManager
from core.database import DatabaseConnector

def test_cache_matching():
    """测试缓存匹配功能"""
    print("=== 缓存匹配诊断测试 ===\n")
    
    # 创建缓存管理器
    db_connector = DatabaseConnector()
    cache_manager = QueryCacheManager(
        cache_dir="./cache",
        database_connector=db_connector,
        cache_strategy="hybrid"
    )
    
    # 测试查询
    test_query = "武汉大学"
    context = {
        "enable_spatial": False,
        "query_intent": "query",
        "include_sql": True
    }
    
    print(f"测试查询: '{test_query}'")
    print(f"上下文: {context}")
    
    # 生成缓存键
    cache_key = cache_manager.get_cache_key(test_query, context)
    print(f"生成的缓存键: {cache_key}")
    
    # 检查缓存元数据
    print(f"\n=== 缓存元数据检查 ===")
    metadata = cache_manager.metadata
    print(f"总缓存条目数: {len(metadata['cache_entries'])}")
    print(f"总命中数: {metadata['total_hits']}")
    print(f"总未命中数: {metadata['total_misses']}")
    
    # 查找匹配的缓存条目
    print(f"\n=== 查找匹配的缓存条目 ===")
    found_match = False
    for key, entry in metadata['cache_entries'].items():
        if key == cache_key:
            print(f"✓ 找到精确匹配的缓存键: {key}")
            print(f"  查询: {entry['query']}")
            print(f"  创建时间: {entry['created_at']}")
            print(f"  命中次数: {entry['hit_count']}")
            found_match = True
            break
    
    if not found_match:
        print(f"✗ 未找到精确匹配的缓存键")
        print(f"  现有缓存键: {list(metadata['cache_entries'].keys())}")
    
    # 尝试获取缓存
    print(f"\n=== 尝试获取缓存 ===")
    cached_result = cache_manager.get_query_cache(cache_key)
    if cached_result:
        print(f"✓ 缓存获取成功")
        print(f"  数据条数: {cached_result.get('count', 'N/A')}")
        print(f"  状态: {cached_result.get('status', 'N/A')}")
    else:
        print(f"✗ 缓存获取失败")
        
        # 尝试语义搜索
        print(f"\n=== 尝试语义搜索 ===")
        semantic_result = cache_manager.get_with_semantic_search(test_query, context)
        if semantic_result:
            print(f"✓ 语义搜索找到匹配")
            print(f"  数据条数: {semantic_result.get('count', 'N/A')}")
        else:
            print(f"✗ 语义搜索也未找到匹配")
    
    # 检查缓存文件
    print(f"\n=== 缓存文件检查 ===")
    cache_file = f"./cache/{cache_key}.json"
    if os.path.exists(cache_file):
        print(f"✓ 缓存文件存在: {cache_file}")
        file_size = os.path.getsize(cache_file)
        print(f"  文件大小: {file_size} bytes")
    else:
        print(f"✗ 缓存文件不存在: {cache_file}")
        
        # 列出所有缓存文件
        print(f"\n=== 所有缓存文件 ===")
        cache_files = [f for f in os.listdir("./cache") if f.endswith('.json') and f != 'query_cache_metadata.json' and f != 'schema_cache.json']
        print(f"总缓存文件数: {len(cache_files)}")
        for i, file in enumerate(cache_files[:5]):  # 只显示前5个
            print(f"  {i+1}. {file}")

if __name__ == "__main__":
    test_cache_matching()
